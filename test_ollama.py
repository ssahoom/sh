"""
Ollama 연동 테스트 스크립트
실행 방법: python test_ollama.py
"""
import sys
from ollama_client import OllamaService

def main():
    service = OllamaService()
    
    print("1. Ollama 서버 상태 점검 중...")
    if not service.is_server_running():
        print("❌ [오류] Ollama 서버(http://localhost:11434)가 응답하지 않습니다.")
        print("▶ 해결 방법: Windows에서 Ollama 앱을 실행하거나 백그라운드 프로세스를 확인해 주세요.\n")
        return

    print("✅ Ollama 서버 연결 정상 확인!")
    
    print("\n2. 설치된 모델 확인 중...")
    models = service.list_installed_models()
    if not models:
        print("⚠️ 설치된 모델이 없습니다.")
        print("▶ 무료 로컬 모델 다운로드: ollama pull gemma2")
        return
    
    # 로컬 무료 모델과 유료 클라우드(:cloud) 모델 분류
    local_models = [m for m in models if not m.endswith(":cloud")]
    cloud_models = [m for m in models if m.endswith(":cloud")]

    print(f"📦 발견된 전체 모델 ({len(models)}개):")
    if local_models:
        print(f"  - 🟢 로컬 무료 모델: {', '.join(local_models)}")
    if cloud_models:
        print(f"  - ☁️ 클라우드(유료 크레딧 필요) 모델: {', '.join(cloud_models)}")
    
    # 테스트할 모델 선정:
    # 1) config에 지정된 모델이 설치되어 있으면 최우선
    # 2) 아니면 로컬 무료 모델 중 첫 번째
    # 3) 둘 다 없으면 첫 번째 모델
    if service.model in models:
        test_model = service.model
    elif local_models:
        test_model = local_models[0]
        print(f"\n💡 config에 지정된 [{service.model}] 대신 사용 가능한 로컬 모델 [{test_model}]을(를) 테스트 대상으로 자동 선택합니다.")
    else:
        test_model = models[0]
        print(f"\n⚠️ 주의: 현재 설치된 모델이 클라우드 유료 모델({test_model})뿐입니다.")
        print("💡 비용 없이 로컬에서 돌리시려면 다음 명령으로 무료 모델을 먼저 받아주세요:")
        print("   👉 ollama pull gemma2 (또는 ollama pull qwen2.5)\n")

    print(f"\n3. 모델 [{test_model}] 호출 테스트...")
    
    try:
        reply = service.chat("안녕! 한국어로 짧게 한 문장으로 자기소개해 줘.", model=test_model)
        print(f"\n🤖 [{test_model}] 응답 결과:\n{reply}\n")
        print("🎉 Ollama 연동이 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"❌ 호출 중 오류 발생: {e}")
        if ":cloud" in test_model or "402" in str(e):
            print("\n💡 [402 에러 해결 가이드]")
            print("현재 테스트한 모델은 유료 크레딧이 필요한 클라우드 모델입니다.")
            print("터미널에서 아래 명령을 실행하여 100% 무료 로컬 모델을 다운로드받아 보세요:")
            print("👉 ollama pull gemma2")

if __name__ == "__main__":
    main()
