import json
from datetime import datetime


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def dumps(data) -> str:
    return json.dumps(data or {}, ensure_ascii=False)


def loads(raw: str, default=None):
    if raw is None or raw == "":
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def brl(value: float | int | None) -> str:
    if value is None:
        return "R$ 0,00"
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
