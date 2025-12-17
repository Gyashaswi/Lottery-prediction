# src/ingest/clean_data.py
from pathlib import Path
import re
import pandas as pd
from datetime import datetime, UTC

PROC = Path("data/processed")
CLEAN = Path("data/clean")
CLEAN.mkdir(parents=True, exist_ok=True)

NOW = datetime.now(UTC).isoformat()

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower().replace("-", "_").replace(" ", "_") for c in df.columns]
    return df

def _norm_date(s):
    return pd.to_datetime(s, errors="coerce").dt.date.astype("string")

def _split_nums(s: str) -> list[int] | None:
    """Return list of ints found in string regardless of separators."""
    if pd.isna(s):
        return None
    # handle multiple spaces or hyphens, commas, NBSPs
    s = str(s).replace("\xa0", " ")
    toks = re.findall(r"\d+", s)
    if not toks:
        return None
    try:
        return [int(t) for t in toks]
    except Exception:
        return None

def _canon_join(nums: list[int]) -> str:
    return ",".join(map(str, sorted(nums)))

def _digits_only(s: str) -> str:
    return "".join(ch for ch in ("" if s is None else str(s)) if ch.isdigit())

def _save_set(game: str, df_out: pd.DataFrame):
    out = CLEAN / f"{game}.csv"
    cols = ["draw_date","numbers","bonus"]
    (pd.DataFrame(columns=cols) if df_out.empty else df_out[cols]).to_csv(out, index=False)
    print(f"[clean] {game}: out={len(df_out):,} → {out}")

def _save_daily(game: str, df_out: pd.DataFrame):
    out = CLEAN / f"{game}.csv"
    cols = ["draw_date","session","pick","sum","booster"]
    (pd.DataFrame(columns=cols) if df_out.empty else df_out[cols]).to_csv(out, index=False)
    print(f"[clean] {game}: out={len(df_out):,} → {out}")

# ---------- Set-draw cleaning ----------
def _clean_set_draw(game: str, need_main: int, bonus_col: str | None):
    src = PROC / f"{game}.csv"
    if not src.exists() or src.stat().st_size == 0:
        _save_set(game, pd.DataFrame()); return

    df = pd.read_csv(src, dtype=str)
    df = _norm_cols(df)
    df["draw_date"] = _norm_date(df.get("draw_date"))

    # pick the right column
    wn_col = next(
        (c for c in df.columns
         if "winning_numbers" in c or ("winning" in c and "number" in c) or c == "numbers"),
        None
    )
    if wn_col is None:
        print(f"[warn] {game}: no winning_numbers column found → cols={list(df.columns)[:8]}")
        _save_set(game, pd.DataFrame()); return

    df["nums_list"] = df[wn_col].apply(_split_nums)
    df = df[df["nums_list"].notna()]
    # For Powerball: sometimes it’s 6 tokens (5 main + 1 powerball)
    df["main"] = df["nums_list"].apply(lambda xs: xs[:need_main])
    df["numbers"] = df["main"].apply(_canon_join)

    if bonus_col and bonus_col in df.columns:
        df["bonus"] = df[bonus_col].astype(str)
    else:
        df["bonus"] = df["nums_list"].apply(lambda xs: str(xs[-1]) if len(xs) > need_main else "")

    out = (
        df[["draw_date","numbers","bonus"]]
        .dropna(subset=["draw_date"])
        .drop_duplicates(subset=["draw_date"])
    )
    _save_set(game, out)

def clean_megamillions(): _clean_set_draw("mega_millions", 5, "mega_ball")
def clean_powerball():    _clean_set_draw("powerball", 5, "powerball")
def clean_take5():        _clean_set_draw("take5", 5, None)
def clean_cash4life():    _clean_set_draw("cash4life", 5, "cash_ball")
def clean_nylotto():      _clean_set_draw("ny_lotto", 6, None)

# ---------- Daily games ----------
def clean_daily(game: str, pad_len: int):
    src = PROC / f"{game}.csv"
    if not src.exists() or src.stat().st_size == 0:
        _save_daily(game, pd.DataFrame()); return

    df = pd.read_csv(src, dtype=str)
    df = _norm_cols(df)

    for col in ("draw_date","session","pick"):
        if col not in df.columns: df[col] = ""

    df["draw_date"] = _norm_date(df.get("draw_date"))
    df["session"] = df["session"].astype(str).str.strip().str.lower()
    df = df[df["session"].isin(["midday","evening"])]

    # Zero-pad: ensures "99"→"099", "999"→"0999"
    df["pick"] = df["pick"].astype(str).apply(_digits_only).apply(lambda x: x.zfill(pad_len))
    df = df[df["pick"].str.len() == pad_len]

    for extra in ("sum","booster"):
        if extra not in df.columns: df[extra] = ""
        else: df[extra] = df[extra].astype(str).str.strip()

    out = (
        df[["draw_date","session","pick","sum","booster"]]
        .dropna(subset=["draw_date"])
        .drop_duplicates(subset=["draw_date","session"])
    )
    _save_daily(game, out)

def main():
    clean_megamillions()
    clean_powerball()
    clean_take5()
    clean_cash4life()
    clean_nylotto()
    clean_daily("numbers", pad_len=3)
    clean_daily("win4", pad_len=4)

if __name__ == "__main__":
    main()
