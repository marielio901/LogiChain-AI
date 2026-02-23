from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from services import list_contracts
from services.kpi_service import calculate_kpis, load_base_data
from ui.theme import render_empty_state, render_page_header, render_panel_header
from utils import brl

CEO_BLUE_SCALE = ["#1f7edc", "#3998f4", "#63b3fb", "#8fcbff", "#b8defe"]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = CEO_BLUE_SCALE


def _fmt_metric(key: str, value):
    if value is None:
        return "sem dados"
    if isinstance(value, dict):
        return "sem dados"
    if isinstance(value, (int, float)):
        if "pct" in key:
            return f"{value:.2f}%"
        if "valor" in key or "custo" in key or "economia" in key or "receita" in key or "multa" in key:
            return brl(value)
        if "dias" in key or "tempo" in key:
            return f"{value:.1f} dias"
        return f"{value:.2f}" if isinstance(value, float) else value
    return str(value)


def _metric_label(key: str) -> str:
    return key.replace("_", " ").capitalize()


def _metric_icon(label: str) -> str:
    tokens = [token for token in label.replace("/", " ").split() if token]
    initials = "".join(token[0] for token in tokens[:2]).upper()
    if len(initials) == 1:
        initials += "X"
    return initials or "KP"


def _render_cards(values: dict):
    scalar_items = [(k, v) for k, v in values.items() if not isinstance(v, dict)]
    if not scalar_items:
        st.info("Sem indicadores escalares para exibir.")
        return
    for start in range(0, len(scalar_items), 4):
        row_items = scalar_items[start : start + 4]
        cols = st.columns(4)
        for idx, (k, v) in enumerate(row_items):
            label = _metric_label(k)
            value = _fmt_metric(k, v)
            icon = _metric_icon(label)
            cols[idx].markdown(
                f"""
                <section class="lc-kpi-card">
                  <div class="lc-kpi-head">
                    <span class="lc-kpi-icon">{escape(icon)}</span>
                    <span class="lc-kpi-label">{escape(label)}</span>
                  </div>
                  <div class="lc-kpi-value">{escape(str(value))}</div>
                </section>
                """,
                unsafe_allow_html=True,
            )


def _dict_df(mapping: dict, key_name: str = "categoria", value_name: str = "valor") -> pd.DataFrame:
    if not mapping:
        return pd.DataFrame(columns=[key_name, value_name])
    return pd.DataFrame([{key_name: k, value_name: v} for k, v in mapping.items()])


def _style_figure(fig, pie: bool = False):
    if fig.layout.title and isinstance(fig.layout.title.text, str):
        if fig.layout.title.text.strip().lower() == "undefined":
            fig.update_layout(title=None)

    fig.update_layout(template="simple_white")
    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Plus Jakarta Sans, Manrope, sans-serif", color="#2f4b68", size=12),
        margin=dict(l=18, r=16, t=56, b=26),
        height=330,
        title=dict(x=0.02, y=0.98, xanchor="left", yanchor="top"),
        title_font=dict(family="Outfit, Plus Jakarta Sans, sans-serif", size=16, color="#123252"),
        legend=dict(
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
            font=dict(size=11, color="#3f5b77", family="Plus Jakarta Sans, sans-serif"),
        ),
    )
    if pie:
        fig.update_layout(
            legend=dict(
                orientation="h",
                y=-0.3,
                x=0,
                xanchor="left",
                yanchor="top",
                itemwidth=84,
                font=dict(size=11, family="Plus Jakarta Sans, sans-serif", color="#3f5b77"),
            ),
            margin=dict(l=8, r=8, t=56, b=100),
        )
        fig.update_traces(
            textinfo="percent",
            textposition="outside",
            textfont=dict(size=11, family="Plus Jakarta Sans, sans-serif", color="#36516d"),
            marker=dict(line=dict(color="#ffffff", width=1.5)),
        )
    else:
        fig.update_xaxes(
            automargin=True,
            gridcolor="rgba(180,205,236,0.55)",
            showgrid=True,
            zeroline=False,
            tickfont=dict(size=11, color="#49627c"),
        )
        fig.update_yaxes(
            automargin=True,
            gridcolor="rgba(180,205,236,0.55)",
            showgrid=True,
            zeroline=False,
            tickfont=dict(size=11, color="#49627c"),
        )
    return fig


