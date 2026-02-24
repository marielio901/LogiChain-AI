import streamlit as st

from services.ai_agent import answer_question
from ui.theme import render_page_header, render_panel_header


QUICK_PROMPTS = [
    "Quais contratos vencem nos próximos 45 dias?",
    "Liste contratos em vigor com risco alto.",
    "Qual o total contratado por fornecedor?",
    "Mostre o resumo do contrato LC-2026-001.",
]


def _init_chat_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def _append_message(role: str, content: str):
    st.session_state.chat_history.append({"role": role, "content": content})


def _process_prompt(prompt: str, mode: str):
    clean_prompt = (prompt or "").strip()
    if not clean_prompt:
        return
    _append_message("user", clean_prompt)
    with st.spinner("Consultando base de contratos..."):
        response = answer_question(clean_prompt, mode=mode)
    _append_message("assistant", response)


def render_ai_agent_page():
    render_page_header(
        "Agente de IA para Contratos",
        "Consulte riscos, vencimentos e resumos da carteira com respostas fundamentadas nos dados reais.",
        badge="Ops Copilot",
    )
    render_panel_header(
        "Configuração da conversa",
        "Escolha o modo de análise e utilize atalhos para acelerar perguntas operacionais.",
        icon="smart_toy",
    )

    _init_chat_state()

    c1, c2 = st.columns([4, 1])
    mode = c1.selectbox("Modo", ["Consulta Geral", "Resumo do Contrato", "Análise de Risco"])
    if c2.button("Limpar chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.caption("Perguntas rápidas")
    q1, q2 = st.columns(2)
    quick_prompt = None
    if q1.button(QUICK_PROMPTS[0], use_container_width=True):
        quick_prompt = QUICK_PROMPTS[0]
    if q2.button(QUICK_PROMPTS[1], use_container_width=True):
        quick_prompt = QUICK_PROMPTS[1]
    q3, q4 = st.columns(2)
    if q3.button(QUICK_PROMPTS[2], use_container_width=True):
        quick_prompt = QUICK_PROMPTS[2]
    if q4.button(QUICK_PROMPTS[3], use_container_width=True):
        quick_prompt = QUICK_PROMPTS[3]

    user_prompt = st.chat_input("Pergunte sobre contratos, riscos, vencimentos, fornecedor ou número do contrato...")

    if quick_prompt:
        _process_prompt(quick_prompt, mode)
        st.rerun()
    elif user_prompt:
        _process_prompt(user_prompt, mode)
        st.rerun()

    if not st.session_state.chat_history:
        with st.chat_message("assistant"):
            st.markdown(
                "Faça uma pergunta como:\n"
                "- Quais contratos vencem nos próximos 45 dias?\n"
                "- Liste contratos em vigor com risco alto.\n"
                "- Mostre o resumo do contrato LC-2026-001."
            )
        return

    for message in st.session_state.chat_history:
        role = "assistant" if message.get("role") == "assistant" else "user"
        with st.chat_message(role):
            st.markdown(message.get("content", ""))
