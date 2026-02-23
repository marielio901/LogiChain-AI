import re
from datetime import date, timedelta

from services.contract_service import get_contract_by_number, list_contracts
from db.connection import get_connection
from utils.helpers import brl


def _safe_contract_view(contract: dict) -> dict:
    return {
        "numero": contract.get("contract_number"),
        "tipo": contract.get("type"),
        "titulo": contract.get("title"),
        "departamento": contract.get("department"),
        "status": contract.get("status"),
        "fornecedor": contract.get("contracted", {}).get("name"),
        "valor": contract.get("contract_value"),
        "inicio": contract.get("start_date"),
        "fim": contract.get("end_date"),
        "escopo": contract.get("scope_text"),
        "clausulas": contract.get("clauses_text"),
    }


def _risk_for_contract(contract_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT risk_score, out_of_standard, nonconformities_count FROM compliance_checks WHERE contract_id = ?",
        (contract_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def _extract_days(question: str, default: int = 30) -> int:
    match = re.search(r"(\d{1,3})\s*dias", question.lower())
    return int(match.group(1)) if match else default


def _summary_response(contract_number: str) -> str:
    contract = get_contract_by_number(contract_number)
    if not contract:
        return f"Não encontrei o contrato {contract_number}. Verifique o número informado."

    info = _safe_contract_view(contract)
    return (
        f"Resumo do contrato {info['numero']}:\n"
        f"- Título: {info['titulo']}\n"
        f"- Tipo: {info['tipo']}\n"
        f"- Status: {info['status']}\n"
        f"- Departamento: {info['departamento']}\n"
        f"- Fornecedor/Contratado: {info['fornecedor']}\n"
        f"- Vigência: {info['inicio']} até {info['fim']}\n"
        f"- Valor: {brl(info['valor'])}\n"
        f"- Escopo: {info['escopo'] or 'Sem descrição'}"
    )


def answer_question(question: str, mode: str = "Consulta Geral") -> str:
    q = question.strip()
    q_lower = q.lower()

    if not q:
        return "Faça uma pergunta sobre os contratos."

    number_match = re.search(r"LC-\d{4}-\d{3}", q, flags=re.IGNORECASE)
    if mode == "Resumo do Contrato" or number_match:
        contract_number = number_match.group(0).upper() if number_match else ""
        if contract_number:
            return _summary_response(contract_number)
        return "No modo Resumo do Contrato, informe o número (ex: LC-2026-001)."

    contracts = list_contracts()
    if not contracts:
        return "Não há contratos cadastrados no momento."

    if "vencem" in q_lower or "vencer" in q_lower:
        days = _extract_days(q, default=45)
        limit = date.today() + timedelta(days=days)
        rows = []
        for c in contracts:
            end = c.get("end_date")
            try:
                d_end = date.fromisoformat(str(end))
            except Exception:
                continue
            if date.today() <= d_end <= limit:
                rows.append(c)
        if not rows:
            return f"Nenhum contrato vence nos próximos {days} dias."
        lines = [f"Contratos que vencem nos próximos {days} dias:"]
        for c in sorted(rows, key=lambda x: x.get("end_date")):
            lines.append(f"- {c['contract_number']} | {c['title']} | vence em {c['end_date']}")
        return "\n".join(lines)

    if "risco alto" in q_lower or mode == "Análise de Risco":
        risky = []
        for c in contracts:
            risk = _risk_for_contract(c["id"])
            if risk and float(risk.get("risk_score", 0) or 0) >= 70:
                risky.append((c, risk))
        if not risky:
            return "Não encontrei contratos com risco alto (score >= 70)."
        lines = ["Contratos em vigor com risco alto:"]
        for c, risk in risky:
            if c["status"] == "Em vigor":
                lines.append(
                    f"- {c['contract_number']} | {c['title']} | risco {risk['risk_score']} | não conformidades {risk['nonconformities_count']}"
                )
        if len(lines) == 1:
            return "Existem contratos com risco alto, mas nenhum está com status 'Em vigor'."
        return "\n".join(lines)

    if "total contratado por fornecedor" in q_lower or "total por fornecedor" in q_lower:
        totals = {}
        for c in contracts:
            supplier = c.get("contracted", {}).get("name", "Não informado")
            totals[supplier] = totals.get(supplier, 0) + float(c.get("contract_value", 0) or 0)
        lines = ["Total contratado por fornecedor:"]
        for supplier, value in sorted(totals.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- {supplier}: {brl(value)}")
        return "\n".join(lines)

    if "em vigor" in q_lower and "listar" in q_lower:
        active = [c for c in contracts if c["status"] == "Em vigor"]
        if not active:
            return "Não há contratos em vigor."
        lines = ["Contratos em vigor:"]
        for c in active:
            lines.append(f"- {c['contract_number']} | {c['title']} | {brl(c['contract_value'])}")
        return "\n".join(lines)

    return (
        "Não consegui mapear sua pergunta para uma consulta segura. "
        "Tente usar formatos como: 'Quais contratos vencem nos próximos 45 dias?' "
        "ou informe o número do contrato (ex: LC-2026-001)."
    )
