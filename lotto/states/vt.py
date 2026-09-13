"""Vermont. One table lists every game with price, tickets printed, percent sold, total
unclaimed prize value and the unclaimed counts for its top prize levels. No prize
structure is published, so the return comes straight from unclaimed value divided by
unsold tickets (compute_aggregate), with a range from the whole-percent rounding."""
from __future__ import annotations

import re

from ..fetch import get_text
from ..html import money, num, tables
from ..metrics import parse_prize_label

STATE = {
    "code": "VT",
    "name": "Vermont",
    "sources": [{"label": "vtlottery.com: Outstanding Prizes", "url": "https://vtlottery.com/games/instant-tickets/outstanding-prizes"}],
}
URL = "https://vtlottery.com/games/instant-tickets/outstanding-prizes"


def fetch_games() -> list[dict]:
    h = get_text(URL)
    rows = [r for t in tables(h) for r in t if len(r) >= 8 and r[1].strip().isdigit()]
    games = []
    for r in rows:
        price = money(r[0])
        labels = re.findall(r"\$[\d,]+(?:[^$]*?(?:LIFE|Life|/YR|/WK|Year|Week))?", r[3])
        counts = [num(x) for x in r[4].split()]
        tiers = []
        for label, left in zip(labels, counts):
            value, annuity = parse_prize_label(label.strip(), price)
            tiers.append({"label": label.strip(), "value": value, "annuity": annuity, "total": 0, "unpaid": left})
        notes = ["Vermont publishes total unclaimed prize money and percent sold rather than a prize table; the return is computed from those."]
        if num(r[6]) >= 90:
            notes.append("Nearly sold out: what is left unclaimed is mostly sold winners not yet cashed, so no estimate.")
        games.append({
            "game_number": r[1].strip(),
            "name": r[2].strip(),
            "price": price,
            "tickets_printed": num(r[7]),
            "pct_sold": num(r[6]) / 100,
            "pct_step": 0.01,
            "unclaimed_value": money(r[5]),
            "top_prize_remaining": counts[0] if counts else 0,
            "url": URL,
            "tiers": tiers,
            "notes": notes,
        })
    return games
