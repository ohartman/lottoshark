"""Nebraska. The prizes-remaining page lists each game's price, number, art and the
remaining count for its top two or three prize levels; each game's detail page has the
full printed prize structure (one row per winning combination, summed per prize) and
the overall odds. Lower tiers have no remaining count, so the return is an estimate."""
from __future__ import annotations

import re
from collections import OrderedDict

from ..fetch import fetch_many, get_text
from ..html import money, num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "NE",
    "name": "Nebraska",
    "sources": [{"label": "nelottery.com: Scratch prizes remaining", "url": "https://nelottery.com/homeapp/scratch/prizesremaining/web"}],
}
LIST = "https://nelottery.com/homeapp/scratch/prizesremaining/web"
DETAIL = "https://nelottery.com/homeapp/scratch/{n}/0/gamedetail/web"


def _detail(n: str) -> dict:
    h = get_text(DETAIL.format(n=n), timeout=40)
    totals: OrderedDict[str, int] = OrderedDict()
    for tb in tables(h):
        rows = [r for r in tb if len(r) >= 3 and r[0].startswith("$")]
        if rows:
            for r in rows:
                totals[r[0].strip()] = totals.get(r[0].strip(), 0) + num(r[2])
            break
    o = re.search(r"Overall odds[^\d]*(1 in [\d.]+)", text(h), re.I)
    return {"totals": totals, "odds": o.group(1) if o else ""}


def fetch_games() -> list[dict]:
    h = get_text(LIST)
    blocks = re.split(r'(?=<div class="gameBlock">)', h)[1:]
    parsed = []
    for b in blocks:
        n = re.search(r"#\s*(\d+)", text(b))
        if not n:
            continue
        name = re.search(r'<span style="font-weight:bold">(.*?)</span>', b, re.S)
        price = money(re.search(r'class="ballDollar">([\d.]+)<', b).group(1)) if re.search(r'class="ballDollar">([\d.]+)<', b) else 0.0
        img = re.search(r'<img src="([^"]+)" class="gameTile"', b)
        remaining = {r[0].strip(): num(r[1]) for tb in tables(b) for r in tb if len(r) >= 2 and r[0].strip().startswith("$")}
        parsed.append({"n": n.group(1), "name": text(name.group(1)) if name else "", "price": price, "image": img.group(1) if img else None, "remaining": remaining})
    details = fetch_many(lambda p: _detail(p["n"]), parsed)
    games = []
    for p, d in zip(parsed, details):
        d = d if isinstance(d, dict) else {"totals": {}, "odds": ""}
        tiers = []
        for label, total in d["totals"].items():
            value, annuity = parse_prize_label(label, p["price"])
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": p["remaining"].get(label)})
        if not tiers:
            for label, left in p["remaining"].items():
                value, annuity = parse_prize_label(label, p["price"])
                tiers.append({"label": label, "value": value, "annuity": annuity, "total": 0, "unpaid": left})
        games.append({
            "game_number": p["n"],
            "name": p["name"],
            "price": p["price"],
            "odds": odds(d["odds"]),
            "odds_label": d["odds"],
            "image": p["image"],
            "url": DETAIL.format(n=p["n"]),
            "tiers": tiers,
            "notes": ["Nebraska publishes remaining counts only for its top prize levels; the rest is estimated."],
        })
    return games
