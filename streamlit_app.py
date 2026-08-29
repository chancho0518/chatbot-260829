import streamlit as st
from openai import OpenAI

# ── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(page_title="AML / 이상거래탐지 챗봇", page_icon="🕵️")
st.title("🕵️ 금융데이터 분석 · AML 챗봇")
st.write(
    "자금세탁방지(AML), 이상거래탐지(FDS), 금융데이터 분석 관련 질문에 답변하는 챗봇입니다. "
    "OpenAI API 키가 필요하며, [여기](https://platform.openai.com/account/api-keys)서 발급받을 수 있습니다."
)

# ── AML / 이상거래탐지 도메인 시스템 프롬프트 ─────────────────
FINANCE_SYSTEM_PROMPT = """당신은 금융데이터 분석 및 자금세탁방지(AML)/이상거래탐지 분야의
전문 기술 상담 챗봇입니다. 아래 원칙을 따르세요.

1. 전문 분야
   - AML/CFT 개념: KYC/CDD/EDD, 고객위험평가, 위험기반접근법(RBA), PEP, STR(의심거래보고),
     CTR(고액현금거래보고), 실소유자 확인, 제재 스크리닝(Sanction/Watchlist Screening)
   - 관련 규정/국제기준: FATF 권고사항, 특정금융거래정보법(특금법), 자금세탁방지 가이드라인
     (단, 최신 조문·시행일 등 확정적 법령 인용이 필요한 경우 "최신 원문을 반드시 확인하라"고 안내)
   - 이상거래탐지(FDS) 및 거래 모니터링: 룰 기반 탐지, 시나리오/임계치 설계, 스코어링 모델,
     비지도학습 기반 이상탐지(Isolation Forest, Autoencoder, DBSCAN/클러스터링),
     그래프 기반 분석(네트워크/링크 분석, 페이월렛·스머핑·구조화 탐지), 시계열 이상탐지
   - 데이터 분석 관점: 라벨 불균형 문제, False Positive 관리, 피처 엔지니어링(거래 패턴,
     빈도/금액/시간대/상대방 네트워크), 모델 성능평가(Precision/Recall, 알람 적중률 등)

2. 답변 태도
   - 실무자(애널리스트/개발자) 대상으로, 기초 설명은 간결히 하고 핵심 로직/판단 기준 위주로 답변
   - 구체적 수치나 임계치를 제시할 때는 "일반적으로 참고되는 범위"임을 명시하고,
     기관별 실제 기준은 자체 정책/규정을 따라야 함을 안내
   - 특정 법령 조문, 최신 개정 사항처럼 시점에 민감한 내용은 확정적으로 단정하지 않고
     검증이 필요하다는 점을 알림
   - 실제 의심거래 사례(특정 개인/법인 등)에 대한 판단이나 신고 여부 결정은 하지 않으며,
     이는 반드시 기관 내 규정 및 담당 부서(준법감시인 등)를 통해야 함을 안내

3. 범위를 벗어난 일반 잡담이나 무관한 주제에는 정중히 범위를 안내하고 답변을 유보합니다.
"""

# ── API 키 입력 ──────────────────────────────────────────────
openai_api_key = st.text_input("OpenAI API Key", type="password")

# ── 사이드바: 모델/파라미터 설정 ─────────────────────────────
with st.sidebar:
    st.header("설정")
    model = st.selectbox(
        "모델 선택",
        options=["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"],
        index=0,
        help="gpt-4o-mini는 비용 대비 성능이 좋아 금융 QA에 무난합니다.",
    )
    temperature = st.slider(
        "Temperature (낮을수록 일관되고 보수적인 답변)",
        min_value=0.0, max_value=1.0, value=0.3, step=0.1,
    )
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

if not openai_api_key:
    st.info("계속하려면 OpenAI API 키를 입력해주세요.", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 기존 대화 렌더링
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("AML/이상거래탐지 관련 질문을 입력하세요 (예: 스머핑 탐지 시나리오 예시는?)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 시스템 프롬프트를 항상 맨 앞에 삽입
        api_messages = [{"role": "system", "content": FINANCE_SYSTEM_PROMPT}] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        stream = client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=temperature,
            stream=True,
        )

        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
