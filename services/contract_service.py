from datetime import datetime
from pathlib import Path

from db.connection import get_connection
from services.pdf_service import generate_contract_pdf
from utils import dumps, loads, now_iso, can_transition


def next_contract_number() -> str:
    year = datetime.now().year
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS total FROM contracts WHERE contract_number LIKE ?",
        (f"LC-{year}-%",),
    ).fetchone()
    conn.close()
    seq = (row["total"] or 0) + 1
    return f"LC-{year}-{seq:03d}"


def _row_to_contract(row):
    if row is None:
        return None
    data = dict(row)
    data["contractor"] = loads(data.pop("contractor_json"), {})
    data["contracted"] = loads(data.pop("contracted_json"), {})
    data["sla_targets"] = loads(data.pop("sla_targets_json"), {})
    data["mandatory_clauses"] = loads(data.pop("mandatory_clauses_json"), [])
    data["milestones"] = loads(data.pop("milestones_json"), [])
    data["signatures"] = loads(data.pop("signatures_json"), {})
    data["tags"] = loads(data.get("tags"), [])
    return data


def create_contract(payload: dict) -> int:
    now = now_iso()
    payload.setdefault("status", "Gerado")
    payload.setdefault("version", 1)

    conn = get_connection()
    with conn:
        cur = conn.execute(
            """
            INSERT INTO contracts (
                contract_number, type, title, department, cost_center, status, tags,
                contractor_json, contracted_json, scope_text, deliverables_text,
                sla_targets_json, acceptance_rules_text, clauses_text,
                critical_clauses, critical_clauses_text, mandatory_clauses_json,
                legal_notes, start_date, end_date, milestones_json, payment_terms,
                reajust_index, penalties_text, penalties_value, signatures_json,
                contract_value, executed_value, savings_value, roi_value,
                request_date, signed_date, archived_date, digitally_signed,
                strategic_alignment, revenue_contribution, operation_critical,
                supplier_key_dependency, supplier_diversification_score,
                maturity_score, governance_index, automation_pct,
                default_probability, aggregate_financial_risk,
                disruption_predictive_score, created_at, updated_at,
                is_archived, is_finalized, version
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?, ?, ?
            )
            """,
            (
                payload["contract_number"], payload["type"], payload["title"], payload["department"],
                payload.get("cost_center"), payload["status"], dumps(payload.get("tags", [])),
                dumps(payload.get("contractor")), dumps(payload.get("contracted")), payload.get("scope_text", ""), payload.get("deliverables_text", ""),
                dumps(payload.get("sla_targets", {})), payload.get("acceptance_rules_text", ""), payload.get("clauses_text", ""),
                int(bool(payload.get("critical_clauses", False))), payload.get("critical_clauses_text", ""), dumps(payload.get("mandatory_clauses", [])),
                payload.get("legal_notes", ""), str(payload["start_date"]), str(payload["end_date"]), dumps(payload.get("milestones", [])), payload.get("payment_terms", ""),
                payload.get("reajust_index", ""), payload.get("penalties_text", ""), float(payload.get("penalties_value", 0) or 0), dumps(payload.get("signatures", {})),
                float(payload.get("contract_value", 0) or 0), float(payload.get("executed_value", 0) or 0), float(payload.get("savings_value", 0) or 0), float(payload.get("roi_value", 0) or 0),
                payload.get("request_date"), payload.get("signed_date"), payload.get("archived_date"), int(bool(payload.get("digitally_signed", False))),
                int(bool(payload.get("strategic_alignment", False))), float(payload.get("revenue_contribution", 0) or 0), int(bool(payload.get("operation_critical", False))),
                int(bool(payload.get("supplier_key_dependency", False))), float(payload.get("supplier_diversification_score", 0) or 0),
                float(payload.get("maturity_score", 0) or 0), float(payload.get("governance_index", 0) or 0), float(payload.get("automation_pct", 0) or 0),
                float(payload.get("default_probability", 0) or 0), float(payload.get("aggregate_financial_risk", 0) or 0),
                float(payload.get("disruption_predictive_score", 0) or 0), now, now,
                0, int(payload["status"] == "Finalizado"), payload.get("version", 1)
            ),
        )
        contract_id = cur.lastrowid
    conn.close()
    add_event(contract_id, "created", {"status": "Gerado"})
    return contract_id


def add_event(contract_id: int, event_type: str, event_data: dict | None = None) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO contract_events (contract_id, event_type, event_data_json, created_at) VALUES (?, ?, ?, ?)",
            (contract_id, event_type, dumps(event_data or {}), now_iso()),
        )
    conn.close()


def generate_and_attach_pdf(contract_id: int) -> str:
    contract = get_contract_by_id(contract_id)
    if not contract:
        raise ValueError("Contrato não encontrado")
    file_path = generate_contract_pdf(contract)
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE contracts SET pdf_path = ?, updated_at = ? WHERE id = ?",
            (file_path, now_iso(), contract_id),
        )
    conn.close()
    add_event(contract_id, "pdf_generated", {"pdf_path": file_path, "version": contract.get("version", 1)})
    return file_path


