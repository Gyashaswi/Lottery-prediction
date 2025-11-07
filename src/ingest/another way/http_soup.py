import time, datetime as dt
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)

HDRS = {
    "User-Agent": "Mozilla/5.0 (compatible; LotteryScraper/1.0; +https://example.com)",
    "Accept-Language": "en-US,en;q=0.9",
}

def _fetch(url: str) -> Optional[str]:
    r = requests.get(url, headers=HDRS, timeout=30)
    if r.status_code == 200 and r.text and r.text.strip():
        return r.text
    return None

def get_soup(url: str, retries: int = 2, sleep_sec: float = 1.0) -> BeautifulSoup:
    """
    Try the page, then a couple of static fallbacks commonly present on CMS sites:
    - AMP version (?amp or /amp)
    - Print view (?print=1)
    """
    tried = []
    candidates = [url]

    # basic AMP variations
    if "?" in url:
        candidates += [url + "&amp", url + "&print=1"]
    else:
        candidates += [url + "?amp", url + "?print=1"]
    # some sites support /amp
    if not url.endswith("/"):
        candidates.append(url + "/amp")
    else:
        candidates.append(url + "amp")

    for cand in candidates:
        tried.append(cand)
        for i in range(retries):
            html = _fetch(cand)
            if html:
                return BeautifulSoup(html, "html.parser")
            time.sleep(sleep_sec * (i + 1))

    # last attempt: raise with context
    raise RuntimeError(f"Failed to fetch after trying: {tried}")

def dump_raw(html: str, game_id: str, suffix: str = "") -> Path:
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    name = f"{game_id}{('_' + suffix) if suffix else ''}_{ts}.html"
    path = RAW_DIR / name
    path.write_text(html, encoding="utf-8")
    return path

def write_csv(rows: List[Dict[str, Any]], game_id: str, suffix: str = "") -> Path:
    import csv
    fname = f"{game_id}{('_' + suffix) if suffix else ''}.csv"
    path = PROC_DIR / fname

    if not rows:
        # do not overwrite existing non-empty file with empty content
        if path.exists() and path.stat().st_size > 0:
            print(f"[skip-empty] {game_id}: parser returned 0 rows, keeping existing {path.name}")
            return path
        # create an empty file with a minimal header so downstream code doesn't crash
        with path.open("w", newline="", encoding="utf-8") as f:
            f.write("")
        print(f"[empty] {game_id}: wrote empty CSV (no rows parsed)")
        return path

    headers = sorted({k for r in rows for k in r.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"[ok] {game_id}: wrote {len(rows)} rows")
    return path