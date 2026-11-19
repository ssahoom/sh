"""
현재 Ollama에 설치된 모든 로컬 모델 목록을 조회하고
사용자님이 보유하신 Gemma 및 Qwen 모델을 자동으로 감지하는 스크립트
실행: python check_models.py
"""
from ollama_client import OllamaService

def main():
    service = OllamaService()
    print("🔍 Ollama에 등록된 모델 확인 중...\n")
    
    if not service.is_server_running():
        print("❌ Ollama 서버에 연결할 수 없습니다. 백그라운드에서 Ollama가 켜져 있는지 확인해 주세요.")
        return

    models = service.list_installed_models()
    if not models:
        print("설치된 모델을 찾지 못했습니다.")
        return

    print("=" * 50)
    print("📋 현재 Ollama에 등록된 모델 목록 (NAME):")
    print("=" * 50)
    
    local_models = []
    cloud_models = []
    
    for m in models:
        if m.endswith(":cloud"):
            cloud_models.append(m)
            print(f"  ☁️  {m}  (유료 클라우드 플랜 전용)")
        else:
            local_models.append(m)
            print(f"  🟢  {m}  (무료 로컬 모델)")
            
    print("=" * 50)
    
    # Gemma 및 Qwen 계열 자동 탐색
    gemma_found = [m for m in local_models if "gemma" in m.lower()]
    qwen_found = [m for m in local_models if "qwen" in m.lower()]
    
    print("\n💡 보유 중인 핵심 로컬 모델 탐지 결과:")
    if gemma_found:
        print(f"  👉 젬마 계열: {gemma_found}")
    if qwen_found:
        print(f"  👉 Qwen 계열: {qwen_found}")
        
    recommended = (gemma_found + qwen_found + local_models)
    if recommended:
        target = recommended[0]
        print(f"\n✅ 추천 설정: antigravity.config.json의 \"model\"을 \"{target}\" 로 지정하시면 됩니다.")
    print("=" * 50)

if __name__ == "__main__":
    main()

