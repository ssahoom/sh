import os
from datetime import datetime
import streamlit as st
from ollama_client import OllamaService
from local_agent_executor import LocalAgentExecutor

st.set_page_config(
    page_title="AI 1인 기업 자동화 허브",
    page_icon="💼",
    layout="wide"
)

# 생성물 저장 폴더 준비
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# 세션 히스토리 초기화
if "history" not in st.session_state:
    st.session_state.history = []

def save_to_history(category: str, title: str, content: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item = {
        "timestamp": timestamp,
        "category": category,
        "title": title,
        "content": content
    }
    st.session_state.history.insert(0, item)
    # 로컬 파일로도 자동 백업
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{category}.md"
    filepath = os.path.join(OUTPUTS_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# [{category}] {title}\n- 생성일시: {timestamp}\n\n{content}")
    except Exception:
        pass

# 서비스 인스턴스 캐싱
@st.cache_resource
def get_service():
    return OllamaService()

service = get_service()

# 사이드바: Ollama 상태 점검 및 모델 선택
st.sidebar.title("⚙️ 시스템 설정")

is_online = service.is_server_running()
if is_online:
    st.sidebar.success(f"🟢 Ollama 서버 연결됨\n({service.base_url})")
    raw_models = service.list_installed_models()
    if not raw_models:
        available_models = [service.model]
    else:
        # 무료 로컬 모델을 우선 배치
        local_mods = [m for m in raw_models if not m.endswith(":cloud")]
        cloud_mods = [m for m in raw_models if m.endswith(":cloud")]
        available_models = local_mods + cloud_mods

    default_idx = available_models.index(service.model) if service.model in available_models else 0
    selected_model = st.sidebar.selectbox(
        "사용할 로컬 모델", 
        available_models, 
        index=default_idx,
        format_func=lambda m: f"🟢 {m} (로컬 모델)" if not m.endswith(":cloud") else f"☁️ {m} (유료 클라우드)"
    )
else:
    st.sidebar.error("🔴 Ollama 서버 오프라인")
    st.sidebar.info("터미널에서 `ollama serve`를 확인해 주세요.")
    selected_model = service.model

temperature = st.sidebar.slider("창의성 (Temperature)", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
st.sidebar.markdown("---")
st.sidebar.caption(f"📁 자동 백업 폴더: `{OUTPUTS_DIR}`")

# 메인 화면
st.title("💼 AI 1인 기업 업무 자동화 어시스턴트")
st.caption("로컬 Ollama LLM을 활용한 비용 0원 비즈니스 자동화 워크스페이스")

# 기능 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "✍️ 마케팅 & 카피라이팅",
    "📝 블로그 콘텐츠 작성",
    "💬 고객 문의/CS 응답",
    "💡 신규 비즈니스 아이디어",
    "📁 보관함 & 히스토리",
    "🤖 Connect AI 자율 에이전트"
])

# 1. 마케팅 카피라이팅 탭
with tab1:
    st.subheader("타깃 마케팅 카피 및 광고 문구 생성")
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("제품/서비스명", placeholder="예: 1인 기업용 노션 업무 템플릿")
        target_audience = st.text_input("타깃 고객", placeholder="예: 시간 관리가 필요한 프리랜서 및 1인 창업가")
    with col2:
        tone = st.selectbox("어조 (톤앤매너)", ["친근하고 감성적인", "신뢰감 있고 전문적인", "위트 있고 직관적인", "긴박감을 주는 프로모션형"])
        key_features = st.text_area("주요 특징/혜택", placeholder="예: 일정 관리 자동화, 매출 대시보드 제공, 초보자용 가이드북 포함", height=80)

    if st.button("🚀 마케팅 카피 생성", key="btn_copy"):
        if not is_online:
            st.error("Ollama 서버가 켜져 있지 않습니다.")
        elif not product_name:
            st.warning("제품/서비스명을 입력해 주세요.")
        else:
            with st.spinner("로컬 AI가 문구를 작성 중입니다..."):
                prompt = f"""
제품/서비스명: {product_name}
타깃 고객: {target_audience}
어조: {tone}
주요 특징: {key_features}

위 정보를 바탕으로 매력적인 SNS 광고 카피 3가지 버전(인스타그램 피드용, 헤드라인형, 스토리형)을 작성해 주세요.
해시태그도 5개 추천해 주세요.
"""
                try:
                    service.temperature = temperature
                    result = service.chat(prompt, system_prompt="당신은 최고의 1인 기업 전문 디지털 마케터입니다.", model=selected_model)
                    st.session_state["last_copy"] = result
                    save_to_history("마케팅카피", product_name, result)
                except Exception as e:
                    st.error(f"생성 실패: {e}")

    if "last_copy" in st.session_state:
        st.markdown("### 📋 생성 결과")
        st.markdown(st.session_state["last_copy"])
        st.download_button(
            label="💾 마크다운 파일로 다운로드",
            data=st.session_state["last_copy"],
            file_name=f"마케팅카피_{product_name or '결과'}.md",
            mime="text/markdown"
        )

# 2. 블로그 콘텐츠 탭
with tab2:
    st.subheader("SEO 친화적 정보성 블로그 아티클 작성")
    topic = st.text_input("블로그 주제 또는 키워드", placeholder="예: 직장인을 위한 퇴사 전 1인 창업 준비 체크리스트")

    if st.button("📄 블로그 초안 작성", key="btn_blog"):
        if not is_online:
            st.error("Ollama 서버를 먼저 켜주세요.")
        elif not topic:
            st.warning("주제를 입력해 주세요.")
        else:
            with st.spinner("블로그 포스팅 생성 중..."):
                prompt = f"주제: '{topic}'에 대해 네이버/티스토리 블로그에 바로 올릴 수 있는 가독성 높은 글을 마크다운 형식으로 작성해 줘."
                try:
                    service.temperature = temperature
                    result = service.chat(prompt, system_prompt="당신은 파워 블로거이자 전문 콘텐츠 작가입니다.", model=selected_model)
                    st.session_state["last_blog"] = result
                    save_to_history("블로그", topic, result)
                except Exception as e:
                    st.error(f"생성 실패: {e}")

    if "last_blog" in st.session_state:
        st.markdown("### 📋 생성 결과")
        st.markdown(st.session_state["last_blog"])
        st.download_button(
            label="💾 블로그 글 다운로드",
            data=st.session_state["last_blog"],
            file_name=f"블로그_{topic or '포스팅'}.md",
            mime="text/markdown"
        )

# 3. CS / 고객 문의 응답 탭
with tab3:
    st.subheader("고객 문의에 대한 정중하고 명확한 답변 생성")
    inquiry = st.text_area("고객 문의 내용 입력", placeholder="예: 결제 완료했는데 다운로드 링크가 이메일로 오지 않았습니다. 환불해 주세요.", height=120)
    company_policy = st.text_input("비즈니스 대응 방침", value="확인 후 재발송 우선 안내, 미해결 시 전액 환불 정책 안내")

    if st.button("✉️ 답변 메일/메시지 생성", key="btn_cs"):
        if not is_online:
            st.error("Ollama 서버 연결 필요")
        elif not inquiry:
            st.warning("고객 문의 내용을 입력해 주세요.")
        else:
            with st.spinner("답변안 작성 중..."):
                prompt = f"고객 문의:\n\"{inquiry}\"\n\n회사의 기본 방침: {company_policy}\n\n위 문의에 대해 정중하고 신뢰감을 주는 고객 응대 답변 메일 초안을 작성해 줘."
                try:
                    service.temperature = temperature
                    result = service.chat(prompt, system_prompt="당신은 고객 감동을 이끄는 전문 CS 매니저입니다.", model=selected_model)
                    st.session_state["last_cs"] = result
                    save_to_history("고객응대", inquiry[:20], result)
                except Exception as e:
                    st.error(f"생성 실패: {e}")

    if "last_cs" in st.session_state:
        st.markdown("### 📋 생성 결과")
        st.markdown(st.session_state["last_cs"])
        st.download_button(
            label="💾 답변 텍스트 다운로드",
            data=st.session_state["last_cs"],
            file_name="고객문의답변.txt",
            mime="text/plain"
        )

# 4. 아이디어 탭
with tab4:
    st.subheader("1인 기업 비즈니스 모델 & 수익화 전략 브레인스토밍")
    interest_field = st.text_input("관심 분야 / 전문 기술", placeholder="예: 파이썬 코딩, 주식 데이터 분석, 엑셀 자동화")

    if st.button("💡 비즈니스 아이디어 제안받기", key="btn_idea"):
        if not is_online:
            st.error("Ollama 서버 연결 필요")
        elif not interest_field:
            st.warning("관심 분야를 입력해 주세요.")
        else:
            with st.spinner("아이디어 구상 중..."):
                prompt = f"나의 역량 및 관심 분야: {interest_field}\n\n이를 기반으로 혼자서 시작할 수 있는 저자본 1인 창업 비즈니스 모델 3가지와 각각의 수익화 경로를 구체적으로 제안해 줘."
                try:
                    service.temperature = temperature
                    result = service.chat(prompt, system_prompt="당신은 성공적인 1인 창업을 돕는 비즈니스 액셀러레이터입니다.", model=selected_model)
                    st.session_state["last_idea"] = result
                    save_to_history("비즈니스아이디어", interest_field, result)
                except Exception as e:
                    st.error(f"생성 실패: {e}")

    if "last_idea" in st.session_state:
        st.markdown("### 📋 생성 결과")
        st.markdown(st.session_state["last_idea"])
        st.download_button(
            label="💾 아이디어 리포트 다운로드",
            data=st.session_state["last_idea"],
            file_name="1인기업_아이디어기획서.md",
            mime="text/markdown"
        )

# 5. 보관함 & 히스토리 탭
with tab5:
    st.subheader("📁 생성된 콘텐츠 히스토리 및 보관함")
    if not st.session_state.history:
        st.info("아직 생성된 콘텐츠가 없습니다. 각 탭에서 AI 작업을 실행해 보세요.")
    else:
        for idx, item in enumerate(st.session_state.history):
            with st.expander(f"[{item['category']}] {item['title']} ({item['timestamp']})", expanded=(idx == 0)):
                st.markdown(item["content"])
                st.download_button(
                    label="📥 다운로드",
                    data=item["content"],
                    file_name=f"{item['category']}_{idx+1}.md",
                    key=f"dl_hist_{idx}"
                )

# 6. Connect AI 자율 코딩 에이전트 탭
with tab6:
    st.subheader("🤖 Connect AI LAB 로컬 자율 코딩 에이전트")
    st.caption("로컬 모델(Gemma)이 지시를 받아 프로젝트 내에 파일을 직접 생성하거나 수정합니다.")
    agent_cmd = st.text_area(
        "에이전트 지시 사항 입력",
        placeholder="예: checklist.md 파일을 만들고 1인 기업 일일 업무 체크리스트를 작성해줘\n또는: README.md에 프로젝트 소개 문구를 수정해줘",
        height=100
    )

    if st.button("🚀 로컬 에이전트 실행", key="btn_agent"):
        if not is_online:
            st.error("Ollama 서버 연결 필요")
        elif not agent_cmd:
            st.warning("지시 사항을 입력해 주세요.")
        else:
            with st.spinner("로컬 에이전트가 코드를 분석하고 파일 작업을 진행 중입니다..."):
                try:
                    executor = LocalAgentExecutor()
                    res = executor.run(agent_cmd, model=selected_model)
                    st.markdown("### 📋 AI 설명")
                    st.markdown(res["response"])
                    if res["reports"]:
                        st.markdown("### ⚙️ 수행된 액션 리포트")
                        for r in res["reports"]:
                            st.info(r)
                    else:
                        st.warning("수행된 파일 생성/수정 액션이 없습니다.")
                except Exception as e:
                    st.error(f"에이전트 실행 실패: {e}")
