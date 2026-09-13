"""Iowa. One page lists claimed and unclaimed counts for every prize of $50 and up; each
game's detail page lists the odds of every prize level and the overall odds. Printed
counts for the small prizes are reconstructed from their odds and the print run implied
by the published tiers; their remaining counts are estimated (see lotto/metrics.py)."""
from __future__ import annotations

import re
from datetime import datetime

from ..fetch import fetch_many, get_text
from ..html import money, num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "IA",
    "name": "Iowa",
    "sources": [{"label": "ialottery.com: Remaining Prizes", "url": "https://ialottery.com/Pages/Games/RemainingPrizes.aspx"}],
}
SITE = "https://ialottery.com"
REMAINING = SITE + "/Pages/Games/RemainingPrizes.aspx"
DETAIL = SITE + "/Pages/Games-Scratch/ScratchGamesDetail.aspx?g={n}"


def _detail(n: str) -> dict:
    h = get_text(DETAIL.format(n=n), timeout=40)
    t = text(h)
    tier_odds = {}
    for tb in tables(h):
        if tb and tb[0] and tb[0][0].lower().startswith("prize"):
            for r in tb[1:]:
                if len(r) >= 2 and r[0].startswith("$") and odds(r[1]):
                    tier_odds[r[0].strip()] = odds(r[1])
            break
    o = re.search(r"Overall Odds[^\d]*(1 in [\d.]+)", t)
    start = re.search(r"Game Start:?\s*(\d{1,2}/\d{1,2}/\d{4})", t)
    end = re.search(r"Last Day To Redeem[^\d]*(\d{1,2}/\d{1,2}/\d{4})", t, re.I)
    fmt = lambda m: datetime.strptime(m.group(1), "%m/%d/%Y").date().isoformat() if m else ""
    return {"tier_odds": tier_odds, "odds_label": o.group(1) if o else "", "release_date": fmt(start), "end_date": fmt(end)}


def fetch_games() -> list[dict]:
    h = get_text(REMAINING, timeout=90)
    rows = [r for tb in tables(h) for r in tb if len(r) >= 6 and r[1].strip().lower() == "scratch"]
    games: dict[str, dict] = {}
    for r in rows:
        m = re.match(r"(.*)\((\d+)\)\s*$", r[0].strip())
        if not m:
            continue
        name, n = m.group(1).strip(), m.group(2)
        g = games.setdefault(n, {"game_number": n, "name": name, "price": money(r[2]), "known": {}})
        label = "$" + f"{money(r[3]):,.0f}"
        g["known"][label] = (num(r[4]) + num(r[5]), num(r[5]))
    details = dict(zip(games, fetch_many(lambda n: _detail(n), list(games))))
    out = []
    for n, g in games.items():
        d = details.get(n)
        d = d if isinstance(d, dict) else {"tier_odds": {}, "odds_label": "", "release_date": "", "end_date": ""}
        price = g["price"]
        # print run implied by the largest published tier: printed x odds
        tickets = None
        for label, (total, _) in g["known"].items():
            if label in d["tier_odds"] and total and (tickets is None or total > tickets[0]):
                tickets = (total, total * d["tier_odds"][label])
        tiers = []
        seen = set()
        for label, tier_odds in d["tier_odds"].items():
            key = "$" + f"{money(label):,.0f}"
            seen.add(key)
            value, annuity = parse_prize_label(label, price)
            if key in g["known"]:
                total, unpaid = g["known"][key]
            else:
                total, unpaid = (round(tickets[1] / tier_odds) if tickets else 0), None
            tiers.append({"label": key, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid})
        for key, (total, unpaid) in g["known"].items():
            if key not in seen:
                value, annuity = parse_prize_label(key, price)
                tiers.append({"label": key, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid})
        out.append({
            "game_number": n,
            "name": g["name"],
            "price": price,
            "odds": odds(d["odds_label"]),
            "odds_label": d["odds_label"],
            "release_date": d["release_date"],
            "end_date": d["end_date"],
            "url": DETAIL.format(n=n),
            "tiers": tiers,
            "notes": ["Iowa publishes remaining counts only for prizes of $50 and up; smaller prizes are estimated from their odds."],
        })
    return out
