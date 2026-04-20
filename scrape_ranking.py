import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import bs4
import requests

URL = "https://finance.naver.com/sise/lastsearch2.naver"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}
KST = ZoneInfo("Asia/Seoul")
COLUMNS = ["scraped_at_kst", "rank", "name", "code", "search_ratio", "price",
           "change", "change_pct", "volume", "open", "high", "low", "per", "roe"]


def scrape():
    now = datetime.now(KST)
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "euc-kr"

    soup = bs4.BeautifulSoup(resp.text, "html.parser")
    table = soup.select_one("table.type_5")
    if table is None:
        raise RuntimeError("lastsearch2 table not found — page layout may have changed")

    ts = now.isoformat(timespec="seconds")
    rows = []
    for tr in table.select("tr"):
        anchor = tr.select_one("a.tltle")
        if anchor is None:
            continue
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        code = anchor.get("href", "").split("code=")[-1]

        def c(i):
            return cells[i] if i < len(cells) else ""

        rank_text = c(0)
        rows.append({
            "scraped_at_kst": ts,
            "rank": int(rank_text) if rank_text.isdigit() else None,
            "name": anchor.get_text(strip=True),
            "code": code,
            "search_ratio": c(2), "price": c(3), "change": c(4),
            "change_pct": c(5), "volume": c(6), "open": c(7),
            "high": c(8), "low": c(9), "per": c(10), "roe": c(11),
        })

    if not rows:
        raise RuntimeError("no stock rows parsed")

    os.makedirs("data", exist_ok=True)
    out = f"data/{now.strftime('%Y-%m-%d')}.csv"
    write_header = not os.path.exists(out)
    with open(out, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if write_header:
            w.writeheader()
        w.writerows(rows)
    print(f"appended {len(rows)} rows to {out} at {ts}")


if __name__ == "__main__":
    scrape()
