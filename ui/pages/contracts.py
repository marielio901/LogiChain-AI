from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from db.connection import get_connection
from services import (
    list_kanban_contracts,
    list_contracts,
    update_status,
    download_pdf_bytes,
    generate_and_attach_pdf,
    edit_contract,
    add_additive,
    add_event,
)
from ui.theme import render_empty_state, render_page_header, render_panel_header
from utils import brl


STATUS_FLOW = ["Gerado", "Assinado", "Protocolado", "Em vigor", "Finalizado"]


def _risk_map():
    conn = get_connection()
    rows = conn.execute("SELECT contract_id, risk_score FROM compliance_checks").fetchall()
    conn.close()
    return {r["contract_id"]: r["risk_score"] for r in rows}


def _next_status(status: str):
    if status not in STATUS_FLOW:
        return status
    idx = STATUS_FLOW.index(status)
    return STATUS_FLOW[min(idx + 1, len(STATUS_FLOW) - 1)]


def _prev_status(status: str):
    if status not in STATUS_FLOW:
        return status
    idx = STATUS_FLOW.index(status)
    return STATUS_FLOW[max(idx - 1, 0)]


def _risk_label(score: float | int | str) -> str:
    if not isinstance(score, (int, float)):
        return "N/A"
    if score > 70:
        return f"{score:.0f} (alto)"
    if score > 40:
        return f"{score:.0f} (médio)"
    return f"{score:.0f} (baixo)"


def _status_step(status: str) -> int:
    if status not in STATUS_FLOW:
        return -1
    return STATUS_FLOW.index(status)


def _status_token(status: str) -> str:
    return {
        "Gerado": "gerado",
        "Assinado": "assinado",
        "Protocolado": "protocolado",
        "Em vigor": "em_vigor",
        "Finalizado": "finalizado",
    }.get(status, "gerado")


def _risk_tier(score: float | int | str) -> str:
    if not isinstance(score, (int, float)):
        return "unknown"
    if score > 70:
        return "high"
    if score > 40:
        return "medium"
    return "low"


