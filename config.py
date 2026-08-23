import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "todo.db"

PRIORITIES = ("High", "Medium", "Low")
PRIORITY_INDICATORS = {
    "High": "🔴",
    "Medium": "🟡",
    "Low": "🟢",
}
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
