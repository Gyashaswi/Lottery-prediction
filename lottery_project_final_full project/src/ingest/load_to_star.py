# src/ingest/load_to_star.py
"""
Build a normalized (star-ish) SQLite database from data/clean CSVs.

Creates data/lottery_star.db with:
  Dimensions:
    - dim_game(game_id, game_name, game_type)
    - dim_session(session_id, session_name)
    - dim_date(date, year, month, day, weekday)
  Facts:
    - fact_set_draws(game_id, draw_date, bonus)                       -- set-draw metadata
    - fact_set_numbers(game_id, draw_date, position, number)          -- atomic numbers (1 row per main number)
    - fact_daily_draws(game_id, draw_date, session_id, pick, sum, booster) -- daily games by session
"""

import sqlite3
from pathlib import Path
import pandas as pd

CLEAN = Path("data/clean")
DB    = Path("data/lottery_star.db")

GAME_MAP = {
    "mega_millions": 1,
    "powerball":     2,
    "take5":         3,
    "cash4life":     4,
    "ny_lotto":      5,
    "numbers":       6,
    "win4":          7,
}
GAME_TYPE = {
    "mega_millions": "set_draw",
    "powerball":     "set_draw",
    "take5":         "set_draw",
    "cash4life":     "set_draw",
    "ny_lotto":      "set_draw",
    "numbers":       "daily",
    "win4":          "daily",
}

DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_game (
  game_id    INTEGER PRIMARY KEY,
  game_name  TEXT NOT NULL UNIQUE,
  game_type  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_session (
  session_id   INTEGER PRIMARY KEY,
  session_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_date (
  date    TEXT PRIMARY KEY,   -- YYYY-MM-DD
  year    INTEGER,
  month   INTEGER,
  day     INTEGER,
  weekday TEXT                -- Monday..Sunday
);

CREATE TABLE IF NOT EXISTS fact_set_draws (
  game_id   INTEGER NOT NULL REFERENCES dim_game(game_id),
  draw_date TEXT    NOT NULL REFERENCES dim_date(date),
  bonus     TEXT,
  PRIMARY KEY (game_id, draw_date)
);

CREATE TABLE IF NOT EXISTS fact_set_numbers (
  game_id   INTEGER NOT NULL REFERENCES dim_game(game_id),
  draw_date TEXT    NOT NULL REFERENCES dim_date(date),
  position  INTEGER NOT NULL,               -- 1..N
  number    INTEGER NOT NULL,
  PRIMARY KEY (game_id, draw_date, position),
  FOREIGN KEY (game_id, draw_date) REFERENCES fact_set_draws(game_id, draw_date)
);

CREATE TABLE IF NOT EXISTS fact_daily_draws (
  game_id    INTEGER NOT NULL REFERENCES dim_game(game_id),
  draw_date  TEXT    NOT NULL REFERENCES dim_date(date),
  session_id INTEGER NOT NULL REFERENCES dim_session(session_id),
  pick       TEXT    NOT NULL,   -- zero-padded '099' / '0999'
  sum        TEXT,
  booster    TEXT,
  PRIMARY KEY (game_id, draw_date, session_id)
);
"""

def execmany(conn, sql, rows):
    if not rows:
        return
    conn.executemany(sql, rows)

def ensure_dims(conn):
    cur = conn.cursor()
    cur.executescript(DDL)

    # dim_game
    game_rows = [(gid, name, GAME_TYPE[name]) for name, gid in GAME_MAP.items()]
    execmany(conn, "INSERT OR IGNORE INTO dim_game(game_id, game_name, game_type) VALUES (?,?,?)", game_rows)

    # dim_session
    session_rows = [(1, "midday"), (2, "evening")]
    execmany(conn, "INSERT OR IGNORE INTO dim_session(session_id, session_name) VALUES (?,?)", session_rows)
    conn.commit()

def upsert_dim_date(conn, dates):
    if not dates:
        return
    df = pd.DataFrame({"date": sorted(set(dates))})
    dt = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = dt.dt.year
    df["month"] = dt.dt.month
    df["day"] = dt.dt.day
    df["weekday"] = dt.dt.day_name()
    rows = df[["date","year","month","day","weekday"]].itertuples(index=False, name=None)
    execmany(conn, """
      INSERT INTO dim_date(date, year, month, day, weekday)
      VALUES (?,?,?,?,?)
      ON CONFLICT(date) DO UPDATE SET
        year=excluded.year, month=excluded.month, day=excluded.day, weekday=excluded.weekday
    """, list(rows))
    conn.commit()

def load_set_draw(conn, game: str):
    path = CLEAN / f"{game}.csv"
    if not path.exists() or path.stat().st_size == 0:
        print(f"[set] {game}: no file"); return
    df = pd.read_csv(path, dtype=str).fillna("")
    if df.empty:
        print(f"[set] {game}: empty"); return

    # Expect columns: draw_date, numbers (comma-joined), bonus (maybe empty)
    df["draw_date"] = pd.to_datetime(df["draw_date"], errors="coerce").dt.date.astype("string")
    df = df.dropna(subset=["draw_date"])

    # Upsert dim_date
    upsert_dim_date(conn, df["draw_date"].tolist())

    gid = GAME_MAP[game]
    # fact_set_draws
    rows_draws = [(gid, d, b) for d, b in df[["draw_date","bonus"]].itertuples(index=False, name=None)]
    execmany(conn, """
      INSERT INTO fact_set_draws(game_id, draw_date, bonus)
      VALUES (?,?,?)
      ON CONFLICT(game_id, draw_date) DO UPDATE SET bonus=excluded.bonus
    """, rows_draws)

    # fact_set_numbers (split and position)
    nums_rows = []
    for d, nums in df[["draw_date","numbers"]].itertuples(index=False, name=None):
        if not nums:
            continue
        try:
            parts = [int(x) for x in str(nums).split(",") if x != ""]
        except Exception:
            continue
        # positions 1..N in the given (already sorted) order
        for pos, val in enumerate(parts, start=1):
            nums_rows.append((gid, d, pos, val))

    execmany(conn, """
      INSERT INTO fact_set_numbers(game_id, draw_date, position, number)
      VALUES (?,?,?,?)
      ON CONFLICT(game_id, draw_date, position) DO UPDATE SET number=excluded.number
    """, nums_rows)

    conn.commit()
    print(f"[set] {game}: draws={len(rows_draws):,}, numbers_rows={len(nums_rows):,}")

def load_daily(conn, game: str):
    path = CLEAN / f"{game}.csv"
    if not path.exists() or path.stat().st_size == 0:
        print(f"[daily] {game}: no file"); return
    df = pd.read_csv(path, dtype=str).fillna("")
    if df.empty:
        print(f"[daily] {game}: empty"); return

    df["draw_date"] = pd.to_datetime(df["draw_date"], errors="coerce").dt.date.astype("string")
    df = df.dropna(subset=["draw_date"])
    df["session"] = df["session"].str.lower()

    upsert_dim_date(conn, df["draw_date"].tolist())

    gid = GAME_MAP[game]
    session_id = df["session"].map({"midday": 1, "evening": 2}).fillna(0).astype(int)

    rows = []
    for (d, sid, pick, s, b) in df[["draw_date","session","pick","sum","booster"]].itertuples(index=False, name=None):
        sid_int = 1 if str(sid).lower() == "midday" else 2 if str(sid).lower() == "evening" else 0
        rows.append((gid, d, sid_int, pick, s, b))

    execmany(conn, """
      INSERT INTO fact_daily_draws(game_id, draw_date, session_id, pick, sum, booster)
      VALUES (?,?,?,?,?,?)
      ON CONFLICT(game_id, draw_date, session_id)
      DO UPDATE SET pick=excluded.pick, sum=excluded.sum, booster=excluded.booster
    """, rows)
    conn.commit()
    print(f"[daily] {game}: rows={len(rows):,}")

def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    ensure_dims(conn)

    # Load set-draw games
    for g in ["mega_millions","powerball","take5","cash4life","ny_lotto"]:
        load_set_draw(conn, g)

    # Load daily games
    for g in ["numbers","win4"]:
        load_daily(conn, g)

    conn.close()
    print(f"[done] normalized DB → {DB}")

if __name__ == "__main__":
    main()
