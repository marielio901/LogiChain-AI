from dataclasses import dataclass


@dataclass
class ContractSummary:
    id: int
    contract_number: str
    type: str
    title: str
    department: str
    status: str
    contract_value: float
    start_date: str
    end_date: str
    contracted_name: str