def get_contract_by_id(contract_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
    conn.close()
    return _row_to_contract(row)


def get_contract_by_number(contract_number: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM contracts WHERE contract_number = ?", (contract_number,)).fetchone()
    conn.close()
    return _row_to_contract(row)


def list_contracts(filters: dict | None = None, include_finalized: bool = True):
    filters = filters or {}
    where = ["1=1"]
    params = []

    mapping = {
        "type": "type = ?",
        "status": "status = ?",
        "department": "department = ?",
    }
    for k, clause in mapping.items():
        if filters.get(k):
            where.append(clause)
            params.append(filters[k])

    if filters.get("contracted"):
        where.append("contracted_json LIKE ?")
        params.append(f"%{filters['contracted']}%")

    if filters.get("min_value") is not None:
        where.append("contract_value >= ?")
        params.append(float(filters["min_value"]))

    if filters.get("max_value") is not None:
        where.append("contract_value <= ?")
        params.append(float(filters["max_value"]))

    if filters.get("date_from"):
        where.append("date(created_at) >= date(?)")
        params.append(str(filters["date_from"]))

    if filters.get("date_to"):
        where.append("date(created_at) <= date(?)")
        params.append(str(filters["date_to"]))

    if not include_finalized:
        where.append("status <> 'Finalizado'")

    order_by = filters.get("order_by", "created_at DESC")
    allowed_order = {
        "created_at DESC": "created_at DESC",
        "created_at ASC": "created_at ASC",
        "end_date ASC": "end_date ASC",
        "contract_value DESC": "contract_value DESC",
        "status ASC": "status ASC",
    }
    order_clause = allowed_order.get(order_by, "created_at DESC")

    query = f"SELECT * FROM contracts WHERE {' AND '.join(where)} ORDER BY {order_clause}"

    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_contract(r) for r in rows]


def list_kanban_contracts():
    return list_contracts(filters={"order_by": "created_at DESC"}, include_finalized=False)


def update_status(contract_id: int, new_status: str, user: str = "system", admin_override: bool = False) -> None:
    contract = get_contract_by_id(contract_id)
    if not contract:
        raise ValueError("Contrato não encontrado")

    if not can_transition(contract["status"], new_status, admin_override=admin_override):
        raise ValueError("Transição de status inválida.")

    is_finalized = int(new_status == "Finalizado")
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE contracts SET status = ?, is_finalized = ?, updated_at = ? WHERE id = ?",
            (new_status, is_finalized, now_iso(), contract_id),
        )
    conn.close()
    add_event(
        contract_id,
        "status_change",
        {"from": contract["status"], "to": new_status, "user": user, "admin_override": admin_override},
    )


def add_additive(contract_id: int, additive_date: str, additive_value: float, reason: str) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO contract_additives (contract_id, additive_date, additive_value, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (contract_id, additive_date, float(additive_value), reason, now_iso()),
        )
        conn.execute(
            "UPDATE contracts SET updated_at = ? WHERE id = ?",
            (now_iso(), contract_id),
        )
    conn.close()
    add_event(contract_id, "aditivo", {"date": additive_date, "value": additive_value, "reason": reason})


def edit_contract(contract_id: int, updates: dict) -> None:
    contract = get_contract_by_id(contract_id)
    if not contract:
        raise ValueError("Contrato não encontrado")

    allowed = {
        "title": "title",
        "department": "department",
        "scope_text": "scope_text",
        "clauses_text": "clauses_text",
        "contract_value": "contract_value",
        "executed_value": "executed_value",
        "savings_value": "savings_value",
        "roi_value": "roi_value",
        "end_date": "end_date",
    }

    sets = []
    params = []
    for k, col in allowed.items():
        if k in updates:
            sets.append(f"{col} = ?")
            params.append(updates[k])

    if not sets:
        return

    new_version = int(contract.get("version", 1)) + 1
    sets += ["version = ?", "updated_at = ?"]
    params += [new_version, now_iso(), contract_id]

    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE contracts SET {', '.join(sets)} WHERE id = ?", params)
    conn.close()

    add_event(contract_id, "edit", {"changes": updates, "new_version": new_version})


