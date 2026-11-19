"""
로컬 Ollama(gemma4:e4b)에 질문을 전달하고 답변을 출력하는 CLI 헬퍼 스크립트
사용법: python ask_local.py "질문 내용" [모델명]
"""
import sys
from ollama_client import OllamaService

def main():
    if len(sys.argv) < 2:
        print("사용법: python ask_local.py \"질문 내용\" [모델명]")
        return

    prompt = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else None

    service = OllamaService()
    if not service.is_server_running():
        print("❌ [오류] Ollama 서버(localhost:11434)가 켜져 있지 않습니다.")
        return

    target_model = model or service.model
    try:
        reply = service.chat(prompt, model=target_model)
        print(reply)
    except Exception as e:
        print(f"❌ 로컬 모델 호출 실패: {e}")

if __name__ == "__main__":
    main()