def render_contracts_page():
    render_page_header(
        "Gestão de Contratos",
        "Visualize, filtre e gerencie todo o ciclo de vida com quadro Kanban e visão analítica em tabela.",
        badge="CLM Ops",
    )

    tab_kanban, tab_table = st.tabs(["Kanban", "Tabela e Detalhes"])

    with tab_kanban:
        render_panel_header(
            "Fluxo de status",
            "Gerado → Assinado → Protocolado → Em vigor → Finalizado",
            icon="account_tree",
        )
        contracts = list_kanban_contracts()
        risk_map = _risk_map()
        if not contracts:
            render_empty_state(
                "Nenhum contrato ativo no Kanban.",
                "Crie novos contratos para iniciar o fluxo operacional.",
                icon="view_kanban",
            )
        else:
            columns = st.columns(4)
            visible_status = STATUS_FLOW[:-1]
            for i, status in enumerate(visible_status):
                with columns[i]:
                    items = [c for c in contracts if c["status"] == status]
                    st.markdown(
                        f"""
                        <div class="lc-kanban-column-title">
                          <span>{escape(status)}</span>
                          <span class="lc-kanban-count">{len(items)}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if not items:
                        render_empty_state("Sem contratos", "Nenhum item nesta etapa do fluxo.", icon="inventory_2")
                    for c in items:
                        with st.container():
                            risk_score = risk_map.get(c["id"], "N/A")
                            risk_label = _risk_label(risk_score)
                            contracted_name = c.get("contracted", {}).get("name", "N/A")
                            status_token = _status_token(c["status"])
                            risk_tier = _risk_tier(risk_score)
                            with st.container(border=True):
                                st.markdown(
                                    f"""
                                    <div class="lc-kanban-meta">
                                      <span class="lc-kanban-chip lc-status-{status_token}">{escape(c["status"])}</span>
                                      <span class="lc-kanban-chip lc-risk-{risk_tier}">Risco: {escape(risk_label)}</span>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                                st.caption(c["contract_number"])
                                st.write(f"**{c['title']}**")
                                st.write(f"Tipo: {c['type']}")
                                st.write(f"Vigência: {c['start_date']} -> {c['end_date']}")
                                st.write(f"Contratado: {contracted_name}")
                                st.write(f"Valor: {brl(c['contract_value'])}")

                                step = _status_step(c["status"])
                                can_go_back = step > 0
                                can_go_next = 0 <= step < len(STATUS_FLOW) - 1
                                next_status = _next_status(c["status"])
                                next_label = "Finalizar" if next_status == "Finalizado" else "Próximo"

                                c1, c2 = st.columns(2)
                                if c1.button(
                                    "Voltar",
                                    key=f"prev_{c['id']}",
                                    use_container_width=True,
                                    disabled=not can_go_back,
                                ):
                                    try:
                                        update_status(c["id"], _prev_status(c["status"]), user="ui")
                                        st.rerun()
                                    except ValueError as e:
                                        st.error(str(e))
                                if c2.button(
                                    next_label,
                                    key=f"next_{c['id']}",
                                    use_container_width=True,
                                    disabled=not can_go_next,
                                ):
                                    try:
                                        update_status(c["id"], next_status, user="ui")
                                        st.rerun()
                                    except ValueError as e:
                                        st.error(str(e))

    with tab_table:
        render_panel_header("Filtros da Tabela", "Refine a busca e abra ações por contrato sem sair da página.", icon="filter_alt")
        c1, c2, c3, c4 = st.columns(4)
        type_filter = c1.selectbox("Tipo", ["", "Prestação de Serviço", "Fornecimento de Materiais", "Alocação"])
        status_filter = c2.selectbox("Status", [""] + STATUS_FLOW)
        dept_filter = c3.text_input("Departamento")
        contracted_filter = c4.text_input("Contratado")

        c5, c6, c7, c8 = st.columns(4)
        min_value = c5.number_input("Valor mínimo", min_value=0.0, value=0.0)
        max_value = c6.number_input("Valor máximo", min_value=0.0, value=0.0)
        use_date_filter = c7.checkbox("Filtrar por criação", value=False)
        c8.caption("Período")
        d1, d2 = st.columns(2)
        date_from = d1.date_input("Criado de", value=date.today().replace(day=1), disabled=not use_date_filter)
        date_to = d2.date_input("Criado até", value=date.today(), disabled=not use_date_filter)

        if use_date_filter and date_from > date_to:
            st.warning("Período inválido: a data inicial deve ser menor ou igual à final.")
            return

        order = st.selectbox(
            "Ordenar por",
            [
                "created_at DESC",
                "created_at ASC",
                "end_date ASC",
                "contract_value DESC",
                "status ASC",
            ],
        )

        filters = {
            "type": type_filter or None,
            "status": status_filter or None,
            "department": dept_filter or None,
            "contracted": contracted_filter or None,
            "min_value": min_value if min_value > 0 else None,
            "max_value": max_value if max_value > 0 else None,
            "date_from": str(date_from) if use_date_filter else None,
            "date_to": str(date_to) if use_date_filter else None,
            "order_by": order,
        }

        contracts = list_contracts(filters=filters, include_finalized=True)

        if not contracts:
            render_empty_state(
                "Nenhum contrato encontrado para os filtros.",
                "Ajuste os campos de busca para carregar registros.",
                icon="search_off",
            )
            return

        df = pd.DataFrame(
            [
                {
                    "id": c["id"],
                    "Número": c["contract_number"],
                    "Título": c["title"],
                    "Tipo": c["type"],
                    "Status": c["status"],
                    "Departamento": c["department"],
                    "Contratado": c.get("contracted", {}).get("name", "N/A"),
                    "Valor": brl(c["contract_value"]),
                    "Início": c["start_date"],
                    "Fim": c["end_date"],
                    "Versão": c.get("version", 1),
                }
                for c in contracts
            ]
        )
        st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)

        render_panel_header("Ações por Contrato", "Execute download, edição, aditivos e finalização no mesmo fluxo.", icon="edit_square")
        contract_map = {c["id"]: c for c in contracts}
        selected_contract_id = st.selectbox(
            "Selecione um contrato",
            options=list(contract_map.keys()),
            format_func=lambda cid: f"{contract_map[cid]['contract_number']} | {contract_map[cid]['title']} | {contract_map[cid]['status']}",
        )
        c = contract_map[selected_contract_id]

        st.write(f"**Status:** {c['status']}  |  **Versão:** {c.get('version', 1)}")
        st.write(f"**Escopo:** {c.get('scope_text') or 'Não informado'}")
        st.write(f"**Cláusulas (prévia):** {(c.get('clauses_text') or 'Não informado')[:500]}")

        admin_override = st.checkbox("Admin override (permitir pular status)", value=False)

        pdf_bytes = download_pdf_bytes(c["id"])
        if pdf_bytes:
            st.download_button(
                "Baixar PDF",
                data=pdf_bytes,
                file_name=f"{c['contract_number']}.pdf",
                mime="application/pdf",
                key=f"download_{c['id']}",
            )
        else:
            st.info("PDF ainda não gerado para este contrato.")

        if st.button("Regerar PDF", key=f"regen_pdf_{c['id']}"):
            generate_and_attach_pdf(c["id"])
            st.success("PDF regerado e evento registrado.")
            st.rerun()

        st.markdown("**Editar (versionamento simples)**")
        e1, e2, e3 = st.columns(3)
        new_title = e1.text_input("Título", value=c["title"], key=f"title_{c['id']}")
        new_dept = e2.text_input("Departamento", value=c["department"], key=f"dept_{c['id']}")
        new_value = e3.number_input("Valor", min_value=0.0, value=float(c["contract_value"]), key=f"value_{c['id']}")
        new_scope = st.text_area("Escopo", value=c.get("scope_text", ""), key=f"scope_{c['id']}")
        new_clauses = st.text_area("Cláusulas", value=c.get("clauses_text", ""), key=f"clauses_{c['id']}")

        if st.button("Salvar edição", key=f"edit_{c['id']}"):
            edit_contract(
                c["id"],
                {
                    "title": new_title,
                    "department": new_dept,
                    "contract_value": new_value,
                    "scope_text": new_scope,
                    "clauses_text": new_clauses,
                },
            )
            st.success("Contrato atualizado com versionamento e evento de auditoria.")
            st.rerun()

        st.markdown("**Registrar aditivo/ocorrência**")
        a1, a2, a3 = st.columns(3)
        add_date = a1.date_input("Data aditivo", key=f"add_date_{c['id']}", value=date.today())
        add_value = a2.number_input("Valor aditivo", min_value=0.0, value=0.0, key=f"add_value_{c['id']}")
        add_reason = a3.text_input("Motivo", key=f"add_reason_{c['id']}")
        occurrence = st.text_area("Ocorrência", key=f"occ_{c['id']}")
        if st.button("Registrar", key=f"register_{c['id']}"):
            if add_value > 0 and add_reason:
                add_additive(c["id"], str(add_date), add_value, add_reason)
            if occurrence.strip():
                add_event(c["id"], "ocorrencia", {"text": occurrence.strip()})
            st.success("Registro salvo.")
            st.rerun()

        if c["status"] != "Finalizado":
            if st.button("Finalizar", key=f"finalize_{c['id']}"):
                try:
                    update_status(c["id"], "Finalizado", user="ui", admin_override=admin_override)
                    st.success("Contrato finalizado.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
