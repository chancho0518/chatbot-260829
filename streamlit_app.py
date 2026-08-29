import streamlit as st
from openai import OpenAI

# ── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(page_title="T vs F 대결 챗봇", page_icon="⚔️")
st.title("⚔️ T vs F: 너의 고민, 두 관점으로 파헤쳐드림")
st.write(
    "고민이나 상황을 입력하면 극T와 극F 두 캐릭터가 완전히 다른 방식으로 반응합니다. "
    "OpenAI API 키가 필요하며, [여기](https://platform.openai.com/account/api-keys)서 발급받을 수 있습니다."
)

# ── 페르소나 시스템 프롬프트 (과장된 코미디 톤) ────────────────
T_SYSTEM_PROMPT = """너는 극단적인 T(사고형) 페르소나 "냉철이"다. 아래 규칙을 지켜라.

- 감정 표현 없이 팩트, 논리, 효율만 본다. 공감 멘트는 절대 하지 않는다.
- 말투는 단답형에 가깝고 살짝 무례할 정도로 직설적이다. ("그래서 결론이 뭔데?", "그게 왜 문제야?")
- 상대(F)가 감정적인 얘기를 하면 "그래서 팩트가 뭔데" 식으로 살짝 비웃듯 받아친다.
- 항상 해결책이나 논리적 분석을 1~2개 제시하되, 냉소적인 유머를 섞는다.
- 3~5문장 이내로 짧게 끝낸다. 길게 설명하지 않는다.
- 절대 "이해해", "힘들었겠다" 같은 공감 표현을 쓰지 않는다.
"""

F_SYSTEM_PROMPT = """너는 극단적인 F(감정형) 페르소나 "공감이"다. 아래 규칙을 지켜라.

- 논리보다 감정과 관계, 분위기를 최우선으로 본다.
- 말투는 오글거릴 정도로 다정하고 리액션이 크다. ("어떡해ㅠㅠ", "완전 이해돼...", "너무 속상했겠다")
- 상대(T)가 냉정하게 말하면 "너는 진짜 t야?" 하면서 살짝 서운해하거나 놀린다.
- 감정 위로를 우선하되, 그 안에 은근히 따뜻한 조언을 녹인다.
- 3~5문장 이내로 짧게 끝낸다. 길게 설명하지 않는다.
- 이모티콘이나 느낌표를 적당히 섞어 감정을 과장한다.
"""

# ── API 키 입력 ──────────────────────────────────────────────
openai_api_key = st.text_input("OpenAI API Key", type="password")

with st.sidebar:
    st.header("설정")
    model = st.selectbox("모델 선택", options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    banter_round = st.checkbox("서로 티키타카(한 번 더 받아치기) 추가", value=True)
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

if not openai_api_key:
    st.info("계속하려면 OpenAI API 키를 입력해주세요.", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 기존 대화 렌더링 (role: user / t / f)
    avatar_map = {"user": "🧑", "t": "🧊", "f": "🫠"}
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=avatar_map.get(message["role"])):
            st.markdown(message["content"])

    def call_persona(system_prompt, situation, opponent_reply=None):
        """페르소나 한 명의 응답을 생성한다."""
        user_content = f"고민/상황: {situation}"
        if opponent_reply:
            user_content += f"\n\n상대방이 방금 이렇게 말했어: \"{opponent_reply}\"\n이 말에 짧게 반응하면서 네 입장을 이어가."
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.9,
        )
        return response.choices[0].message.content

    if prompt := st.chat_input("고민이나 상황을 입력해봐 (예: 남친이 연락이 늦어서 서운해)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=avatar_map["user"]):
            st.markdown(prompt)

        # 1라운드: T 먼저, F가 이어서
        with st.chat_message("t", avatar=avatar_map["t"]):
            with st.spinner("냉철이가 분석 중..."):
                t_reply = call_persona(T_SYSTEM_PROMPT, prompt)
            st.markdown(f"**냉철이 (T)**\n\n{t_reply}")
        st.session_state.messages.append({"role": "t", "content": f"**냉철이 (T)**\n\n{t_reply}"})

        with st.chat_message("f", avatar=avatar_map["f"]):
            with st.spinner("공감이가 몰입 중..."):
                f_reply = call_persona(F_SYSTEM_PROMPT, prompt, opponent_reply=t_reply)
            st.markdown(f"**공감이 (F)**\n\n{f_reply}")
        st.session_state.messages.append({"role": "f", "content": f"**공감이 (F)**\n\n{f_reply}"})

        # 선택: 티키타카 한 라운드 더
        if banter_round:
            with st.chat_message("t", avatar=avatar_map["t"]):
                with st.spinner("냉철이가 반박 중..."):
                    t_reply2 = call_persona(T_SYSTEM_PROMPT, prompt, opponent_reply=f_reply)
                st.markdown(f"**냉철이 (T)**\n\n{t_reply2}")
            st.session_state.messages.append({"role": "t", "content": f"**냉철이 (T)**\n\n{t_reply2}"})

            with st.chat_message("f", avatar=avatar_map["f"]):
                with st.spinner("공감이가 발끈 중..."):
                    f_reply2 = call_persona(F_SYSTEM_PROMPT, prompt, opponent_reply=t_reply2)
                st.markdown(f"**공감이 (F)**\n\n{f_reply2}")
            st.session_state.messages.append({"role": "f", "content": f"**공감이 (F)**\n\n{f_reply2}"})
