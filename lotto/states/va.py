"""Virginia. valottery.com's scratcher list API gives game ids, price and art; each game
page has a table of every tier (winning tickets at start, unclaimed) plus overall odds,
start date and game number."""
from __future__ import annotations

import re
from datetime import datetime

from ..fetch import fetch_many, get_json, get_text
from ..html import money, num, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "VA",
    "name": "Virginia",
    "sources": [{"label": "valottery.com: Scratchers", "url": "https://www.valottery.com/scratchers"}],
}
SITE = "https://www.valottery.com"


def _list() -> list[dict]:
    out, page, total = [], 0, 1
    while page < total:
        d = get_json(SITE + "/api/v1/scratchers", data={"page": page, "totalPages": 0, "pageSize": 50})
        out += d.get("data", [])
        total = int(d.get("totalPages") or 1)
        page += 1
    return out


def _game(rec: dict) -> dict:
    gid = str(rec["GameID"])
    url = f"{SITE}/scratchers/{gid}"
    h = get_text(url, timeout=40)
    t = text(h)
    price = money(rec.get("TicketPrice")) or money((re.search(r"Ticket Price\s*\$?([\d.]+)", t) or [None, "0"])[1])
    tiers = []
    for tb in tables(h):
        if tb and tb[0] and tb[0][0].lower().startswith("prize amount"):
            for r in tb[1:]:
                if len(r) < 3 or not r[1].strip():
                    continue
                label = r[0].replace("*", "").strip()
                value, annuity = parse_prize_label(label, price)
                total, unpaid = num(r[1]), num(r[2])
                tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
            break
    o = re.search(r"Odds of Winning Overall:?\s*(1 in [\d.,]+)", t, re.I)
    start = re.search(r"Start Date\s*(\d{1,2}/\d{1,2}/\d{4})", t)
    img = re.search(r'src="([^"]*scratcher-scratched[^"]*)"', h) or re.search(r'src="([^"]*scratcher-teaser[^"]*)"', h)
    return {
        "game_number": gid,
        "name": (rec.get("Title") or "").strip(),
        "price": price,
        "odds": float(o.group(1)[5:].replace(",", "")) if o else None,
        "odds_label": o.group(1) if o else "",
        "release_date": datetime.strptime(start.group(1), "%m/%d/%Y").date().isoformat() if start else "",
        "top_prize_label": (rec.get("TopPrize") or "").replace("*", "").strip() or None,
        "top_prize_remaining": int(rec.get("PayoutNumber") or 0),
        "image": rec.get("RolloverImageUrl") or (img.group(1) if img else None),
        "url": url,
        "tiers": tiers,
        "notes": ["Closing soon."] if rec.get("IsClosingSoon") else [],
    }


def fetch_games() -> list[dict]:
    recs = _list()
    return [g for g in fetch_many(_game, recs) if isinstance(g, dict) and g["tiers"]]
