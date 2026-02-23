from datetime import date

import pandas as pd

from db.connection import get_connection


def _fetch_df(query: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def load_base_data():
    contracts = _fetch_df("SELECT * FROM contracts")
    additives = _fetch_df("SELECT * FROM contract_additives")
    compliance = _fetch_df("SELECT * FROM compliance_checks")
    supplier = _fetch_df("SELECT * FROM supplier_performance")
    events = _fetch_df("SELECT * FROM contract_events")
    return contracts, additives, compliance, supplier, events


def _pct(numerator, denominator):
    if denominator in (0, None):
        return None
    return (numerator / denominator) * 100


def calculate_kpis(expiring_days: int = 30, contract_ids: list[int] | None = None):
    contracts, additives, compliance, supplier, events = load_base_data()
    if contract_ids is not None:
        ids_set = set(contract_ids)
        contracts = contracts[contracts["id"].isin(ids_set)] if not contracts.empty else contracts
        additives = additives[additives["contract_id"].isin(ids_set)] if not additives.empty else additives
        compliance = compliance[compliance["contract_id"].isin(ids_set)] if not compliance.empty else compliance
        supplier = supplier[supplier["contract_id"].isin(ids_set)] if not supplier.empty else supplier
        events = events[events["contract_id"].isin(ids_set)] if not events.empty else events

    if contracts.empty:
        return {"has_data": False, "sections": {}, "charts": {}}

    contracts["start_date"] = pd.to_datetime(contracts["start_date"], errors="coerce")
    contracts["end_date"] = pd.to_datetime(contracts["end_date"], errors="coerce")
    contracts["created_at"] = pd.to_datetime(contracts["created_at"], errors="coerce")
    today = pd.Timestamp(date.today())

    total_value = float(contracts["contract_value"].fillna(0).sum())
    executed_total = float(contracts["executed_value"].fillna(0).sum())
    savings_total = float(contracts["savings_value"].fillna(0).sum())
    multas_total = float(contracts["penalties_value"].fillna(0).sum())
    aditivos_total = float(additives["additive_value"].fillna(0).sum()) if not additives.empty else 0.0

    avg_contract_value = float(contracts["contract_value"].fillna(0).mean()) if len(contracts) else None
    price_variation = _pct(aditivos_total, total_value)
    roi_mean = float(contracts["roi_value"].fillna(0).mean()) if len(contracts) else None

    active_contracts = contracts[contracts["status"].isin(["Assinado", "Protocolado", "Em vigor"])]
    duration_days = (contracts["end_date"] - contracts["start_date"]).dt.days
    avg_term = float(duration_days.dropna().mean()) if duration_days.notna().any() else None
    expiring = contracts[(contracts["end_date"] >= today) & (contracts["end_date"] <= today + pd.Timedelta(days=expiring_days))]
    expiring_pct = _pct(len(expiring), len(contracts))
    expired_no_renew = contracts[(contracts["end_date"] < today) & (contracts["status"] != "Finalizado")]

    signed = contracts[contracts["signed_date"].notna()].copy()
    signed["signed_date"] = pd.to_datetime(signed["signed_date"], errors="coerce")
    lead_days = (signed["signed_date"] - signed["created_at"]).dt.days
    lead_time = float(lead_days.dropna().mean()) if lead_days.notna().any() else None

    renewal_rate = _pct(len(contracts[contracts["status"] == "Finalizado"]), len(contracts))

    if not compliance.empty:
        mandatory_score = float(compliance["mandatory_clauses_score"].fillna(0).mean())
        out_standard = int(compliance["out_of_standard"].fillna(0).sum())
        guarantee_missing = int((compliance["has_guarantee"].fillna(0) == 0).sum())
        risk_idx = float(compliance["risk_score"].fillna(0).mean())
        reg_compliance = float(compliance["regulatory_compliance_pct"].fillna(0).mean())
        audited_pct = _pct(int(compliance["audited"].fillna(0).sum()), len(compliance))
        nonconf = int(compliance["nonconformities_count"].fillna(0).sum())
    else:
        mandatory_score = out_standard = guarantee_missing = risk_idx = reg_compliance = audited_pct = nonconf = None

    add_freq = float(additives.groupby("contract_id").size().mean()) if not additives.empty else None

    if not supplier.empty:
        sla = float(supplier["sla_pct"].fillna(0).mean())
        delivery_fail = float(supplier["delivery_fail_rate"].fillna(0).mean())
        on_time = float(supplier["on_time_pct"].fillna(0).mean())
        quality = float(supplier["quality_score"].fillna(0).mean())
        switch_rate = float(supplier["supplier_switch_rate"].fillna(0).mean())
        satisfaction = float(supplier["satisfaction_score"].fillna(0).mean())
    else:
        sla = delivery_fail = on_time = quality = switch_rate = satisfaction = None

    litigation = int((contracts.get("legal_notes", pd.Series([], dtype="string")).fillna("").str.contains("litígio|litigio", case=False, regex=True)).sum())
    critical_clauses = int(contracts["critical_clauses"].fillna(0).sum())

    archived = contracts[contracts["archived_date"].notna()].copy()
    archived["archived_date"] = pd.to_datetime(archived["archived_date"], errors="coerce")
    archive_time = (archived["archived_date"] - archived["created_at"]).dt.days
    avg_archive = float(archive_time.dropna().mean()) if archive_time.notna().any() else None

    created_to_signed = lead_time
    signed_time = lead_time
    digital_signed_pct = _pct(int(contracts["digitally_signed"].fillna(0).sum()), len(contracts))

    strategic = _pct(int(contracts["strategic_alignment"].fillna(0).sum()), len(contracts))
    rev_contrib = float(contracts["revenue_contribution"].fillna(0).sum())
    operation_critical = _pct(int(contracts["operation_critical"].fillna(0).sum()), len(contracts))
    key_dependency = float(contracts["supplier_key_dependency"].fillna(0).mean() * 100)
    diversification = float(contracts["supplier_diversification_score"].fillna(0).mean())

    maturity = float(contracts["maturity_score"].fillna(0).mean())
    governance = float(contracts["governance_index"].fillna(0).mean())
    automation = float(contracts["automation_pct"].fillna(0).mean())
    default_prob = float(contracts["default_probability"].fillna(0).mean())
    agg_risk = float(contracts["aggregate_financial_risk"].fillna(0).sum())
    disruption = float(contracts["disruption_predictive_score"].fillna(0).mean())

    sections = {
        "financeiro": {
            "valor_total_contratado": total_value,
            "executado_vs_contratado_pct": _pct(executed_total, total_value),
            "economia_obtida": savings_total,
            "custo_medio_contrato": avg_contract_value,
            "multas_total": multas_total,
            "custos_adicionais_aditivos": aditivos_total,
            "variacao_preco_pct": price_variation,
            "roi_medio": roi_mean,
        },
        "prazo_execucao": {
            "prazo_medio_vigencia_dias": avg_term,
            "pct_proximos_vencimento": expiring_pct,
            "atraso_medio_execucao_dias": None,
            "lead_time_contratacao_dias": lead_time,
            "taxa_renovacao": renewal_rate,
            "vencidos_sem_renovacao": len(expired_no_renew),
            "cumprimento_cronograma_pct": None,
        },
        "compliance_risco": {
            "pct_clausulas_obrigatorias": mandatory_score,
            "fora_padrao_juridico": out_standard,
            "sem_garantia_ou_seguro": guarantee_missing,
            "indice_risco": risk_idx,
            "conformidade_regulatoria_pct": reg_compliance,
            "auditados_pct": audited_pct,
            "nao_conformidades": nonconf,
        },
        "operacionais": {
            "total_ativos": len(active_contracts),
            "contratos_por_tipo": contracts["type"].value_counts().to_dict(),
            "contratos_por_fornecedor": contracts["contracted_json"].fillna("").str.extract(r'"name"\s*:\s*"([^"]+)"')[0].fillna("N/A").value_counts().to_dict(),
            "contratos_por_departamento": contracts["department"].value_counts().to_dict(),
            "volume_aditivos_medio": add_freq,
            "frequencia_alteracoes": int((events["event_type"] == "edit").sum()) if not events.empty else 0,
            "digitalizados_vs_fisicos_pct": digital_signed_pct,
        },
        "fornecedor": {
            "sla_cumprido_pct": sla,
            "indice_falhas_entrega": delivery_fail,
            "pontualidade_entrega": on_time,
            "qualidade_servico": quality,
            "taxa_substituicao_fornecedor": switch_rate,
            "satisfacao_fornecedor": satisfaction,
        },
        "juridicos": {
            "litigios_relacionados": litigation,
            "com_clausulas_criticas": critical_clauses,
            "tempo_medio_analise_juridica": None,
            "tempo_medio_aprovacao": None,
            "rescindidos_antecipadamente": 0,
            "exposicao_juridica_estimada": agg_risk,
        },
        "clm": {
            "tempo_criacao_aprovacao_assinatura": created_to_signed,
            "tempo_medio_assinatura": signed_time,
            "pct_assinados_digitalmente": digital_signed_pct,
            "tempo_medio_arquivamento": avg_archive,
            "tempo_renegociacao": None,
            "eficiencia_fluxo_aprovacao": automation,
        },
        "estrategicos": {
            "pct_alinhados_planejamento": strategic,
            "contribuicao_receita": rev_contrib,
            "contratos_criticos_operacao": operation_critical,
            "dependencia_fornecedores_chave": key_dependency,
            "diversificacao_fornecedores": diversification,
        },
        "avancados": {
            "score_maturidade": maturity,
            "indice_governanca": governance,
            "pct_automacao": automation,
            "prob_inadimplencia": default_prob,
            "risco_financeiro_agregado": agg_risk,
            "ruptura_preditiva_baseline": disruption,
        },
    }

    charts = {
        "status_dist": contracts["status"].value_counts().to_dict(),
        "tipo_dist": contracts["type"].value_counts().to_dict(),
        "valor_por_departamento": contracts.groupby("department")["contract_value"].sum().to_dict(),
    }
    return {"has_data": True, "sections": sections, "charts": charts}
