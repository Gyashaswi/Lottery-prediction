# Basic data-quality checks across data/clean and both DBs.
from pathlib import Path
import sqlite3
import sys
import pandas as pd

CLEAN = Path("data/clean")
DB_SIMPLE = Path("data/lottery.db")
DB_STAR = Path("data/lottery_star.db")

def require_file(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        raise SystemExit(f"[DQ][FAIL] missing or empty file: {path}")

def check_clean_files():
    for f in ["mega_millions.csv","powerball.csv","take5.csv","cash4life.csv","ny_lotto.csv","numbers.csv","win4.csv"]:
        require_file(CLEAN / f)
    print("[DQ] clean files present ✓")

    # quick schema checks
    daily = pd.read_csv(CLEAN/"numbers.csv", dtype=str)
    if not {"draw_date","session","pick"}.issubset(daily.columns):
        raise SystemExit("[DQ][FAIL] numbers.csv missing required columns")
    if daily["pick"].str.len().ne(3).any():
        raise SystemExit("[DQ][FAIL] numbers.csv non-3-digit pick detected")
    print("[DQ] numbers schema ✓")

    w4 = pd.read_csv(CLEAN/"win4.csv", dtype=str)
    if w4["pick"].str.len().ne(4).any():
        raise SystemExit("[DQ][FAIL] win4.csv non-4-digit pick detected")
    print("[DQ] win4 schema ✓")

def check_db(path: Path, table_checks: list[tuple[str, str]]):
    con = sqlite3.connect(path)
    cur = con.cursor()
    for table, key_expr in table_checks:
        # existence
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            n = cur.fetchone()[0]
        except sqlite3.Error as e:
            con.close()
            raise SystemExit(f"[DQ][FAIL] {path.name}: table {table} missing ({e})")
        # basic uniqueness (if a key_expr provided)
        if key_expr:
            sql = f"SELECT COUNT(*)-COUNT(DISTINCT {key_expr}) FROM {table};"
            dup = cur.execute(sql).fetchone()[0]
            if dup and dup > 0:
                con.close()
                raise SystemExit(f"[DQ][FAIL] {path.name}: duplicates on key {key_expr} in {table}: {dup}")
        print(f"[DQ] {path.name}:{table} rows={n:,} ✓")
    con.close()

def main():
    check_clean_files()
    check_db(DB_SIMPLE, [
        ("mega_millions_draws", "draw_date"),
        ("powerball_draws",     "draw_date"),
        ("take5_draws",         "draw_date"),
        ("cash4life_draws",     "draw_date"),
        ("ny_lotto_draws",      "draw_date"),
        ("numbers_draws",       "draw_date||'|'||session"),
        ("win4_draws",          "draw_date||'|'||session"),
    ])
    check_db(DB_STAR, [
        ("fact_set_draws",    "game_id||'|'||draw_date"),
        ("fact_set_numbers",  "game_id||'|'||draw_date||'|'||position"),
        ("fact_daily_draws",  "game_id||'|'||draw_date||'|'||session_id"),
    ])
    print("[DQ] all checks passed ✓")

if __name__ == "__main__":
    main()
