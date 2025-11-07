from pathlib import Path
from typing import List
from bs4 import BeautifulSoup

from src.ingest.http_soup import get_soup, dump_raw, write_csv
from src.ingest.parsers import parse_set_draws, parse_digits_draws
from src.ingest.pages import PAGES

def _debug_counts(soup: BeautifulSoup, game_id: str):
    tables = len(soup.select("table"))
    rows = len(soup.select("table tr"))
    items = len(soup.select("ul li, ol li"))
    scripts = len(soup.find_all("script"))
    print(f"[debug:{game_id}] tables={tables} rows={rows} list_items={items} scripts={scripts}")

def scrape_mega_millions() -> Path:
    url = PAGES["mega_millions"]
    soup = get_soup(url)
    dump_raw(str(soup), "mega_millions")
    _debug_counts(soup, "mega_millions")
    rows = parse_set_draws(soup, "mega_millions")
    return write_csv(rows, "mega_millions")

def scrape_powerball() -> Path:
    url = PAGES["powerball"]
    soup = get_soup(url)
    dump_raw(str(soup), "powerball")
    _debug_counts(soup, "powerball")
    rows = parse_set_draws(soup, "powerball")
    return write_csv(rows, "powerball")

def scrape_take5() -> Path:
    url = PAGES["take5"]
    soup = get_soup(url)
    dump_raw(str(soup), "take5")
    _debug_counts(soup, "take5")
    rows = parse_set_draws(soup, "take5")
    return write_csv(rows, "take5")

def scrape_cash4life() -> Path:
    url = PAGES["cash4life"]
    soup = get_soup(url)
    dump_raw(str(soup), "cash4life")
    _debug_counts(soup, "cash4life")
    rows = parse_set_draws(soup, "cash4life")
    return write_csv(rows, "cash4life")

def scrape_ny_lotto() -> Path:
    url = PAGES["ny_lotto"]
    soup = get_soup(url)
    dump_raw(str(soup), "ny_lotto")
    _debug_counts(soup, "ny_lotto")
    rows = parse_set_draws(soup, "ny_lotto")
    return write_csv(rows, "ny_lotto")

def scrape_numbers() -> Path:
    url = PAGES["numbers"]
    soup = get_soup(url)
    dump_raw(str(soup), "numbers")
    _debug_counts(soup, "numbers")
    rows = parse_digits_draws(soup, "numbers")
    return write_csv(rows, "numbers")

def scrape_win4() -> Path:
    url = PAGES["win4"]
    soup = get_soup(url)
    dump_raw(str(soup), "win4")
    _debug_counts(soup, "win4")
    rows = parse_digits_draws(soup, "win4")
    return write_csv(rows, "win4")

def scrape_all() -> List[Path]:
    return [
        scrape_mega_millions(),
        scrape_powerball(),
        scrape_take5(),
        scrape_cash4life(),
        scrape_ny_lotto(),
        scrape_numbers(),
        scrape_win4(),
    ]

if __name__ == "__main__":
    for p in scrape_all():
        print("wrote:", p)