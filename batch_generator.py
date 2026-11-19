"""
AI 1인 기업 콘텐츠 대량 자동 생성기 (Batch Content Generator)
실행: python batch_generator.py
"""
import os
import sys
import time
from datetime import datetime
from ollama_client import OllamaService

TOPICS_FILE = os.path.join(os.path.dirname(__file__), "topics.txt")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    service = OllamaService()
    print("=" * 60)
    print("🚀 AI 1인 기업 블로그 콘텐츠 자동 대량 생성기")
    print(f"🤖 대상 로컬 모델: {service.model}")
    print("=" * 60)

    if not service.is_server_running():
        print("❌ Ollama 서버가 실행되어 있지 않습니다. Ollama를 먼저 켜주세요.")
        return

    if not os.path.exists(TOPICS_FILE):
        print(f"❌ {TOPICS_FILE} 파일이 없습니다.")
        return

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not topics:
        print("생성할 주제가 topics.txt에 없습니다.")
        return

    print(f"📝 총 {len(topics)}개의 콘텐츠 주제를 발견했습니다.\n")

    for idx, topic in enumerate(topics, 1):
        print(f"[{idx}/{len(topics)}] 생성 중: {topic}")
        start_time = time.time()

        prompt = f"""
주제: "{topic}"

위 주제에 대해 1인 기업 창업가 및 부업 준비자들을 위한 네이버/티스토리/브런치 포스팅용 고품질 블로그 글을 작성해 주세요.

작성 가이드라인:
1. 매력적인 제목 (SEO 최적화)
2. 서론 (독자의 공감 유발 및 문제 제기)
3. 본론 (핵심 팁 3~4가지를 구체적이고 실천 가능한 내용으로 정리)
4. 결론 (핵심 요약 및 행동 유도(Call To Action))
5. 추천 해시태그 5개

마크다운 형식으로 가독성 좋게 작성해 주세요.
"""
        try:
            content = service.chat(
                prompt=prompt,
                system_prompt="당신은 누적 조회수 500만 뷰를 달성한 최고의 1인 기업 전문 비즈니스 콘텐츠 크리에이터입니다."
            )

            # 파일 저장
            safe_title = "".join(c for c in topic[:25] if c.isalnum() or c in (" ", "_", "-")).rstrip()
            filename = f"{datetime.now().strftime('%Y%m%d')}_{idx:02d}_{safe_title}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)

            with open(filepath, "w", encoding="utf-8") as out_f:
                out_f.write(f"---\n")
                out_f.write(f"title: \"{topic}\"\n")
                out_f.write(f"model: {service.model}\n")
                out_f.write(f"created_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                out_f.write(f"---\n\n")
                out_f.write(content)

            elapsed = round(time.time() - start_time, 1)
            print(f"  ✅ 생성 완료 ({elapsed}초) ➔ 저장 위치: outputs/{filename}\n")

        except Exception as e:
            print(f"  ❌ 생성 실패: {e}\n")

    print("=" * 60)
    print(f"🎉 모든 콘텐츠 생성이 완료되었습니다! (확인: outputs/ 폴더)")
    print("=" * 60)

if __name__ == "__main__":
    main()

