"""
scrape_latest.py — use Playwright + BeautifulSoup to scrape the latest draw
from the NY Lottery site (client-rendered).

What this version does:
- Normalizes dates to YYYY-MM-DD
- For Numbers/Win4: extracts BOTH sessions (midday & evening) if present,
  returning rows like {game_id, draw_date, session, pick, scraped_at}
- For set-draw games: extracts the latest draw
  {game_id, draw_date, numbers, bonus?, scraped_at}
- De-dupes by (draw_date, session) for Numbers/Win4; by draw_date for others
- Prints DEBUG lines so you can see what was parsed
"""

import re
import datetime as dt
from pathlib import Path
import importlib

import pandas as pd
from bs4 import BeautifulSoup

# Optional import for Playwright with a helpful error if not installed
try:
    _pw = importlib.import_module("playwright.sync_api")
    sync_playwright = _pw.sync_playwright
except Exception:
    def sync_playwright(*args, **kwargs):
        raise RuntimeError(
            "playwright is not installed or could not be imported. "
            "Install with: pip install playwright && playwright install"
        )

from src.ingest.pages import PAGES

OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Match human-formatted dates like "Nov 5, 2025"
DATE_RX = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b",
    re.I,
)


def fetch_rendered_html(url: str) -> str:
    """Open a page with JS execution and return the final HTML."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60_000)
        page.wait_for_load_state("networkidle")
        html = page.content()
        browser.close()
        return html


def _extract_digits_near(label: str, text: str, pad_len: int) -> str | None:
    """
    Try to find digits near a session label (e.g., 'Midday', 'Evening').
    If not found, fall back to the last digits on the page.
    """
    m = re.search(rf"{label}\W*([0-9][0-9\W]{{0,12}})", text, flags=re.I)
    digits = "".join(ch for ch in (m.group(1) if m else "") if ch.isdigit())
    if not digits:
        digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    return digits[-pad_len:].zfill(pad_len)


def extract_latest_draw(soup: BeautifulSoup, game_id: str):
    """
    Parse the most recent draw(s) from the rendered HTML.

    Returns:
      - For Numbers/Win4: list[dict] with up to two rows (midday, evening)
      - For set-draw games: a single dict (latest only)
      - None if nothing parseable was found
    """
    text = " ".join(soup.get_text(" ").split())
    tlow = text.lower()

    # Find a human-readable date and convert to ISO
    mdate = DATE_RX.search(text)
    if not mdate:
        return None
    try:
        date_iso = pd.to_datetime(mdate.group(0)).date().isoformat()
    except Exception:
        return None

    # Daily games: Numbers (3-digit) and Win4 (4-digit) with sessions
    if game_id in {"numbers", "win4"}:
        rows = []
        pad_len = 3 if game_id == "numbers" else 4
        for sess_label in ("Midday", "Evening"):
            pick = _extract_digits_near(sess_label, text, pad_len=pad_len)
            if not pick:
                continue
            rows.append({
                "game_id": game_id,
                "draw_date": date_iso,
                "session": sess_label.lower(),
                "pick": pick,
                "scraped_at": dt.datetime.utcnow().isoformat(),
            })
        return rows or None

    # Set-draw games (Mega/Powerball/Take5/Cash4Life/NY Lotto) — latest only
    nums = re.findall(r"\b\d{1,2}\b", text)[:7]  # enough to capture 5..6 + bonus if present
    bonus = None
    if "bonus" in tlow or "mega" in tlow or "powerball" in tlow:
        if len(nums) >= 6:
            bonus = nums[-1]
            nums = nums[:-1]

    if nums:
        return {
            "game_id": game_id,
            "draw_date": date_iso,
            "numbers": ",".join(nums),
            "bonus": bonus,
            "scraped_at": dt.datetime.utcnow().isoformat(),
        }
    return None


def update_csv(row: dict, csvfile: Path):
    """
    Append 'row' to 'csvfile' unless it's already present.
    Numbers/Win4: de-dupe by (draw_date, session)
    Other games  : de-dupe by draw_date
    """
    df = pd.read_csv(csvfile) if csvfile.exists() and csvfile.stat().st_size > 0 else pd.DataFrame()

    if row["game_id"] in {"numbers", "win4"}:
        if not df.empty and {"draw_date", "session"}.issubset(df.columns):
            mask = (df["draw_date"].astype(str) == str(row["draw_date"])) & \
                   (df["session"].astype(str) == str(row.get("session")))
            if mask.any():
                print(f"[SKIP] {row['game_id']} already has {row['draw_date']} ({row.get('session')})")
                return
    else:
        if not df.empty and "draw_date" in df.columns:
            if str(row["draw_date"]) in df["draw_date"].astype(str).values:
                print(f"[SKIP] {row['game_id']} already has {row['draw_date']}")
                return

    pd.concat([pd.DataFrame([row]), df], ignore_index=True).to_csv(csvfile, index=False)
    if row["game_id"] in {"numbers", "win4"}:
        print(f"[ADD] {row['game_id']} {row['draw_date']} ({row.get('session')})")
    else:
        print(f"[ADD] {row['game_id']} {row['draw_date']}")


def scrape_latest_all():
    for gid, url in PAGES.items():
        try:
            print(f"\n[scraping latest] {gid}")
            html = fetch_rendered_html(url)
            soup = BeautifulSoup(html, "html.parser")
            res = extract_latest_draw(soup, gid)
            if not res:
                print(f"[WARN] could not extract draw for {gid}")
                continue

            # Normalize return type to a list for uniform handling
            rows = res if isinstance(res, list) else [res]
            for row in rows:
                print(f"[DEBUG] parsed -> {row}")
                csvfile = OUT_DIR / f"{gid}.csv"
                update_csv(row, csvfile)

        except Exception as e:
            print(f"[ERR] {gid}: {e}")


if __name__ == "__main__":
    scrape_latest_all()
