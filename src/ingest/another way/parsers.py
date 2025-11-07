import re, json, datetime as dt
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

DATE_RX = re.compile(
    r"(\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4})",
    re.I,
)
NUM_GROUP_RX = re.compile(r"(?:\b\d{1,2}\b[\s,]+){2,7}\b\d{1,2}\b")
DIGITS_RX = re.compile(r"\b\d{3,4}\b")

def _clean_date(s: str) -> Optional[str]:
    m = DATE_RX.search(s)
    if not m:
        return None
    raw = m.group(1)
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return dt.datetime.strptime(raw, fmt).date().isoformat()
        except Exception:
            continue
    return None

def _log_fallback(game_id: str, reason: str, count: int) -> None:
    print(f"[parse:{game_id}] {reason} -> rows={count}")

def _script_json_candidates(soup: BeautifulSoup) -> List[dict]:
    """Look for JSON blobs embedded in <script> tags that may contain results."""
    blobs = []
    for s in soup.find_all("script"):
        t = (s.string or s.text or "").strip()
        if not t:
            continue
        if "winning" in t.lower() or "results" in t.lower():
            # try JSON loads on the largest bracketed object
            try:
                # crude heuristic: find the first {...} or [...] big chunk
                m = re.search(r"(\{.*\}|\[.*\])", t, re.S)
                if m:
                    candidate = json.loads(m.group(1))
                    blobs.append(candidate)
            except Exception:
                continue
    return blobs

def parse_set_draws(soup: BeautifulSoup, game_id: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    # 1) Target common server-rendered structures first
    selectors = [
        "table tbody tr",
        "table tr",
        "ul.past-winning-numbers li",
        "section.past-winning-numbers li",
        "article",
        "div.card, div.teaser, div.result, li",
    ]
    for sel in selectors:
        for node in soup.select(sel):
            text = " ".join(node.get_text(" ").split())
            if not text:
                continue
            d = _clean_date(text)
            mg = NUM_GROUP_RX.search(text)
            if not (d and mg):
                continue
            seq = [int(x) for x in re.findall(r"\b\d{1,2}\b", mg.group(0))]
            bonus = None
            label_text = text.lower()
            if any(lbl in label_text for lbl in ["mega ball", "powerball", "cash ball", "bonus"]):
                if len(seq) >= 6:
                    bonus = seq[-1]
                    seq = seq[:-1]
            if 3 <= len(seq) <= 6:
                rows.append({
                    "game_id": game_id,
                    "draw_date": d,
                    "numbers": ",".join(map(str, seq)),
                    "bonus": bonus,
                    "raw_text": text[:300],
                })
    if rows:
        _log_fallback(game_id, "DOM selectors", len(rows))
        # de-dup
        uniq = {(r["draw_date"], r["numbers"]): r for r in rows}
        return list(uniq.values())

    # 2) Script/JSON fallback (some Drupal/React sites hydrate via JSON)
    blobs = _script_json_candidates(soup)
    for b in blobs:
        try:
            # try a few common structures
            items = []
            if isinstance(b, dict):
                for k, v in b.items():
                    if isinstance(v, list):
                        items.extend(v)
            elif isinstance(b, list):
                items = b
            for it in items:
                txt = json.dumps(it, ensure_ascii=False)
                d = _clean_date(txt)
                nums = [int(x) for x in re.findall(r"\b\d{1,2}\b", txt)]
                bonus = None
                if "mega" in txt.lower() or "powerball" in txt.lower() or "cash ball" in txt.lower() or "bonus" in txt.lower():
                    if len(nums) >= 6:
                        bonus = nums[-1]
                        nums = nums[:-1]
                if d and 3 <= len(nums) <= 6:
                    rows.append({
                        "game_id": game_id,
                        "draw_date": d,
                        "numbers": ",".join(map(str, nums)),
                        "bonus": bonus,
                        "raw_text": txt[:300],
                    })
        except Exception:
            continue
    _log_fallback(game_id, "script JSON", len(rows))
    uniq = {(r["draw_date"], r["numbers"]): r for r in rows}
    return list(uniq.values())

def parse_digits_draws(soup: BeautifulSoup, game_id: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    selectors = [
        "table tbody tr",
        "table tr",
        "ul.past-winning-numbers li",
        "section.past-winning-numbers li",
        "article",
        "div.card, div.teaser, div.result, li",
    ]
    for sel in selectors:
        for node in soup.select(sel):
            text = " ".join(node.get_text(" ").split())
            if not text:
                continue
            d = _clean_date(text)
            if not d:
                continue
            picks = [p for p in re.findall(r"\b\d{3,4}\b", text) if len(p) in (3,4)]
            if not picks:
                continue
            when = None
            lt = text.lower()
            if "midday" in lt: when = "midday"
            elif "evening" in lt: when = "evening"
            for p in picks:
                rows.append({
                    "game_id": game_id,
                    "draw_date": d,
                    "pick": p,
                    "session": when,
                    "raw_text": text[:300],
                })
    if rows:
        _log_fallback(game_id, "DOM selectors", len(rows))
        uniq = {(r["draw_date"], r["pick"], r.get("session")): r for r in rows}
        return list(uniq.values())

    blobs = _script_json_candidates(soup)
    for b in blobs:
        try:
            items = []
            if isinstance(b, dict):
                for k, v in b.items():
                    if isinstance(v, list):
                        items.extend(v)
            elif isinstance(b, list):
                items = b
            for it in items:
                txt = json.dumps(it, ensure_ascii=False)
                d = _clean_date(txt)
                picks = [p for p in re.findall(r"\b\d{3,4}\b", txt) if len(p) in (3,4)]
                if not (d and picks):
                    continue
                when = None
                lt = txt.lower()
                if "midday" in lt: when = "midday"
                elif "evening" in lt: when = "evening"
                for p in picks:
                    rows.append({
                        "game_id": game_id,
                        "draw_date": d,
                        "pick": p,
                        "session": when,
                        "raw_text": txt[:300],
                    })
        except Exception:
            continue
    _log_fallback(game_id, "script JSON", len(rows))
    uniq = {(r["draw_date"], r["pick"], r.get("session")): r for r in rows}
    return list(uniq.values())