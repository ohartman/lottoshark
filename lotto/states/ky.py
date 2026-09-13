"""Kentucky. One page lists every game on sale with price, odds, dates, art and a table
of prizes remaining for every level, but no printed counts. Tickets unsold are taken as
prizes remaining times the overall odds (compute_remaining_only)."""
from __future__ import annotations

import re
from datetime import datetime

from ..fetch import get_text
from ..html import money, num, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "KY",
    "name": "Kentucky",
    "sources": [{"label": "kylottery.com: Scratch-offs available", "url": "https://www.kylottery.com/apps/scratch_offs/available_games.html"}],
}
URL = "https://www.kylottery.com/apps/scratch_offs/available_games.html"
SITE = "https://www.kylottery.com"


def _date(s: str) -> str:
    try:
        return datetime.strptime(s.strip(), "%B %d, %Y").date().isoformat()
    except ValueError:
        return ""


def fetch_games() -> list[dict]:
    h = get_text(URL, timeout=90)
    blocks = re.split(r'(?=<h4 class="panel-title")', h)[1:]
    games = []
    for b in blocks:
        title = re.search(r'<h4 class="panel-title"[^>]*>(.*?)</h4>', b, re.S)
        m = re.match(r"(.*)\s+-\s+(\d+)\s*$", text(title.group(1)) if title else "")
        if not m:
            continue
        name, n = m.group(1).strip(), m.group(2)
        t = text(b)
        f = lambda k: (re.search(re.escape(k) + r":?\s*([^\n]{0,30}?)(?:\s{2,}|\s(?:Game|Last|Value|Top|Overall|Prizes)\b|$)", t) or [None, ""])[1].strip()
        price = money(f("Value"))
        o = re.search(r"Overall Odds:?\s*1\s*[:in]+\s*([\d.]+)", t)
        img = re.search(r'src="([^"]*KYLottery_ScratchOffs[^"]*)"', b)
        tiers = []
        for tb in tables(b):
            rows = [(x[0].strip(), num(x[1])) for x in tb if len(x) >= 2 and x[0].strip().startswith("$")]
            if rows:
                for label, left in rows:
                    value, annuity = parse_prize_label(label, price)
                    tiers.append({"label": label, "value": value, "annuity": annuity, "total": 0, "unpaid": left})
                break
        games.append({
            "game_number": n,
            "name": name,
            "price": price,
            "odds": float(o.group(1)) if o else None,
            "odds_label": f"1 in {o.group(1)}" if o else "",
            "release_date": _date(f("Start Date")),
            "end_date": _date(f("Last Date to Claim")),
            "image": (SITE + img.group(1)) if img and img.group(1).startswith("/") else (img.group(1) if img else None),
            "url": URL,
            "tiers": tiers,
            "notes": ["Kentucky publishes remaining counts for every prize but not how many were printed."],
        })
    return games
