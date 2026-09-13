"""New Mexico. nmlottery.com/games/scratchers/ is one server-rendered page with a block
per game: price, game number, start date, overall odds, art, and a table of every tier
(prize, odds, printed, remaining)."""
from __future__ import annotations

import re
from datetime import datetime

from ..fetch import get_text
from ..html import money, num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "NM",
    "name": "New Mexico",
    "sources": [{"label": "nmlottery.com: Scratchers", "url": "https://www.nmlottery.com/games/scratchers/"}],
}
URL = "https://www.nmlottery.com/games/scratchers/"


def _p(block: str, cls: str) -> str:
    m = re.search(rf'<p class="{cls}"[^>]*>(.*?)</p>', block, re.S)
    return text(m.group(1)) if m else ""


def fetch_games() -> list[dict]:
    html = get_text(URL)
    blocks = re.split(r'(?=<p class="top-prize")', html)
    games = []
    for b in blocks:
        gnum = re.sub(r"\D", "", _p(b, "game-number"))
        if not gnum:
            continue
        b = b.split('<p class="top-prize"', 2)[0] + b.split('<p class="top-prize"', 2)[1] if b.count('<p class="top-prize"') > 1 else b
        price = money(_p(b, "price"))
        name_m = re.search(r"<h3[^>]*>(.*?)</h3>", b, re.S)
        start = _p(b, "start-date").replace("Start Date:", "").strip()
        try:
            release = datetime.strptime(start, "%B %d, %Y").date().isoformat()
        except ValueError:
            release = ""
        o = re.search(r"overall odds of winning[^:]*:\s*(1 in [\d.,]+)", b, re.I)
        img = re.search(r'scratcher-image.*?<img[^>]+src="([^"]+)"', b, re.S)
        tiers, tickets = [], None
        for t in tables(b):
            if not t or not any(r and r[0].startswith("$") for r in t):
                continue
            for r in t:
                if len(r) < 4 or not r[0].startswith("$"):
                    continue
                value, annuity = parse_prize_label(r[0], price)
                total, unpaid = num(r[2]), num(r[3])
                tier_odds = money(r[1])
                if total and tier_odds and (tickets is None or total > tickets[0]):
                    tickets = (total, round(total * tier_odds))
                tiers.append({"label": r[0].replace(".00", ""), "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
            break
        games.append({
            "game_number": gnum,
            "name": text(name_m.group(1)) if name_m else "",
            "price": price,
            "odds": odds(o.group(1)) if o else None,
            "odds_label": o.group(1) if o else "",
            "tickets_printed": tickets[1] if tickets else None,
            "release_date": release,
            "image": img.group(1) if img else None,
            "url": URL,
            "tiers": tiers,
            "notes": [],
        })
    return games
