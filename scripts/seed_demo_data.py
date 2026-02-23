import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.connection import get_connection
from db.migrations import run_migrations
from utils.helpers import dumps


def random_date(start: datetime, end: datetime) -> datetime:
    delta = max((end - start).days, 1)
    return start + timedelta(days=random.randint(0, delta))


def insert_row(conn, table: str, data: dict):
    cols = list(data.keys())
    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    cur = conn.execute(sql, [data[c] for c in cols])
    return cur.lastrowid


def main():
    random.seed(42)
    run_migrations()

    year = datetime.now().year
    total_to_create = 80

    types = ["Prestação de Serviço", "Fornecimento de Materiais", "Alocação"]
    departments = ["Operações", "Suprimentos", "TI", "Jurídico", "Financeiro", "Logística"]
    statuses = ["Gerado", "Assinado", "Protocolado", "Em vigor", "Finalizado"]
    contractors = ["LogiChain Holding", "Grupo Atlas", "Nexa Corp"]
    suppliers = ["TransRoad Brasil", "Alfa Industrial", "Beta Services", "Orbital Tech", "Cargas Unidas", "Prime Solutions", "Fornec+"]

    base_start = datetime.now() - timedelta(days=420)
    now = datetime.now()

    conn = get_connection()
    created = 0
    with conn:
        existing = conn.execute("SELECT COUNT(*) AS c FROM contracts").fetchone()["c"]
        start_seq = int(existing) + 1

        for i in range(start_seq, start_seq + total_to_create):
            contract_number = f"LC-{year}-{i:03d}"
            if conn.execute("SELECT 1 FROM contracts WHERE contract_number = ?", (contract_number,)).fetchone():
                continue

            ctype = random.choice(types)
            dept = random.choice(departments)
            status = random.choices(statuses, weights=[10, 15, 18, 37, 20], k=1)[0]

            created_at = random_date(base_start, now - timedelta(days=1))
            start_date = random_date(created_at - timedelta(days=20), now + timedelta(days=120))
            term_days = random.randint(45, 420)
            end_date = start_date + timedelta(days=term_days)

            contract_value = round(random.uniform(30000, 1500000), 2)
            executed_value = round(contract_value * random.uniform(0.2, 1.15), 2)
            savings_value = round(contract_value * random.uniform(0.0, 0.15), 2)
            roi_value = round(random.uniform(2, 48), 2)

            signed_date = None
            if status in ["Assinado", "Protocolado", "Em vigor", "Finalizado"]:
                signed_date = created_at + timedelta(days=random.randint(2, 35))

            archived_date = None
            if status == "Finalizado":
                archived_date = end_date + timedelta(days=random.randint(5, 60))

            critical = random.random() < 0.32
            risk_fin = round(random.uniform(10000, 250000), 2)

            contract_data = {
                "contract_number": contract_number,
                "type": ctype,
                "title": f"{ctype} - Projeto {i}",
                "department": dept,
                "cost_center": f"CC-{random.randint(100, 999)}",
                "status": status,
                "tags": dumps([dept.lower(), ctype.lower().split()[0]]),
                "contractor_json": dumps({
                    "name": random.choice(contractors),
                    "doc": f"00.000.000/0001-{random.randint(10,99)}",
                    "address": "Av. Central, 1000 - SP",
                    "email": "contratante@empresa.com",
                    "phone": "+55 11 3000-0000",
                }),
                "contracted_json": dumps({
                    "name": random.choice(suppliers),
                    "doc": f"11.111.111/0001-{random.randint(10,99)}",
                    "address": "Rua dos Fornecedores, 500 - SP",
                    "email": "contato@fornecedor.com",
                    "phone": "+55 11 4000-0000",
                }),
                "scope_text": "Execução de escopo logístico com metas e indicadores de performance.",
                "deliverables_text": "Entrega mensal de serviços/produtos com relatório de execução.",
                "sla_targets_json": dumps({"sla_pct": round(random.uniform(85, 99.9), 2), "on_time_target": round(random.uniform(85, 99.9), 2)}),
                "acceptance_rules_text": "Aceite condicionado ao cumprimento de SLA e inspeção de qualidade.",
                "clauses_text": "Cláusulas de vigência, pagamento, penalidades, rescisão, confidencialidade e compliance.",
                "critical_clauses": int(critical),
                "critical_clauses_text": "Cláusula de confidencialidade e multa elevada." if critical else "",
                "mandatory_clauses_json": dumps(["Objeto", "Vigência", "Pagamento", "Penalidades", "Rescisão", "LGPD"]),
                "legal_notes": "Sem litígio." if random.random() > 0.14 else "Potencial litigio comercial.",
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "milestones_json": dumps([
                    {"date": (start_date + timedelta(days=30)).date().isoformat(), "description": "Marco 1"},
                    {"date": (start_date + timedelta(days=90)).date().isoformat(), "description": "Marco 2"},
                ]),
                "payment_terms": "Mensal com 30 dias",
                "reajust_index": random.choice(["IPCA", "IGP-M", "", "INPC"]),
                "penalties_text": "Multa por atraso e descumprimento de SLA.",
                "penalties_value": round(random.uniform(0, 80000), 2),
                "signatures_json": dumps({
                    "contractor_sign": "Representante Contratante - São Paulo",
                    "contracted_sign": "Representante Contratado - São Paulo",
                    "witnesses": "Testemunha 1; Testemunha 2",
                }),
                "contract_value": contract_value,
                "executed_value": executed_value,
                "savings_value": savings_value,
                "roi_value": roi_value,
                "request_date": created_at.date().isoformat(),
                "signed_date": signed_date.date().isoformat() if signed_date else None,
                "archived_date": archived_date.date().isoformat() if archived_date else None,
                "digitally_signed": int(random.random() < 0.68),
                "strategic_alignment": int(random.random() < 0.62),
                "revenue_contribution": round(random.uniform(10000, 350000), 2),
                "operation_critical": int(random.random() < 0.35),
                "supplier_key_dependency": int(random.random() < 0.28),
                "supplier_diversification_score": round(random.uniform(25, 95), 2),
                "maturity_score": round(random.uniform(30, 95), 2),
                "governance_index": round(random.uniform(35, 97), 2),
                "automation_pct": round(random.uniform(20, 90), 2),
                "default_probability": round(random.uniform(1, 35), 2),
                "aggregate_financial_risk": risk_fin,
                "disruption_predictive_score": round(random.uniform(10, 85), 2),
                "created_at": created_at.isoformat(timespec="seconds"),
                "updated_at": now.isoformat(timespec="seconds"),
                "pdf_path": None,
                "is_archived": int(status == "Finalizado"),
                "is_finalized": int(status == "Finalizado"),
                "version": random.randint(1, 4),
            }

            contract_id = insert_row(conn, "contracts", contract_data)

            for _ in range(random.randint(0, 4)):
                add_date = start_date + timedelta(days=random.randint(10, max(term_days, 20)))
                insert_row(conn, "contract_additives", {
                    "contract_id": contract_id,
                    "additive_date": add_date.date().isoformat(),
                    "additive_value": round(random.uniform(5000, 120000), 2),
                    "reason": random.choice(["Escopo adicional", "Reequilíbrio econômico", "Reajuste anual", "Inclusão de módulo"]),
                    "created_at": now.isoformat(timespec="seconds"),
                })

            risk_score = round(random.uniform(12, 94), 2)
            insert_row(conn, "compliance_checks", {
                "contract_id": contract_id,
                "mandatory_clauses_score": round(random.uniform(72, 100), 2),
                "out_of_standard": int(risk_score > 76 and random.random() < 0.55),
                "has_guarantee": int(random.random() < 0.71),
                "has_insurance": int(random.random() < 0.63),
                "regulatory_compliance_pct": round(random.uniform(70, 100), 2),
                "audited": int(random.random() < 0.52),
                "nonconformities_count": random.randint(0, 9),
                "risk_score": risk_score,
                "created_at": now.isoformat(timespec="seconds"),
                "updated_at": now.isoformat(timespec="seconds"),
            })

            insert_row(conn, "supplier_performance", {
                "contract_id": contract_id,
                "sla_pct": round(random.uniform(75, 99.8), 2),
                "delivery_fail_rate": round(random.uniform(0, 26), 2),
                "on_time_pct": round(random.uniform(70, 99.7), 2),
                "quality_score": round(random.uniform(60, 98), 2),
                "supplier_switch_rate": round(random.uniform(0, 35), 2),
                "satisfaction_score": round(random.uniform(55, 97), 2),
                "created_at": now.isoformat(timespec="seconds"),
                "updated_at": now.isoformat(timespec="seconds"),
            })

            insert_row(conn, "contract_events", {
                "contract_id": contract_id,
                "event_type": "created",
                "event_data_json": dumps({"status": status}),
                "created_at": created_at.isoformat(timespec="seconds"),
            })
            if status != "Gerado":
                insert_row(conn, "contract_events", {
                    "contract_id": contract_id,
                    "event_type": "status_change",
                    "event_data_json": dumps({"from": "Gerado", "to": status, "user": "seed"}),
                    "created_at": (created_at + timedelta(days=3)).isoformat(timespec="seconds"),
                })

            created += 1

    conn.close()
    print(f"Seed finalizado. Contratos novos inseridos: {created}")


if __name__ == "__main__":
    main()
