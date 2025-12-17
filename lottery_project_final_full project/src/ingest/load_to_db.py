# src/ingest/load_to_db.py
"""
Load cleaned lottery CSVs from data/clean into a SQLite database (data/lottery.db).

Tables (all separate):
  - mega_millions_draws (PK: draw_date)
  - powerball_draws     (PK: draw_date)
  - take5_draws         (PK: draw_date)
  - cash4life_draws     (PK: draw_date)
  - ny_lotto_draws      (PK: draw_date)
  - numbers_draws       (PK: draw_date, session)
  - win4_draws          (PK: draw_date, session)
"""

import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("data/lottery.db")
CLEAN_DIR = Path("data/clean")

# ---------- Table creation SQL (separate per game) ----------
CREATE_SET_DRAW = {
    "mega_millions": """
        CREATE TABLE IF NOT EXISTS mega_millions_draws (
          draw_date TEXT NOT NULL PRIMARY KEY,
          numbers   TEXT NOT NULL,
          bonus     TEXT,
          source    TEXT,
          loaded_at TEXT
        );
    """,
    "powerball": """
        CREATE TABLE IF NOT EXISTS powerball_draws (
          draw_date TEXT NOT NULL PRIMARY KEY,
          numbers   TEXT NOT NULL,
          bonus     TEXT,
          source    TEXT,
          loaded_at TEXT
        );
    """,
    "take5": """
        CREATE TABLE IF NOT EXISTS take5_draws (
          draw_date TEXT NOT NULL PRIMARY KEY,
          numbers   TEXT NOT NULL,
          bonus     TEXT,
          source    TEXT,
          loaded_at TEXT
        );
    """,
    "cash4life": """
        CREATE TABLE IF NOT EXISTS cash4life_draws (
          draw_date TEXT NOT NULL PRIMARY KEY,
          numbers   TEXT NOT NULL,
          bonus     TEXT,
          source    TEXT,
          loaded_at TEXT
        );
    """,
    "ny_lotto": """
        CREATE TABLE IF NOT EXISTS ny_lotto_draws (
          draw_date TEXT NOT NULL PRIMARY KEY,
          numbers   TEXT NOT NULL,
          bonus     TEXT,
          source    TEXT,
          loaded_at TEXT
        );
    """,
}

CREATE_NUMBERS = """
CREATE TABLE IF NOT EXISTS numbers_draws (
  draw_date TEXT NOT NULL,
  session   TEXT NOT NULL,     -- 'midday' | 'evening'
  pick      TEXT NOT NULL,     -- zero-padded 3 digits
  sum       TEXT,
  booster   TEXT,
  source    TEXT,
  loaded_at TEXT,
  PRIMARY KEY (draw_date, session)
);
"""

CREATE_WIN4 = """
CREATE TABLE IF NOT EXISTS win4_draws (
  draw_date TEXT NOT NULL,
  session   TEXT NOT NULL,     -- 'midday' | 'evening'
  pick      TEXT NOT NULL,     -- zero-padded 4 digits
  sum       TEXT,
  booster   TEXT,
  source    TEXT,
  loaded_at TEXT,
  PRIMARY KEY (draw_date, session)
);
"""

def upsert_df(df: pd.DataFrame, table: str, pk_cols: list[str]):
    """Idempotent upsert into SQLite."""
    if df.empty:
        print(f"[skip] {table}: no data to load")
        return
    conn = sqlite3.connect(DB_PATH)
    cols = list(df.columns)
    placeholders = ",".join(["?"] * len(cols))
    col_csv = ",".join(cols)
    update_set = ",".join([f"{c}=excluded.{c}" for c in cols if c not in pk_cols])
    sql = f"""
      INSERT INTO {table} ({col_csv})
      VALUES ({placeholders})
      ON CONFLICT({','.join(pk_cols)})
      DO UPDATE SET {update_set};
    """
    conn.executemany(sql, df.itertuples(index=False, name=None))
    conn.commit()
    conn.close()
    print(f"[load] {table}: {len(df):,} rows upserted")

def main():
    # Ensure DB and tables exist
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for g, ddl in CREATE_SET_DRAW.items():
        cur.executescript(ddl)
    cur.executescript(CREATE_NUMBERS)
    cur.executescript(CREATE_WIN4)
    conn.commit()
    conn.close()

    # ----- Load set-draw games into their own tables -----
    for game, table in [
        ("mega_millions", "mega_millions_draws"),
        ("powerball",     "powerball_draws"),
        ("take5",         "take5_draws"),
        ("cash4life",     "cash4life_draws"),
        ("ny_lotto",      "ny_lotto_draws"),
    ]:
        f = CLEAN_DIR / f"{game}.csv"
        if not f.exists() or f.stat().st_size == 0:
            print(f"[warn] missing clean file: {f.name}")
            continue
        df = pd.read_csv(f, dtype=str).fillna("")
        # Expect columns: draw_date, numbers, bonus, source, loaded_at
        keep = [c for c in ["draw_date","numbers","bonus","source","loaded_at"] if c in df.columns]
        df = df[keep]
        upsert_df(df, table, pk_cols=["draw_date"])

    # ----- Load daily games into their own tables -----
    # Numbers
    fnum = CLEAN_DIR / "numbers.csv"
    if fnum.exists() and fnum.stat().st_size > 0:
        df = pd.read_csv(fnum, dtype=str).fillna("")
        keep = [c for c in ["draw_date","session","pick","sum","booster","source","loaded_at"] if c in df.columns]
        df = df[keep]
        upsert_df(df, "numbers_draws", pk_cols=["draw_date","session"])
    else:
        print("[warn] missing clean file: numbers.csv")

    # Win4
    fwin = CLEAN_DIR / "win4.csv"
    if fwin.exists() and fwin.stat().st_size > 0:
        df = pd.read_csv(fwin, dtype=str).fillna("")
        keep = [c for c in ["draw_date","session","pick","sum","booster","source","loaded_at"] if c in df.columns]
        df = df[keep]
        upsert_df(df, "win4_draws", pk_cols=["draw_date","session"])
    else:
        print("[warn] missing clean file: win4.csv")

    print(f"[done] Loaded all games into {DB_PATH}")

if __name__ == "__main__":
    main()
