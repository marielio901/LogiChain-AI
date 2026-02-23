from db.connection import get_connection


DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS contracts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      contract_number TEXT UNIQUE NOT NULL,
      type TEXT NOT NULL,
      title TEXT NOT NULL,
      department TEXT NOT NULL,
      cost_center TEXT,
      status TEXT NOT NULL,
      tags TEXT,
      contractor_json TEXT NOT NULL,
      contracted_json TEXT NOT NULL,
      scope_text TEXT,
      deliverables_text TEXT,
      sla_targets_json TEXT,
      acceptance_rules_text TEXT,
      clauses_text TEXT,
      critical_clauses INTEGER DEFAULT 0,
      critical_clauses_text TEXT,
      mandatory_clauses_json TEXT,
      legal_notes TEXT,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      milestones_json TEXT,
      payment_terms TEXT,
      reajust_index TEXT,
      penalties_text TEXT,
      penalties_value REAL,
      signatures_json TEXT,
      contract_value REAL DEFAULT 0,
      executed_value REAL DEFAULT 0,
      savings_value REAL DEFAULT 0,
      roi_value REAL DEFAULT 0,
      request_date TEXT,
      signed_date TEXT,
      archived_date TEXT,
      digitally_signed INTEGER DEFAULT 0,
      strategic_alignment INTEGER DEFAULT 0,
      revenue_contribution REAL DEFAULT 0,
      operation_critical INTEGER DEFAULT 0,
      supplier_key_dependency INTEGER DEFAULT 0,
      supplier_diversification_score REAL DEFAULT 0,
      maturity_score REAL DEFAULT 0,
      governance_index REAL DEFAULT 0,
      automation_pct REAL DEFAULT 0,
      default_probability REAL DEFAULT 0,
      aggregate_financial_risk REAL DEFAULT 0,
      disruption_predictive_score REAL DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      pdf_path TEXT,
      is_archived INTEGER DEFAULT 0,
      is_finalized INTEGER DEFAULT 0,
      version INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS contract_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      contract_id INTEGER NOT NULL,
      event_type TEXT NOT NULL,
      event_data_json TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY (contract_id) REFERENCES contracts(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS contract_additives (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      contract_id INTEGER NOT NULL,
      additive_date TEXT NOT NULL,
      additive_value REAL NOT NULL,
      reason TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY (contract_id) REFERENCES contracts(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS compliance_checks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      contract_id INTEGER NOT NULL,
      mandatory_clauses_score REAL DEFAULT 0,
      out_of_standard INTEGER DEFAULT 0,
      has_guarantee INTEGER DEFAULT 0,
      has_insurance INTEGER DEFAULT 0,
      regulatory_compliance_pct REAL DEFAULT 0,
      audited INTEGER DEFAULT 0,
      nonconformities_count INTEGER DEFAULT 0,
      risk_score REAL DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY (contract_id) REFERENCES contracts(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS supplier_performance (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      contract_id INTEGER NOT NULL,
      sla_pct REAL DEFAULT 0,
      delivery_fail_rate REAL DEFAULT 0,
      on_time_pct REAL DEFAULT 0,
      quality_score REAL DEFAULT 0,
      supplier_switch_rate REAL DEFAULT 0,
      satisfaction_score REAL DEFAULT 0,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL,
      FOREIGN KEY (contract_id) REFERENCES contracts(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_contracts_type ON contracts(type)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_contracts_end_date ON contracts(end_date)
    """,
]


def run_migrations() -> None:
    conn = get_connection()
    with conn:
        for ddl in DDL_STATEMENTS:
            conn.execute(ddl)
    conn.close()
