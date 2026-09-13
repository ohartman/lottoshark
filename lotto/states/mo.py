"""Missouri. molottery.com's scratchers list page links every active game; each detail
page has a table of every tier (total, unclaimed), the price, overall odds and dates."""
from __future__ import annotations

import re
from datetime import datetime

from ..fetch import fetch_many, get_text
from ..html import money, num, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "MO",
    "name": "Missouri",
    "sources": [{"label": "molottery.com: Scratchers", "url": "https://www.molottery.com/scratchers-list.do"}],
}
SITE = "https://www.molottery.com"
LIST = SITE + "/scratchers-list.do"


def _date(s: str) -> str:
    try:
        return datetime.strptime(s.strip(), "%b %d, %Y").date().isoformat()
    except ValueError:
        return ""


def _game(num_: str) -> dict:
    url = f"{SITE}/scratchers.do?method=d&game={num_}"
    h = get_text(url, timeout=40)
    t = text(h)
    f = lambda k: (re.search(re.escape(k) + r"\*?:?\s*([A-Z][a-z]{2} \d{2}, \d{4}|\$[\d,.]+|1 in [\d.]+)", t) or [None, ""])[1]
    price = money(f("Ticket Price"))
    tiers = []
    for tb in tables(h):
        if tb and tb[0] and tb[0][0].lower().startswith("prize level"):
            for r in tb[1:]:
                if len(r) < 3 or not r[0].strip():
                    continue
                value, annuity = parse_prize_label(r[0], price)
                total, unpaid = num(r[1]), num(r[2])
                tiers.append({"label": r[0], "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
            break
    names = [text(x) for x in re.findall(r"<h1[^>]*>(.*?)</h1>", h, re.S)]
    name = next((n for n in names if n and n.lower() != "search"), "")
    o = f("Average Chances")
    end = _date(f("End Date"))
    img = re.search(r'src="([^"]*media/scratchers/[^"]*)"', h)
    return {
        "game_number": num_,
        "name": name,
        "price": price,
        "odds": float(o[5:]) if o else None,
        "odds_label": o,
        "release_date": _date(f("Official Start Date")),
        "end_date": _date(f("Expire Date")),
        "top_prize_label": f("Top Prize") or None,
        "image": (SITE + img.group(1)) if img and img.group(1).startswith("/") else (img.group(1) if img else None),
        "url": url,
        "tiers": tiers,
        "notes": ["Sales have ended; prizes can still be claimed."] if end and end < datetime.now().date().isoformat() else [],
    }


def fetch_games() -> list[dict]:
    nums = sorted(set(re.findall(r"scratchers\.do\?method=d&(?:amp;)?game=(\d+)", get_text(LIST, timeout=60))))
    return [g for g in fetch_many(_game, nums) if isinstance(g, dict) and g["tiers"]]
