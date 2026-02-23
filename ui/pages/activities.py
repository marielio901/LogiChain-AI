from datetime import date

import streamlit as st

from services import (
    list_contracts,
    get_contract_by_id,
    add_additive,
    add_event,
    upsert_compliance,
    upsert_supplier_performance,
    update_contract_activity,
)
from ui.theme import render_empty_state, render_page_header, render_panel_header


def _contract_label(c: dict) -> str:
    return f"{c['contract_number']} | {c['title']} | {c['status']}"


def render_activities_page():
    render_page_header(
        "Registrar Atividades",
        "Selecione um contrato e registre eventos para retroalimentar KPIs e modelos analíticos.",
        badge="Data Feeder",
    )

    contracts = list_contracts(filters={"order_by": "created_at DESC"}, include_finalized=True)
    if not contracts:
        render_empty_state(
            "Nenhum contrato cadastrado.",
            "Crie pelo menos um contrato para iniciar o registro de atividades.",
            icon="data_table",
        )
        return

    options = {c["id"]: c for c in contracts}
    selected_id = st.selectbox("Contrato", options=list(options.keys()), format_func=lambda cid: _contract_label(options[cid]))
    contract = get_contract_by_id(selected_id)
    if not contract:
        st.error("Contrato não encontrado.")
        return

    render_panel_header(
        "Contexto do contrato selecionado",
        f"{contract['contract_number']} · status atual: {contract['status']}",
        icon="fact_check",
    )

    tabs = st.tabs(
        [
            "Financeiro e Execução",
            "Compliance e Risco",
            "Desempenho Fornecedor",
            "Jurídico / CLM / Estratégico",
            "Aditivo / Ocorrência",
        ]
    )

    with tabs[0]:
        st.subheader("Atualizar execução financeira")
        c1, c2, c3 = st.columns(3)
        executed_value = c1.number_input("Valor executado (R$)", min_value=0.0, value=float(contract.get("executed_value") or 0.0))
        savings_value = c2.number_input("Saving (R$)", min_value=0.0, value=float(contract.get("savings_value") or 0.0))
        roi_value = c3.number_input("ROI (%)", min_value=0.0, value=float(contract.get("roi_value") or 0.0))

        if st.button("Salvar financeiro", use_container_width=True):
            update_contract_activity(
                selected_id,
                {
                    "executed_value": executed_value,
                    "savings_value": savings_value,
                    "roi_value": roi_value,
                },
                event_type="finance_update",
            )
            st.success("Dados financeiros atualizados.")
            st.rerun()

    with tabs[1]:
        st.subheader("Registrar compliance")
        c1, c2, c3 = st.columns(3)
        mandatory_score = c1.slider("Score cláusulas obrigatórias (%)", 0, 100, 100)
        reg_pct = c2.slider("Conformidade regulatória (%)", 0, 100, 100)
        risk_score = c3.slider("Score de risco", 0, 100, 35)

        c4, c5, c6 = st.columns(3)
        out_of_standard = c4.checkbox("Fora do padrão jurídico")
        has_guarantee = c5.checkbox("Possui garantia")
        has_insurance = c6.checkbox("Possui seguro")
        c7, c8 = st.columns(2)
        audited = c7.checkbox("Auditado")
        nonconf = c8.number_input("Não conformidades", min_value=0, value=0)

        if st.button("Salvar compliance", use_container_width=True):
            upsert_compliance(
                selected_id,
                {
                    "mandatory_clauses_score": mandatory_score,
                    "out_of_standard": out_of_standard,
                    "has_guarantee": has_guarantee,
                    "has_insurance": has_insurance,
                    "regulatory_compliance_pct": reg_pct,
                    "audited": audited,
                    "nonconformities_count": nonconf,
                    "risk_score": risk_score,
                },
            )
            add_event(selected_id, "compliance_update", {"risk_score": risk_score, "out_of_standard": out_of_standard})
            st.success("Compliance atualizado.")
            st.rerun()

    with tabs[2]:
        st.subheader("Registrar desempenho do fornecedor")
        c1, c2, c3 = st.columns(3)
        sla_pct = c1.number_input("SLA cumprido (%)", min_value=0.0, max_value=100.0, value=95.0)
        fail_rate = c2.number_input("Falhas na entrega (%)", min_value=0.0, max_value=100.0, value=5.0)
        on_time_pct = c3.number_input("Pontualidade (%)", min_value=0.0, max_value=100.0, value=95.0)
        c4, c5, c6 = st.columns(3)
        quality = c4.number_input("Qualidade (0-100)", min_value=0.0, max_value=100.0, value=90.0)
        switch_rate = c5.number_input("Troca de fornecedor (%)", min_value=0.0, max_value=100.0, value=0.0)
        satisfaction = c6.number_input("Satisfação (0-100)", min_value=0.0, max_value=100.0, value=90.0)

        if st.button("Salvar fornecedor", use_container_width=True):
            upsert_supplier_performance(
                selected_id,
                {
                    "sla_pct": sla_pct,
                    "delivery_fail_rate": fail_rate,
                    "on_time_pct": on_time_pct,
                    "quality_score": quality,
                    "supplier_switch_rate": switch_rate,
                    "satisfaction_score": satisfaction,
                },
            )
            add_event(selected_id, "supplier_performance_update", {"sla_pct": sla_pct, "on_time_pct": on_time_pct})
            st.success("Desempenho do fornecedor atualizado.")
            st.rerun()

    with tabs[3]:
        st.subheader("Jurídico / CLM / Estratégico / Avançados")
        legal_notes = st.text_area("Observações jurídicas", value=contract.get("legal_notes") or "")

        c1, c2, c3 = st.columns(3)
        signed_date = c1.date_input("Data de assinatura", value=date.fromisoformat(contract["signed_date"]) if contract.get("signed_date") else date.today())
        archived_date = c2.date_input("Data de arquivamento", value=date.fromisoformat(contract["archived_date"]) if contract.get("archived_date") else date.today())
        request_date = c3.date_input("Data do pedido", value=date.fromisoformat(contract["request_date"]) if contract.get("request_date") else date.today())

        c4, c5, c6 = st.columns(3)
        digitally_signed = c4.checkbox("Assinado digitalmente", value=bool(contract.get("digitally_signed")))
        strategic_alignment = c5.checkbox("Alinhado ao planejamento", value=bool(contract.get("strategic_alignment")))
        operation_critical = c6.checkbox("Crítico para operação", value=bool(contract.get("operation_critical")))

        c7, c8, c9 = st.columns(3)
        supplier_key_dependency = c7.checkbox("Dependência de fornecedor-chave", value=bool(contract.get("supplier_key_dependency")))
        revenue_contribution = c8.number_input("Contribuição para receita (R$)", min_value=0.0, value=float(contract.get("revenue_contribution") or 0.0))
        supplier_diversification = c9.number_input("Diversificação fornecedores (0-100)", min_value=0.0, max_value=100.0, value=float(contract.get("supplier_diversification_score") or 0.0))

        c10, c11, c12 = st.columns(3)
        maturity = c10.number_input("Maturidade contratual (0-100)", min_value=0.0, max_value=100.0, value=float(contract.get("maturity_score") or 0.0))
        governance = c11.number_input("Governança (0-100)", min_value=0.0, max_value=100.0, value=float(contract.get("governance_index") or 0.0))
        automation = c12.number_input("Automação (%)", min_value=0.0, max_value=100.0, value=float(contract.get("automation_pct") or 0.0))

        c13, c14, c15 = st.columns(3)
        default_probability = c13.number_input("Prob. inadimplência (%)", min_value=0.0, max_value=100.0, value=float(contract.get("default_probability") or 0.0))
        aggregate_risk = c14.number_input("Risco financeiro agregado (R$)", min_value=0.0, value=float(contract.get("aggregate_financial_risk") or 0.0))
        disruption = c15.number_input("Ruptura baseline (0-100)", min_value=0.0, max_value=100.0, value=float(contract.get("disruption_predictive_score") or 0.0))

        if st.button("Salvar atividade estratégica", use_container_width=True):
            update_contract_activity(
                selected_id,
                {
                    "legal_notes": legal_notes,
                    "signed_date": str(signed_date),
                    "archived_date": str(archived_date),
                    "request_date": str(request_date),
                    "digitally_signed": int(digitally_signed),
                    "strategic_alignment": int(strategic_alignment),
                    "operation_critical": int(operation_critical),
                    "supplier_key_dependency": int(supplier_key_dependency),
                    "revenue_contribution": revenue_contribution,
                    "supplier_diversification_score": supplier_diversification,
                    "maturity_score": maturity,
                    "governance_index": governance,
                    "automation_pct": automation,
                    "default_probability": default_probability,
                    "aggregate_financial_risk": aggregate_risk,
                    "disruption_predictive_score": disruption,
                },
                event_type="strategic_update",
            )
            st.success("Atividades estratégicas/jurídicas/CLM atualizadas.")
            st.rerun()

    with tabs[4]:
        st.subheader("Registrar aditivo financeiro")
        c1, c2, c3 = st.columns(3)
        add_date = c1.date_input("Data do aditivo", value=date.today(), key=f"add_date_{selected_id}")
        add_value = c2.number_input("Valor do aditivo", min_value=0.0, value=0.0, key=f"add_value_{selected_id}")
        add_reason = c3.text_input("Motivo", key=f"add_reason_{selected_id}")

        if st.button("Salvar aditivo", use_container_width=True):
            if add_value <= 0 or not add_reason.strip():
                st.error("Informe valor > 0 e motivo.")
            else:
                add_additive(selected_id, str(add_date), add_value, add_reason.strip())
                st.success("Aditivo registrado.")
                st.rerun()

        st.divider()
        st.subheader("Registrar ocorrência")
        occurrence = st.text_area("Descrição da ocorrência")
        if st.button("Salvar ocorrência", use_container_width=True):
            if not occurrence.strip():
                st.error("Descreva a ocorrência.")
            else:
                add_event(selected_id, "ocorrencia", {"text": occurrence.strip()})
                st.success("Ocorrência registrada.")
                st.rerun()