def update_contract_activity(contract_id: int, updates: dict, event_type: str = "activity_update") -> None:
    contract = get_contract_by_id(contract_id)
    if not contract:
        raise ValueError("Contrato não encontrado")

    allowed = {
        "executed_value": "executed_value",
        "savings_value": "savings_value",
        "roi_value": "roi_value",
        "legal_notes": "legal_notes",
        "signed_date": "signed_date",
        "archived_date": "archived_date",
        "digitally_signed": "digitally_signed",
        "strategic_alignment": "strategic_alignment",
        "revenue_contribution": "revenue_contribution",
        "operation_critical": "operation_critical",
        "supplier_key_dependency": "supplier_key_dependency",
        "supplier_diversification_score": "supplier_diversification_score",
        "maturity_score": "maturity_score",
        "governance_index": "governance_index",
        "automation_pct": "automation_pct",
        "default_probability": "default_probability",
        "aggregate_financial_risk": "aggregate_financial_risk",
        "disruption_predictive_score": "disruption_predictive_score",
        "request_date": "request_date",
    }

    sets = []
    params = []
    applied_changes = {}
    for k, col in allowed.items():
        if k in updates:
            sets.append(f"{col} = ?")
            params.append(updates[k])
            applied_changes[k] = updates[k]

    if not sets:
        return

    sets.append("updated_at = ?")
    params.append(now_iso())
    params.append(contract_id)

    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE contracts SET {', '.join(sets)} WHERE id = ?", params)
    conn.close()
    add_event(contract_id, event_type, {"changes": applied_changes})


def download_pdf_bytes(contract_id: int) -> bytes | None:
    contract = get_contract_by_id(contract_id)
    if not contract or not contract.get("pdf_path"):
        return None
    path = Path(contract["pdf_path"])
    if not path.exists():
        return None
    return path.read_bytes()


def get_contract_events(contract_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM contract_events WHERE contract_id = ? ORDER BY created_at DESC", (contract_id,)
    ).fetchall()
    conn.close()
    out = []
    for row in rows:
        item = dict(row)
        item["event_data"] = loads(item.pop("event_data_json"), {})
        out.append(item)
    return out


def upsert_compliance(contract_id: int, payload: dict):
    conn = get_connection()
    now = now_iso()
    existing = conn.execute(
        "SELECT id FROM compliance_checks WHERE contract_id = ?", (contract_id,)
    ).fetchone()
    with conn:
        if existing:
            conn.execute(
                """
                UPDATE compliance_checks
                SET mandatory_clauses_score = ?, out_of_standard = ?, has_guarantee = ?,
                    has_insurance = ?, regulatory_compliance_pct = ?, audited = ?,
                    nonconformities_count = ?, risk_score = ?, updated_at = ?
                WHERE contract_id = ?
                """,
                (
                    payload.get("mandatory_clauses_score", 0),
                    int(bool(payload.get("out_of_standard", False))),
                    int(bool(payload.get("has_guarantee", False))),
                    int(bool(payload.get("has_insurance", False))),
                    payload.get("regulatory_compliance_pct", 0),
                    int(bool(payload.get("audited", False))),
                    payload.get("nonconformities_count", 0),
                    payload.get("risk_score", 0),
                    now,
                    contract_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO compliance_checks (
                    contract_id, mandatory_clauses_score, out_of_standard, has_guarantee,
                    has_insurance, regulatory_compliance_pct, audited, nonconformities_count,
                    risk_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contract_id,
                    payload.get("mandatory_clauses_score", 0),
                    int(bool(payload.get("out_of_standard", False))),
                    int(bool(payload.get("has_guarantee", False))),
                    int(bool(payload.get("has_insurance", False))),
                    payload.get("regulatory_compliance_pct", 0),
                    int(bool(payload.get("audited", False))),
                    payload.get("nonconformities_count", 0),
                    payload.get("risk_score", 0),
                    now,
                    now,
                ),
            )
    conn.close()


def upsert_supplier_performance(contract_id: int, payload: dict):
    conn = get_connection()
    now = now_iso()
    existing = conn.execute(
        "SELECT id FROM supplier_performance WHERE contract_id = ?", (contract_id,)
    ).fetchone()
    with conn:
        if existing:
            conn.execute(
                """
                UPDATE supplier_performance
                SET sla_pct = ?, delivery_fail_rate = ?, on_time_pct = ?, quality_score = ?,
                    supplier_switch_rate = ?, satisfaction_score = ?, updated_at = ?
                WHERE contract_id = ?
                """,
                (
                    payload.get("sla_pct", 0),
                    payload.get("delivery_fail_rate", 0),
                    payload.get("on_time_pct", 0),
                    payload.get("quality_score", 0),
                    payload.get("supplier_switch_rate", 0),
                    payload.get("satisfaction_score", 0),
                    now,
                    contract_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO supplier_performance (
                    contract_id, sla_pct, delivery_fail_rate, on_time_pct, quality_score,
                    supplier_switch_rate, satisfaction_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contract_id,
                    payload.get("sla_pct", 0),
                    payload.get("delivery_fail_rate", 0),
                    payload.get("on_time_pct", 0),
                    payload.get("quality_score", 0),
                    payload.get("supplier_switch_rate", 0),
                    payload.get("satisfaction_score", 0),
                    now,
                    now,
                ),
            )
    conn.close()
