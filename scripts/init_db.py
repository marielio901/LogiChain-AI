import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.migrations import run_migrations


if __name__ == "__main__":
    run_migrations()
    print("Banco SQLite inicializado com sucesso em storage/logichain.db")
