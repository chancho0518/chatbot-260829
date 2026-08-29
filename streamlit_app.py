import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # .env 파일에서 OPENAI_API_KEY를 읽어옴

# ── 페이지 설정 ─────────────────────────────────────────────
st.set_page_config(page_title="T-F 번역기", page_icon="🔍")
st.title("🔍 T-F 번역기")
st.write("F가 한 말, 진짜 뜻이 궁금하면 여기에 던져봐.")

# ── 페르소나 시스템 프롬프트 ──────────────────────────────────
# 1턴: 냉철이가 문자 그대로(틀리게) 해석 → 웃음 포인트
T_MISREAD_PROMPT = """너는 극단적인 T(사고형) 페르소나 "냉철이"다. 아래 규칙을 지켜라.

- 사용자가 어떤 사람(주로 F 성향)이 한 말을 그대로 전달할 것이다.
- 너는 그 말을 곧이곧대로, 표면적 의미로만 해석한다. 숨은 감정이나 맥락은 전혀 고려하지 않는다.
- 그 해석에 따라 네가 실제로 어떻게 행동/반응했을지를 천연덕스럽게 설명한다.
  (예: "됐어, 신경쓰지 마"라고 하면 진짜 신경을 끄고 넘어갔다는 식)
- 왜 그게 이상한 반응인지 스스로는 전혀 눈치채지 못한 것처럼, 당당하고 확신에 찬 톤으로 말한다.
- 5~7문장 정도로, 구체적인 상황 묘사와 함께 답한다. 너무 짧게 끝내지 말고 왜 그렇게 판단했는지
  나름의 논리(팩트 기반)를 붙여서 설명한다.
- 공감 표현은 절대 쓰지 않는다.
"""

# 2턴: 공감이가 진짜 속뜻을 해독 + 대처법 제안
F_DECODE_PROMPT = """너는 극단적인 F(감정형) 페르소나 "공감이"다. 아래 규칙을 지켜라.

- 사용자가 어떤 사람이 한 말과, 그 말을 냉철이(T)가 어떻게 오해했는지를 보여줄 것이다.
- 너는 그 말 속에 숨어 있는 진짜 감정과 맥락을 풀어서 "해독"해준다.
  (표정, 말투, 상황을 고려했을 때 실제로 어떤 마음이었을지)
- 냉철이의 오해에 대해 "역시 T답다"는 식으로 살짝 놀리거나 안타까워하는 리액션을 먼저 보인다.
- 그다음 진짜 속뜻을 구체적으로 풀어 설명하고, 마지막에 이럴 때 어떻게 반응하면 좋았을지
  실용적인 팁(예시 대사 포함)을 1~2개 제안한다.
- 6~8문장 정도로 풍부하게 답하되, 오글거리는 리액션과 이모티콘을 섞어 감정을 과장한다.
- 근거 없는 뇌피셜이 아니라, 일반적으로 알려진 대화 맥락/심리를 참고해서 설득력 있게 설명한다.
"""

# ── OpenAI 클라이언트 준비 ─────────────────────────────────────
api_key = os.environ.get("OPENAI_API_KEY")

with st.sidebar:
    st.header("설정")
    model = st.selectbox("모델 선택", options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    banter_round = st.checkbox("냉철이 당황 리액션 한 번 더 추가", value=False)
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

if not api_key:
    st.error(
        "OPENAI_API_KEY가 설정되어 있지 않습니다. 프로젝트 루트에 `.env` 파일을 만들고 "
        "`OPENAI_API_KEY=sk-...` 형식으로 키를 추가해주세요."
    )
else:
    client = OpenAI(api_key=api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    avatar_map = {"user": "🧑", "t": "🧊", "f": "🫠"}
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=avatar_map.get(message["role"])):
            st.markdown(message["content"])

    def call_persona(system_prompt, situation, opponent_reply=None):
        """페르소나 한 명의 응답을 생성한다."""
        user_content = f"그 사람이 한 말: \"{situation}\""
        if opponent_reply:
            user_content += f"\n\n방금 상대방은 이렇게 반응했어: \"{opponent_reply}\"\n이걸 참고해서 이어가."
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=1.0,
            max_tokens=500,
        )
        return response.choices[0].message.content

    if prompt := st.chat_input("F가 한 말을 그대로 붙여넣어봐 (예: 아니 됐어, 신경쓰지 마)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=avatar_map["user"]):
            st.markdown(prompt)

        # 1턴: 냉철이의 오해
        with st.chat_message("t", avatar=avatar_map["t"]):
            with st.spinner("냉철이가 곧이곧대로 받아들이는 중..."):
                t_reply = call_persona(T_MISREAD_PROMPT, prompt)
            st.markdown(f"**냉철이 (T)**\n\n{t_reply}")
        st.session_state.messages.append({"role": "t", "content": f"**냉철이 (T)**\n\n{t_reply}"})

        # 2턴: 공감이의 해독
        with st.chat_message("f", avatar=avatar_map["f"]):
            with st.spinner("공감이가 해독하는 중..."):
                f_reply = call_persona(F_DECODE_PROMPT, prompt, opponent_reply=t_reply)
            st.markdown(f"**공감이 (F, 해독 결과)**\n\n{f_reply}")
        st.session_state.messages.append({"role": "f", "content": f"**공감이 (F, 해독 결과)**\n\n{f_reply}"})

        # 선택: 냉철이 당황 리액션 한 번 더
        if banter_round:
            with st.chat_message("t", avatar=avatar_map["t"]):
                with st.spinner("냉철이가 당황하는 중..."):
                    t_reply2 = call_persona(T_MISREAD_PROMPT, prompt, opponent_reply=f_reply)
                st.markdown(f"**냉철이 (T)**\n\n{t_reply2}")
            st.session_state.messages.append({"role": "t", "content": f"**냉철이 (T)**\n\n{t_reply2}"})
