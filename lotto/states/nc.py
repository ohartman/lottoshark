"""North Carolina. nclottery.com/scratch-off-prizes-remaining is one server-rendered page
with a table per game: value, odds, total, remaining for every tier, plus price, game
number, name and thumbnail. Overall odds are derived from the print run implied by the
biggest tier's odds."""
from __future__ import annotations

import re

from ..fetch import get_text
from ..html import money, num, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "NC",
    "name": "North Carolina",
    "sources": [{"label": "nclottery.com: Scratch-Off Prizes Remaining", "url": "https://nclottery.com/scratch-off-prizes-remaining"}],
}
URL = "https://nclottery.com/scratch-off-prizes-remaining"
BASE = "https://nclottery.com"


def fetch_games() -> list[dict]:
    html = get_text(URL, timeout=90)
    games = []
    for m in re.finditer(r'<div class="box cloudfx databox price_(\d+)">(.*?)(?=<div class="box cloudfx databox|$)', html, re.S):
        price, b = float(m.group(1)), m.group(2)
        name_m = re.search(r'<span class="gamename"><a href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
        gnum = re.search(r"Game Number:</b>\s*(\d+)", b)
        thumb = re.search(r'<span class="gamethumb"><a href="([^"]+)"', b)
        if not gnum:
            continue
        tiers, tickets = [], None
        for t in tables(b):
            for r in t:
                if len(r) < 4 or not r[0].startswith("$"):
                    continue
                value, annuity = parse_prize_label(r[0], price)
                total, unpaid, tier_odds = num(r[2]), num(r[3]), money(r[1])
                if total and tier_odds and (tickets is None or total > tickets[0]):
                    tickets = (total, round(total * tier_odds))
                tiers.append({"label": r[0], "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        games.append({
            "game_number": gnum.group(1),
            "name": text(name_m.group(2)) if name_m else "",
            "price": price,
            "tickets_printed": tickets[1] if tickets else None,
            "image": BASE + thumb.group(1) if thumb else None,
            "url": BASE + name_m.group(1) if name_m else URL,
            "tiers": tiers,
            "notes": ["Reordered: more tickets were printed after launch."] if "Reordered" in b else [],
        })
    return games
