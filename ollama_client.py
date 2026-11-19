import json
import os
import requests
from openai import OpenAI

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "antigravity.config.json")

def load_config():
    """antigravity.config.json 설정을 불러옵니다."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

class OllamaService:
    def __init__(self):
        self.config = load_config()
        local_cfg = self.config.get("models", {}).get("local", {})
        
        raw_base_url = local_cfg.get("baseURL", "http://localhost:11434").rstrip("/")
        if raw_base_url.endswith("/v1"):
            self.base_url = raw_base_url[:-3]
            self.v1_url = raw_base_url
        else:
            self.base_url = raw_base_url
            self.v1_url = f"{raw_base_url}/v1"
            
        self.model = local_cfg.get("model", "gemma2")
        self.api_key = local_cfg.get("apiKey", "ollama")
        self.temperature = local_cfg.get("temperature", 0.7)
        self.max_tokens = local_cfg.get("maxTokens", 4096)
        
        # OpenAI 호환 클라이언트 초기화
        self.client = OpenAI(
            base_url=self.v1_url,
            api_key=self.api_key
        )

    def is_server_running(self) -> bool:
        """Ollama 로컬 서버가 정상 동작 중인지 확인합니다."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return res.status_code == 200
        except Exception:
            return False

    def list_installed_models(self) -> list[str]:
        """로컬 Ollama에 설치되어 있는 모델 목록을 반환합니다."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if res.status_code == 200:
                data = res.json()
                return [m.get("name") for m in data.get("models", [])]
        except Exception as e:
            print(f"모델 목록 조회 실패: {e}")
        return []

    def resolve_model_name(self, requested_model: str) -> str:
        """
        요청된 모델명이 설치된 모델 목록과 정확히 일치하지 않더라도,
        가장 적합한 로컬 무료 설치 모델(Gemma, Qwen 등)을 지능적으로 매핑합니다.
        유료 :cloud 모델은 제외합니다.
        """
        installed = self.list_installed_models()
        if not installed:
            return requested_model

        # 1. 정확히 일치하는 경우
        if requested_model in installed:
            return requested_model

        req_lower = requested_model.lower()
        # 2. 접두사/부분 일치 검사 (클라우드 제외)
        local_mods = [m for m in installed if not m.endswith(":cloud")]
        for m in local_mods:
            if req_lower in m.lower() or m.lower() in req_lower:
                return m

        # 3. 키워드 기반 탐색 (gemma, qwen)
        for kw in ["gemma", "qwen"]:
            if kw in req_lower:
                matches = [m for m in local_mods if kw in m.lower()]
                if matches:
                    return matches[0]

        # 4. 사용 가능한 첫 번째 로컬 모델 반환
        return local_mods[0] if local_mods else installed[0]

    def chat(self, prompt: str, system_prompt: str = "당신은 유능한 AI 어시스턴트입니다.", model: str = None) -> str:
        """Ollama 모델을 호출하여 대화 응답을 받습니다."""
        raw_model = model or self.model
        target_model = self.resolve_model_name(raw_model)
        try:
            response = self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            fallback_cfg = self.config.get("fallback", {})
            if fallback_cfg.get("enabled"):
                print(f"[Warning] 로컬 Ollama 호출 실패 ({e}). Fallback 모델({fallback_cfg.get('model')}) 검토 필요.")
            raise e

if __name__ == "__main__":
    service = OllamaService()
    print("=== Ollama 연결 상태 점검 ===")
    if service.is_server_running():
        print(f"✅ Ollama 서버 연결 성공! ({service.base_url})")
        models = service.list_installed_models()
        print(f"📦 설치된 모델 목록: {models if models else '설치된 모델 없음'}")
    else:
        print(f"❌ Ollama 서버에 연결할 수 없습니다. ({service.base_url})")
        print("💡 터미널에서 'ollama serve'를 실행하거나 Ollama 앱을 켜주세요.")
