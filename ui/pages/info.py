import streamlit as st

from ui.theme import render_page_header, render_panel_header


FEATURE_CARDS = [
    (
        "Contratos",
        "Cadastro completo com geração automática de PDF, identificação única e controle de versão.",
    ),
    (
        "Dashboard",
        "KPIs executivos em 10 categorias com leitura financeira, operacional e estratégica.",
    ),
    (
        "Agente de IA",
        "Chat com guardrails: respostas baseadas apenas nos dados reais da carteira.",
    ),
    (
        "Kanban",
        "Fluxo visual de status com auditoria automática em cada transição.",
    ),
    (
        "Compliance",
        "Score de risco, conformidade jurídica e trilha de eventos por contrato.",
    ),
    (
        "Fornecedores",
        "SLA, pontualidade, qualidade e satisfação monitorados continuamente.",
    ),
]


def _render_feature_grid() -> None:
    cols = st.columns(3)
    for idx, (title, text) in enumerate(FEATURE_CARDS):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.caption(text)


def render_info_page():
    render_page_header(
        "Sobre o LogiChain AI",
        "Plataforma para gestão do ciclo de vida de contratos (CLM) com foco em operação, risco e governança.",
        badge="Product Brief",
    )

    render_panel_header("Capacidades da plataforma", "Visão rápida dos módulos do sistema.", icon="deployed_code")
    _render_feature_grid()

    render_panel_header("Fluxo de Vida do Contrato", "Pipeline operacional padrão.", icon="timeline")
    st.write("Gerado -> Assinado -> Protocolado -> Em vigor -> Finalizado")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Regras de Negócio**")
        st.markdown(
            """
- Contratos finalizados não aparecem no Kanban.
- Toda alteração de status gera auditoria automática.
- Admin override habilita transições fora da ordem.
- Edições geram versionamento incremental.
- PDF é gerado e vinculado após a criação.
            """
        )
    with col2:
        st.markdown("**Guardrails do Agente de IA**")
        st.markdown(
            """
- Sem dados no banco: sem resposta inventada.
- Contexto limitado ao acervo de contratos.
- Histórico de chat mantido por sessão.
- Modos: Consulta Geral, Resumo e Risco.
- Perguntas rápidas para acesso imediato.
            """
        )

    st.info("**Stack Tecnológico:** Python, Streamlit, SQLite, Plotly, ReportLab, OpenAI API")
