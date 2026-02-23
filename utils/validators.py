from datetime import date


ALLOWED_STATUS_FLOW = ["Gerado", "Assinado", "Protocolado", "Em vigor", "Finalizado"]


def validate_required_fields(payload: dict) -> list[str]:
    errors = []
    required = ["type", "title", "department", "start_date", "end_date", "contract_value"]
    for key in required:
        if payload.get(key) in (None, "", []):
            errors.append(f"Campo obrigatório ausente: {key}")

    contractor = payload.get("contractor", {})
    contracted = payload.get("contracted", {})

    for side, party in [("Contratante", contractor), ("Contratado", contracted)]:
        if not party.get("name"):
            errors.append(f"{side}: razão social/nome é obrigatório")
        if not party.get("doc"):
            errors.append(f"{side}: CNPJ/CPF é obrigatório")
        if not party.get("email"):
            errors.append(f"{side}: email é obrigatório")

    clauses_text = payload.get("clauses_text", "")
    if len(clauses_text.strip()) < 20:
        errors.append("Cláusulas mínimas insuficientes (mínimo 20 caracteres).")

    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    if isinstance(start_date, date) and isinstance(end_date, date) and start_date > end_date:
        errors.append("Data inicial deve ser menor ou igual à data final.")

    return errors


def can_transition(current_status: str, next_status: str, admin_override: bool = False) -> bool:
    if admin_override:
        return True
    if current_status == next_status:
        return True
    try:
        current_idx = ALLOWED_STATUS_FLOW.index(current_status)
        next_idx = ALLOWED_STATUS_FLOW.index(next_status)
    except ValueError:
        return False
    return next_idx in (current_idx - 1, current_idx + 1)
