"""Texas.

  1. scratchoff.csv: every game, every prize level, printed and claimed. Refreshed daily.
  2. all.html: game number -> detail page link and start date.
  3. One detail page per game for the overall odds and the ticket image.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime

from ..fetch import fetch_many, get_text
from ..html import attr_all, odds, tables
from ..metrics import parse_prize_label

STATE = {
    "code": "TX",
    "name": "Texas",
    "sources": [
        {"label": "texaslottery.com: Scratch Ticket Prizes Remaining (CSV)",
         "url": "https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/scratchoff.csv"},
        {"label": "texaslottery.com: Scratch Tickets", "url": "https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/all.html"},
    ],
}
BASE = "https://www.texaslottery.com"
CSV_URL = BASE + "/export/sites/lottery/Games/Scratch_Offs/scratchoff.csv"
ALL_URL = BASE + "/export/sites/lottery/Games/Scratch_Offs/all.html"


def _date(s: str) -> str:
    for fmt in ("%m/%d/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return ""


def _detail(link: str) -> dict:
    h = get_text(BASE + link, timeout=40)
    m = re.search(r"Game No\.\s*(\d+)", h)
    img = next((s for s in attr_all(h, "img", "src") if "/Images/scratchoffs/" in s), None)
    o = re.search(r"Overall odds of winning any prize[^<]*?are\s*(1 in [\d.]+)", h, re.I)
    printed = re.search(r"approximately\s*([\d,]+)\*?\s*tickets", h, re.I)
    return {
        "game_number": m.group(1) if m else "",
        "odds_label": o.group(1) if o else "",
        "image": BASE + img if img else None,
        "tickets_printed": int(printed.group(1).replace(",", "")) if printed else None,
    }


def fetch_games() -> list[dict]:
    raw = get_text(CSV_URL)
    lines = raw.splitlines()
    as_of = lines[0]
    rows = list(csv.DictReader(io.StringIO("\n".join(lines[1:]))))

    # all.html: link + start date per game (first row of each game block carries them)
    all_html = get_text(ALL_URL)
    links = {m.group(2): m.group(1) for m in re.finditer(r'href="([^"]*details\.html_\d+\.html)">\s*(\d+)\s*<', all_html)}
    starts: dict[str, str] = {}
    for t in tables(all_html):
        for r in t:
            if len(r) >= 3 and r[0].isdigit():
                starts[r[0]] = _date(r[1])

    details = {d["game_number"]: d for d in fetch_many(_detail, list(links.values())) if isinstance(d, dict) and d["game_number"]}

    games: dict[str, dict] = {}
    for r in rows:
        num = r["Game Number"].strip()
        level = r["Prize Level"].strip()
        if not num or level.upper() == "TOTAL":
            continue
        price = float(r["Ticket Price"] or 0)
        g = games.setdefault(num, {
            "game_number": num, "name": r["Game Name"].strip(), "price": price,
            "end_date": _date(r["Game Close Date"]) if r["Game Close Date"].strip() else "",
            "release_date": starts.get(num, ""), "tiers": [], "notes": [],
            "url": BASE + links[num] if num in links else ALL_URL,
        })
        label = f"${int(float(level)):,}" if re.fullmatch(r"[\d.]+", level) else level
        value, annuity = parse_prize_label(label, price)
        total, claimed = int(r["Total Prizes in Level"] or 0), int(r["Prizes Claimed"] or 0)
        g["tiers"].append({"label": label, "value": value, "annuity": annuity, "total": total, "paid": claimed, "unpaid": max(total - claimed, 0)})

    for num, g in games.items():
        d = details.get(num)
        if d:
            g["odds_label"] = d["odds_label"]
            g["odds"] = odds(d["odds_label"])
            g["image"] = d["image"]
            if d["tickets_printed"]:
                g["tickets_printed"] = d["tickets_printed"]
        else:
            g["notes"].append("Not on the Texas Lottery active game list (likely off sale); odds unknown.")
        if g["end_date"]:
            g["notes"].append(f"Closing; last day to claim {g['end_date']}.")
    return list(games.values())
