# src/ingest/config.py
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
CLEAN = DATA / "clean"
DB_SIMPLE = DATA / "lottery.db"
DB_STAR = DATA / "lottery_star.db"

# Optional Socrata App Token (not required for public)
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN", "").strip()

PROCESSED.mkdir(parents=True, exist_ok=True)
CLEAN.mkdir(parents=True, exist_ok=True)