def _plot_figure(fig, target=None, pie: bool = False):
    renderer = target if target is not None else st
    with renderer.container(border=True):
        st.plotly_chart(
            _style_figure(fig, pie=pie),
            use_container_width=True,
            config={"displaylogo": False, "responsive": True},
        )


def render_dashboard_page():
    render_page_header(
        "Dashboard Executivo",
        "Visão consolidada de KPIs e indicadores estratégicos da carteira de contratos.",
        badge="Control Tower",
    )

    render_panel_header("Filtros Globais", "Ajuste o recorte da análise antes de abrir os painéis de KPI.", icon="tune")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        type_filter = c1.selectbox("Tipo", ["", "Prestação de Serviço", "Fornecimento de Materiais", "Alocação"])
        dept_filter = c2.text_input("Departamento")
        contracted_filter = c3.text_input("Contratado")
        expiring_days = c4.selectbox("Janela de vencimento", [30, 45, 60, 90], index=0)

        use_period_filter = st.checkbox("Filtrar por período", value=True)
        c5, c6 = st.columns(2)
        default_start = date.today() - timedelta(days=90)
        default_end = date.today()
        date_from = c5.date_input("Período inicial", value=default_start)
        date_to = c6.date_input("Período final", value=default_end)

    if use_period_filter and date_from > date_to:
        st.warning("Período inválido: a data inicial deve ser menor ou igual à data final.")
        return

    filters = {
        "type": type_filter or None,
        "department": dept_filter or None,
        "contracted": contracted_filter or None,
        "date_from": str(date_from) if use_period_filter else None,
        "date_to": str(date_to) if use_period_filter else None,
    }

    filtered = list_contracts(filters=filters, include_finalized=True)
    if not filtered:
        render_empty_state(
            "Sem dados para os filtros selecionados.",
            "Ajuste período, departamento ou tipo para visualizar indicadores.",
            icon="query_stats",
        )
        return

    df = pd.DataFrame(filtered)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["signed_date"] = pd.to_datetime(df.get("signed_date"), errors="coerce")
    df["archived_date"] = pd.to_datetime(df.get("archived_date"), errors="coerce")
    df["vigencia_dias"] = (df["end_date"] - df["start_date"]).dt.days
    df["lead_time_dias"] = (df["signed_date"] - df["created_at"]).dt.days
    df["archive_time_dias"] = (df["archived_date"] - df["created_at"]).dt.days

    today = pd.Timestamp.today().normalize()
    df["dias_para_vencer"] = (df["end_date"] - today).dt.days

    _contracts_raw, additives_raw, compliance_raw, supplier_raw, _events_raw = load_base_data()
    contract_ids = set(df["id"].tolist())
    additives = additives_raw[additives_raw["contract_id"].isin(contract_ids)] if not additives_raw.empty else additives_raw
    compliance = compliance_raw[compliance_raw["contract_id"].isin(contract_ids)] if not compliance_raw.empty else compliance_raw
    supplier = supplier_raw[supplier_raw["contract_id"].isin(contract_ids)] if not supplier_raw.empty else supplier_raw

    kpi_result = calculate_kpis(expiring_days=expiring_days, contract_ids=df["id"].tolist())
    if not kpi_result["has_data"]:
        render_empty_state(
            "Sem dados de KPIs.",
            "Registre atividades e dados complementares para liberar todos os indicadores.",
            icon="database",
        )
        return

    sections = kpi_result["sections"]

    tabs = st.tabs(
        [
            "Geral",
            "Financeiros",
            "Prazo e Execução",
            "Compliance e Risco",
            "Operacionais",
            "Fornecedor",
            "Jurídicos",
            "CLM",
            "Estratégicos",
            "Avançados",
        ]
    )

    with tabs[0]:
        _render_cards(
            {
                "total_contratos": len(df),
                "valor_total_contratado": df["contract_value"].fillna(0).sum(),
                "contratos_em_vigor": int((df["status"] == "Em vigor").sum()),
                "contratos_finalizados": int((df["status"] == "Finalizado").sum()),
            }
        )

        col_a, col_b = st.columns(2)
        fig_status = px.pie(df, names="status", title="Distribuição por Status")
        fig_type = px.bar(df.groupby("type", as_index=False)["contract_value"].sum(), x="type", y="contract_value", title="Valor por Tipo")
        _plot_figure(fig_status, target=col_a, pie=True)
        _plot_figure(fig_type, target=col_b)

        fig_dept = px.bar(
            df.groupby("department", as_index=False)["contract_value"].sum().sort_values("contract_value", ascending=False),
            x="department",
            y="contract_value",
            title="Valor por Departamento",
        )
        _plot_figure(fig_dept)

    with tabs[1]:
        _render_cards(sections["financeiro"])

        fin_df = pd.DataFrame(
            {
                "Métrica": ["Contratado", "Executado", "Savings", "Aditivos", "Multas"],
                "Valor": [
                    df["contract_value"].fillna(0).sum(),
                    df["executed_value"].fillna(0).sum(),
                    df["savings_value"].fillna(0).sum(),
                    additives["additive_value"].fillna(0).sum() if not additives.empty else 0,
                    df["penalties_value"].fillna(0).sum(),
                ],
            }
        )
        c1, c2 = st.columns(2)
        _plot_figure(px.bar(fin_df, x="Métrica", y="Valor", title="Composição Financeira"), target=c1)
        _plot_figure(px.histogram(df, x="roi_value", nbins=20, title="Distribuição de ROI (%)"), target=c2)

    with tabs[2]:
        _render_cards(sections["prazo_execucao"])

        prazo_bucket = pd.DataFrame(
            {
                "Faixa": ["Vence <=30 dias", "Vence 31-60 dias", "Vence >60 dias", "Vencido"],
                "Qtd": [
                    int(((df["dias_para_vencer"] >= 0) & (df["dias_para_vencer"] <= 30)).sum()),
                    int(((df["dias_para_vencer"] > 30) & (df["dias_para_vencer"] <= 60)).sum()),
                    int((df["dias_para_vencer"] > 60).sum()),
                    int((df["dias_para_vencer"] < 0).sum()),
                ],
            }
        )
        c1, c2 = st.columns(2)
        _plot_figure(px.histogram(df, x="vigencia_dias", nbins=20, title="Distribuição de Vigência (dias)"), target=c1)
        _plot_figure(px.bar(prazo_bucket, x="Faixa", y="Qtd", title="Pipeline de Vencimento"), target=c2)

    with tabs[3]:
        _render_cards(sections["compliance_risco"])
        if compliance.empty:
            render_empty_state(
                "Sem dados de compliance no recorte atual.",
                "Preencha checkpoints de compliance em 'Registrar Atividades' para liberar esta aba.",
                icon="gavel",
            )
        else:
            c1, c2 = st.columns(2)
            _plot_figure(px.histogram(compliance, x="risk_score", nbins=20, title="Distribuição de Risco"), target=c1)

            audited_map = _dict_df({"Auditados": int(compliance["audited"].fillna(0).sum()), "Não auditados": int((compliance["audited"].fillna(0) == 0).sum())}, "status", "qtd")
            _plot_figure(px.pie(audited_map, names="status", values="qtd", title="Auditoria"), target=c2, pie=True)

            out_map = _dict_df({"Fora do padrão": int(compliance["out_of_standard"].fillna(0).sum()), "Dentro do padrão": int((compliance["out_of_standard"].fillna(0) == 0).sum())}, "status", "qtd")
            _plot_figure(px.bar(out_map, x="status", y="qtd", title="Conformidade Jurídica"))

    with tabs[4]:
        _render_cards(sections["operacionais"])

        tipo_df = _dict_df(df["type"].value_counts().to_dict(), "tipo", "qtd")
        dep_df = _dict_df(df["department"].value_counts().to_dict(), "departamento", "qtd")
        supplier_names = df["contracted"].apply(lambda x: x.get("name", "N/A") if isinstance(x, dict) else "N/A")
        supplier_df = _dict_df(supplier_names.value_counts().to_dict(), "fornecedor", "qtd")

        c1, c2 = st.columns(2)
        _plot_figure(px.bar(tipo_df, x="tipo", y="qtd", title="Contratos por Tipo"), target=c1)
        _plot_figure(px.bar(dep_df, x="departamento", y="qtd", title="Contratos por Departamento"), target=c2)
        _plot_figure(px.bar(supplier_df.head(10), x="fornecedor", y="qtd", title="Top 10 Fornecedores por Volume"))

    with tabs[5]:
        _render_cards(sections["fornecedor"])
        if supplier.empty:
            render_empty_state(
                "Sem dados de desempenho do fornecedor no recorte atual.",
                "Atualize métricas de SLA, pontualidade e qualidade para visualizar análises.",
                icon="handshake",
            )
        else:
            c1, c2 = st.columns(2)
            _plot_figure(
                px.scatter(
                    supplier,
                    x="sla_pct",
                    y="on_time_pct",
                    color="quality_score",
                    title="SLA x Pontualidade (cor = qualidade)",
                ),
                target=c1,
            )
            _plot_figure(px.histogram(supplier, x="delivery_fail_rate", nbins=20, title="Distribuição de Falhas na Entrega"), target=c2)
            _plot_figure(px.box(supplier, y="satisfaction_score", title="Satisfação com Fornecedores"))

    with tabs[6]:
        _render_cards(sections["juridicos"])
        legal_df = pd.DataFrame(
            {
                "Indicador": ["Com cláusulas críticas", "Sem cláusulas críticas", "Com potencial litígio"],
                "Qtd": [
                    int(df["critical_clauses"].fillna(0).sum()),
                    int((df["critical_clauses"].fillna(0) == 0).sum()),
                    int(df["legal_notes"].fillna("").str.contains("litígio|litigio", case=False, regex=True).sum()),
                ],
            }
        )
        _plot_figure(px.bar(legal_df, x="Indicador", y="Qtd", title="Riscos Jurídicos"))

    with tabs[7]:
        _render_cards(sections["clm"])

        c1, c2 = st.columns(2)
        _plot_figure(px.histogram(df.dropna(subset=["lead_time_dias"]), x="lead_time_dias", nbins=20, title="Lead Time Criação -> Assinatura (dias)"), target=c1)

        digital_map = _dict_df(
            {
                "Digital": int(df["digitally_signed"].fillna(0).sum()),
                "Físico": int((df["digitally_signed"].fillna(0) == 0).sum()),
            },
            "tipo_assinatura",
            "qtd",
        )
        _plot_figure(px.pie(digital_map, names="tipo_assinatura", values="qtd", title="Assinatura Digital vs Física"), target=c2, pie=True)

        _plot_figure(px.histogram(df.dropna(subset=["archive_time_dias"]), x="archive_time_dias", nbins=20, title="Tempo de Arquivamento (dias)"))

    with tabs[8]:
        _render_cards(sections["estrategicos"])

        strategic_map = _dict_df(
            {
                "Alinhados": int(df["strategic_alignment"].fillna(0).sum()),
                "Não alinhados": int((df["strategic_alignment"].fillna(0) == 0).sum()),
            },
            "status",
            "qtd",
        )
        c1, c2 = st.columns(2)
        _plot_figure(px.pie(strategic_map, names="status", values="qtd", title="Alinhamento Estratégico"), target=c1, pie=True)
        _plot_figure(px.bar(df.groupby("department", as_index=False)["revenue_contribution"].sum(), x="department", y="revenue_contribution", title="Contribuição de Receita por Área"), target=c2)
        _plot_figure(px.histogram(df, x="supplier_diversification_score", nbins=20, title="Diversificação de Fornecedores"))

    with tabs[9]:
        _render_cards(sections["avancados"])

        adv_means = pd.DataFrame(
            {
                "Métrica": ["Maturidade", "Governança", "Automação", "Prob. Inadimplência", "Ruptura"],
                "Valor": [
                    df["maturity_score"].fillna(0).mean(),
                    df["governance_index"].fillna(0).mean(),
                    df["automation_pct"].fillna(0).mean(),
                    df["default_probability"].fillna(0).mean(),
                    df["disruption_predictive_score"].fillna(0).mean(),
                ],
            }
        )
        c1, c2 = st.columns(2)
        _plot_figure(px.bar(adv_means, x="Métrica", y="Valor", title="Médias de Indicadores Avançados"), target=c1)
        _plot_figure(px.histogram(df, x="aggregate_financial_risk", nbins=20, title="Risco Financeiro Agregado"), target=c2)
