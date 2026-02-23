from datetime import date

import streamlit as st

from services import next_contract_number, create_contract, generate_and_attach_pdf, download_pdf_bytes
from ui.theme import render_page_header, render_panel_header
from utils import validate_required_fields


CONTRACT_TYPES = ["Prestação de Serviço", "Fornecimento de Materiais", "Alocação"]
MANDATORY_CLAUSES = [
    "Objeto do contrato",
    "Prazo e vigência",
    "Condições de pagamento",
    "Penalidades",
    "Rescisão",
    "Compliance e LGPD",
]


def _parse_lines(lines: str, separator: str = "|"):
    parsed = []
    for line in (lines or "").splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(separator)]
        parsed.append(parts)
    return parsed


def render_new_contract_page():
    render_page_header(
        "Novo Contrato",
        "Preencha os dados para gerar um contrato completo com versionamento e PDF vinculado.",
        badge="Contract Builder",
    )
    render_panel_header(
        "Fluxo de cadastro",
        "Preencha as abas em sequência para reduzir retrabalho e validações pendentes.",
        icon="playlist_add_check",
    )

    contract_number = next_contract_number()

    with st.form("new_contract_form", clear_on_submit=False):
        tab_a, tab_b, tab_c, tab_d, tab_e, tab_f, tab_g, tab_h = st.tabs(
            [
                "A) Identificação",
                "B) Contratante",
                "C) Contratado",
                "D) Escopo",
                "E) Cláusulas",
                "F) Financeiro",
                "G) Datas",
                "H) Assinaturas",
            ]
        )

        with tab_a:
            st.text_input("Número do contrato", value=contract_number, disabled=True)
            c1, c2 = st.columns(2)
            contract_type = c1.selectbox("Tipo de contrato", CONTRACT_TYPES)
            title = c2.text_input("Título/objeto curto")
            c3, c4 = st.columns(2)
            department = c3.text_input("Área/departamento")
            cost_center = c4.text_input("Centro de custo (opcional)")
            tags = st.text_input("Tags (separadas por vírgula)")

        with tab_b:
            st.subheader("Dados do Contratante")
            contractor_name = st.text_input("Razão social / Nome (Contratante)")
            contractor_doc = st.text_input("CNPJ/CPF (Contratante)")
            contractor_address = st.text_area("Endereço completo (Contratante)")
            c1, c2, c3 = st.columns(3)
            contractor_rep_name = c1.text_input("Representante legal - Nome (Contratante)")
            contractor_rep_role = c2.text_input("Representante legal - Cargo (Contratante)")
            contractor_rep_doc = c3.text_input("Representante legal - Documento (Contratante)")
            c4, c5 = st.columns(2)
            contractor_email = c4.text_input("Email (Contratante)")
            contractor_phone = c5.text_input("Telefone (Contratante)")

        with tab_c:
            st.subheader("Dados do Contratado")
            contracted_name = st.text_input("Razão social / Nome (Contratado)")
            contracted_doc = st.text_input("CNPJ/CPF (Contratado)")
            contracted_address = st.text_area("Endereço completo (Contratado)")
            c1, c2, c3 = st.columns(3)
            contracted_rep_name = c1.text_input("Representante legal - Nome (Contratado)")
            contracted_rep_role = c2.text_input("Representante legal - Cargo (Contratado)")
            contracted_rep_doc = c3.text_input("Representante legal - Documento (Contratado)")
            c4, c5 = st.columns(2)
            contracted_email = c4.text_input("Email (Contratado)")
            contracted_phone = c5.text_input("Telefone (Contratado)")

        with tab_d:
            scope_text = st.text_area("Descrição detalhada")
            deliverables_text = st.text_area("Entregáveis")
            c1, c2 = st.columns(2)
            sla_pct = c1.number_input("SLA meta (%)", min_value=0.0, max_value=100.0, value=95.0)
            on_time_target = c2.number_input("Pontualidade meta (%)", min_value=0.0, max_value=100.0, value=95.0)
            acceptance_rules_text = st.text_area("Regras de aceite")

        with tab_e:
            clauses_text = st.text_area("Cláusulas (editor)", height=180)
            critical_clauses = st.checkbox("Possui cláusulas críticas?")
            critical_clauses_text = st.text_area("Detalhes das cláusulas críticas")
            mandatory_clauses = st.multiselect(
                "Cláusulas obrigatórias presentes",
                options=MANDATORY_CLAUSES,
                default=MANDATORY_CLAUSES,
            )
            legal_notes = st.text_area("Observações jurídicas")

        with tab_f:
            contract_value = st.number_input("Valor contratado (R$)", min_value=0.0, value=0.0, step=1000.0)
            payment_terms = st.text_area("Forma de pagamento")
            reajust_index = st.text_input("Índice de reajuste (opcional)")
            penalties_text = st.text_area("Multas previstas")
            penalties_value = st.number_input("Valor de multas (opcional)", min_value=0.0, value=0.0)

        with tab_g:
            c1, c2 = st.columns(2)
            start_date = c1.date_input("Data inicial (vigência)", value=date.today())
            end_date = c2.date_input("Data final (vigência)", value=date.today())
            request_date = st.date_input("Data do pedido/solicitação", value=date.today())
            has_signed_date = st.checkbox("Informar data de assinatura agora?")
            signed_date = st.date_input("Data de assinatura", value=date.today(), disabled=not has_signed_date)
            st.caption("Marcos importantes (um por linha: YYYY-MM-DD|descrição)")
            milestones_lines = st.text_area("Marcos")

        with tab_h:
            c1, c2 = st.columns(2)
            contractor_sign = c1.text_input("Assinatura Contratante (nome + local)")
            contracted_sign = c2.text_input("Assinatura Contratado (nome + local)")
            witnesses = st.text_input("Testemunhas (opcional)")
            st.file_uploader("Upload assinatura (Contratante) - opcional", type=["png", "jpg", "jpeg"])
            st.file_uploader("Upload assinatura (Contratado) - opcional", type=["png", "jpg", "jpeg"])

        submit = st.form_submit_button("Gerar Contrato (PDF)", use_container_width=True)

    if submit:
        payload = {
            "contract_number": contract_number,
            "type": contract_type,
            "title": title,
            "department": department,
            "cost_center": cost_center,
            "status": "Gerado",
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "contractor": {
                "name": contractor_name,
                "doc": contractor_doc,
                "address": contractor_address,
                "representative": {
                    "name": contractor_rep_name,
                    "role": contractor_rep_role,
                    "doc": contractor_rep_doc,
                },
                "email": contractor_email,
                "phone": contractor_phone,
            },
            "contracted": {
                "name": contracted_name,
                "doc": contracted_doc,
                "address": contracted_address,
                "representative": {
                    "name": contracted_rep_name,
                    "role": contracted_rep_role,
                    "doc": contracted_rep_doc,
                },
                "email": contracted_email,
                "phone": contracted_phone,
            },
            "scope_text": scope_text,
            "deliverables_text": deliverables_text,
            "sla_targets": {"sla_pct": sla_pct, "on_time_target": on_time_target},
            "acceptance_rules_text": acceptance_rules_text,
            "clauses_text": clauses_text,
            "critical_clauses": critical_clauses,
            "critical_clauses_text": critical_clauses_text,
            "mandatory_clauses": mandatory_clauses,
            "legal_notes": legal_notes,
            "contract_value": contract_value,
            "payment_terms": payment_terms,
            "reajust_index": reajust_index,
            "penalties_text": penalties_text,
            "penalties_value": penalties_value,
            "start_date": start_date,
            "end_date": end_date,
            "milestones": [
                {"date": p[0], "description": p[1] if len(p) > 1 else ""}
                for p in _parse_lines(milestones_lines)
            ],
            "request_date": str(request_date) if request_date else None,
            "signed_date": str(signed_date) if has_signed_date else None,
            "signatures": {
                "contractor_sign": contractor_sign,
                "contracted_sign": contracted_sign,
                "witnesses": witnesses,
            },
        }

        errors = validate_required_fields(payload)
        if errors:
            for err in errors:
                st.error(err)
            st.stop()

        contract_id = create_contract(payload)
        pdf_path = generate_and_attach_pdf(contract_id)
        pdf_bytes = download_pdf_bytes(contract_id)

        st.success(f"Contrato {contract_number} criado com sucesso. PDF: {pdf_path}")
        if pdf_bytes:
            st.download_button(
                "Baixar PDF",
                data=pdf_bytes,
                file_name=f"{contract_number}.pdf",
                mime="application/pdf",
            )
