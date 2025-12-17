# src/ingest/fetch_api.py
"""
fetch_api.py — Incremental fetch for NY Open Data (CSV), plus Numbers/Win4 split.

Set-draw games (mega_millions, powerball, take5, cash4life, ny_lotto):
  - Read max draw_date from data/processed/<game>.csv
  - Fetch only newer rows via $where draw_date > 'YYYY-MM-DD'
  - Append, dedupe, sort, save

Daily combined dataset (numbers_win4):
  - Full pull (fast enough), then split into data/processed/numbers.csv and win4.csv
"""

from pathlib import Path
import io
import requests
import pandas as pd

OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

URLS = {
    "mega_millions": "https://data.ny.gov/resource/5xaw-6ayf.csv",
    "powerball":     "https://data.ny.gov/resource/d6yy-54nr.csv",
    "take5":         "https://data.ny.gov/resource/dg63-4siq.csv",
    "cash4life":     "https://data.ny.gov/resource/kwxv-fwze.csv",
    "ny_lotto":      "https://data.ny.gov/resource/6nbc-h7bj.csv",
    "numbers_win4":  "https://data.ny.gov/resource/hsys-3def.csv",
}

def _read_existing(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size > 0:
        return pd.read_csv(path, dtype=str)
    return pd.DataFrame()

def _max_draw_date(df: pd.DataFrame) -> str | None:
    if df.empty or "draw_date" not in df.columns:
        return None
    dt = pd.to_datetime(df["draw_date"], errors="coerce")
    if dt.notna().any():
        return dt.max().date().isoformat()
    return None

def _read_csv_via_requests(base_url: str, params: dict) -> pd.DataFrame:
    """Fetch CSV using requests (safe query param encoding), then parse with pandas."""
    resp = requests.get(base_url, params=params, timeout=60)
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text), dtype=str)

def fetch_incremental_set(game: str, base_url: str, limit: int = 50000):
    out = OUT_DIR / f"{game}.csv"
    existing = _read_existing(out)
    last = _max_draw_date(existing)

    params = {"$limit": str(limit)}
    if last:
        # Socrata handles simple ISO dates fine for these datasets.
        params["$where"] = f"draw_date > '{last}'"

    print(f"[API] {game} … params: {params}")
    try:
        df_new = _read_csv_via_requests(base_url, params)
    except Exception as e:
        print(f"[API] {game} failed: {e}")
        return

    if existing.empty and df_new.empty:
        print(f"[API] {game}: nothing to write (empty initial)")
        return

    df_all = pd.concat([existing, df_new], ignore_index=True).drop_duplicates()
    if "draw_date" in df_all.columns:
        df_all["__dt"] = pd.to_datetime(df_all["draw_date"], errors="coerce")
        df_all = df_all.sort_values("__dt").drop(columns="__dt")

    df_all.to_csv(out, index=False)
    print(f"[API] {game} saved {len(df_all):,} rows → {out}")

def fetch_numbers_win4(base_url: str, limit: int = 50000):
    # Full pull, then split to numbers.csv (3-digit) and win4.csv (4-digit)
    params = {"$limit": str(limit)}
    print("[API] numbers_win4 … full pull then split")
    df = _read_csv_via_requests(base_url, params)
    if df.empty:
        (OUT_DIR / "numbers.csv").write_text("draw_date,session,pick,sum,booster\n")
        (OUT_DIR / "win4.csv").write_text("draw_date,session,pick,sum,booster\n")
        print("[API] numbers_win4: empty result")
        return

    # normalize columns
    df.columns = [c.strip().lower().replace("-", "_").replace(" ", "_") for c in df.columns]
    df["draw_date"] = pd.to_datetime(df.get("draw_date"), errors="coerce").dt.date.astype("string")

    # ensure expected columns exist
    for c in [
        "midday_daily","midday_daily_sum","evening_daily","evening_daily_sum",
        "midday_win_4","midday_win_4_sum","evening_win_4","evening_win_4_sum",
        "midday_daily_booster","evening_daily_booster","midday_win_4_booster","evening_win_4_booster"
    ]:
        if c not in df.columns:
            df[c] = ""

    # Build Numbers (3-digit)
    n_rows = []
    for _, r in df.iterrows():
        d = r["draw_date"]
        if not d:
            continue
        if r["midday_daily"]:
            n_rows.append((d, "midday", str(r["midday_daily"]).zfill(3), str(r["midday_daily_sum"]), str(r["midday_daily_booster"])))
        if r["evening_daily"]:
            n_rows.append((d, "evening", str(r["evening_daily"]).zfill(3), str(r["evening_daily_sum"]), str(r["evening_daily_booster"])))
    pd.DataFrame(n_rows, columns=["draw_date","session","pick","sum","booster"]).to_csv(OUT_DIR / "numbers.csv", index=False)

    # Build Win4 (4-digit)
    w_rows = []
    for _, r in df.iterrows():
        d = r["draw_date"]
        if not d:
            continue
        if r["midday_win_4"]:
            w_rows.append((d, "midday", str(r["midday_win_4"]).zfill(4), str(r["midday_win_4_sum"]), str(r["midday_win_4_booster"] or "")))
        if r["evening_win_4"]:
            w_rows.append((d, "evening", str(r["evening_win_4"]).zfill(4), str(r["evening_win_4_sum"]), str(r["evening_win_4_booster"] or "")))
    pd.DataFrame(w_rows, columns=["draw_date","session","pick","sum","booster"]).to_csv(OUT_DIR / "win4.csv", index=False)

    print(f"[API] numbers rows={len(n_rows):,} → {OUT_DIR/'numbers.csv'}")
    print(f"[API] win4 rows={len(w_rows):,} → {OUT_DIR/'win4.csv'}")

def main():
    # Set-draw (incremental)
    fetch_incremental_set("mega_millions", URLS["mega_millions"])
    fetch_incremental_set("powerball",     URLS["powerball"])
    fetch_incremental_set("take5",         URLS["take5"])
    fetch_incremental_set("cash4life",     URLS["cash4life"])
    fetch_incremental_set("ny_lotto",      URLS["ny_lotto"])

    # Daily combined → split
    fetch_numbers_win4(URLS["numbers_win4"])

if __name__ == "__main__":
    main()
