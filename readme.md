# 🎯 Lottery Prediction (NY Lottery) — Data Pipeline

End-to-end data engineering project for NY Lottery games:
**Mega Millions, Powerball, Take 5, Cash4Life, NY Lotto, Numbers, Win4**.

This repo showcases skills across **data collection → cleaning → modeling-ready storage** with both a simple DB and a normalized star schema. Scraping is optional; we currently use **official NY Open Data APIs**.

---

## Features

- **Incremental API ingestion** (Socrata CSV endpoints; Numbers/Win4 split)
- **Robust cleaning** (dates, parsing winning numbers, zero-padding 3/4-digit picks)
- **Two SQLite databases**
  - `data/lottery.db` — per-game flat tables (quick checks/dashboards)
  - `data/lottery_star.db` — normalized (dim/fact) analytics schema
- **Data Quality checks** (hard fail if something’s off)
- **Indexes + VACUUM** for speed/size
- **One-command run** on Windows via `make.bat` (or manual scripts)
- GitHub Action workflow prepared (daily updates)

---

## Architecture (current)

NY Open Data APIs ──► fetch_api.py ──► data/processed/.csv
└──► clean_data.py ───► data/clean/.csv
└──► load_to_db.py ───► data/lottery.db
└──► load_to_star.py ──► data/lottery_star.db
└──► dq_checks.py ───► quality gates
└──► build_indices.py ─► indexes + vacuum