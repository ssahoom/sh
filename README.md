# 💼 AI 1인 기업 자동화 허브 (Ollama 로컬 LLM 기반)

로컬에서 구동되는 경량/고성능 오픈소스 LLM(Gemma 4 계열)을 활용하여 **API 비용 0원**으로 1인 기업 업무를 자동화하는 프로젝트입니다.

---

## 📁 프로젝트 구조

```text
AI 1인 기업 test/
│
├── antigravity.config.json   # 모델 엔드포인트 및 기본 파라미터 설정
├── ollama_client.py          # OpenAI 호환 Ollama API 연동 서비스 모듈
├── test_ollama.py            # 모델 연결 및 응답 테스트 스크립트
├── check_models.py           # 로컬 Ollama 모델 태그 확인 스크립트
├── app.py                    # Streamlit 기반 1인 기업 웹 대시보드
├── outputs/                  # 생성된 콘텐츠 자동 백업 저장소 (.md)
└── README.md                 # 본 가이드 문서
```

---

## ⚙️ 설정된 모델 현황 (`antigravity.config.json`)

* **기본 모델**: `gemma4:e4b` (6.6 GB)
* **보유 모델**: 
  - `gemma4:e4b`: 기본 작업용 균형 모델
  - `gemma4:12b`: 정밀한 분석 및 심층 콘텐츠 작성용 고성능 모델
  - `gemma4:e2b`: 빠른 응답용 경량 모델
  - `gemma2:latest`: 공식 검증 모델
* **엔드포인트**: `http://localhost:11434` (OpenAI 호환 `/v1` 지원)

---

## 🚀 실행 방법

### 1. 연결 테스트 (CLI)
터미널에서 Ollama 서버 상태와 `gemma4:e4b` 모델 호출을 테스트합니다.
```powershell
python test_ollama.py
```

### 2. 웹 대시보드 실행 (GUI)
브라우저 환경에서 직관적으로 업무를 자동화합니다.
```powershell
streamlit run app.py
```

---

## 🌟 웹 대시보드 주요 기능

1. **✍️ 마케팅 & 카피라이팅**: 인스타그램 피드, 헤드라인형 광고 문구, 해시태그 자동 생성
2. **📝 블로그 포스팅 작성**: SEO 최적화된 마크다운 형식의 아티클 초안 작성
3. **💬 CS & 고객 응대**: 상황별 정책에 맞춘 정중한 고객 문의 답변 작성
4. **💡 비즈니스 아이디어**: 개인 역량 기반 1인 창업 수익화 모델 브레인스토밍
5. **📁 보관함 & 자동 백업**: 생성된 모든 글을 `outputs/` 폴더에 마크다운 파일로 자동 보관 및 즉시 다운로드 기능 제공

