"""Wisconsin. Each game page gives price, odds, start date and the top prize's printed
and remaining counts; its features-and-procedures page gives the approximate printed
count for every prize level. Only the top prize has a remaining count, so the return is
an estimate with a range."""
from __future__ import annotations

import re
from datetime import date, datetime

from ..fetch import fetch_many, get_text
from ..html import money, num, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "WI",
    "name": "Wisconsin",
    "sources": [{"label": "wilottery.com: Scratch Games", "url": "https://wilottery.com/games/instant-games/scratch-games"}],
}
SITE = "https://wilottery.com"
LIST = SITE + "/games/instant-games/scratch-games?page={p}"


def _game(path: str) -> dict:
    h = get_text(SITE + path, timeout=40)
    t = text(h)
    f = lambda k: (re.search(re.escape(k) + r"\s*:?\s*(\S[^\n]{0,24})", t) or [None, ""])[1]
    n = re.search(r"Game Number\s*(\d+)", t)
    price = money(re.search(r"Price\s*\$([\d.]+)", t).group(1)) if re.search(r"Price\s*\$([\d.]+)", t) else 0.0
    o = re.search(r"Overall Odds\s*1\s*[:in]+\s*([\d.]+)", t)
    top_total = num((re.search(r"Total Top Prizes\s*([\d,]+)", t) or [None, "0"])[1])
    top_left = num((re.search(r"Remaining Top Prizes\s*([\d,]+)", t) or [None, "0"])[1])
    start = re.search(r"Start Date\s*(\d{2}/\d{2}/\d{4})", t)
    name = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    img = re.search(r'src="([^"]*sites/default/files/styles[^"]*)"', h)
    feat = re.search(r'href="([^"]*features-procedures[^"]*)"', h)
    tiers = []
    if feat:
        fh = get_text(SITE + feat.group(1) if feat.group(1).startswith("/") else feat.group(1), timeout=40)
        for tb in tables(fh):
            rows = [(r[0].strip(), num(r[1])) for r in tb if len(r) >= 2 and r[0].strip().startswith("$")]
            if rows:
                for label, total in rows:
                    value, annuity = parse_prize_label(label, price)
                    tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": None})
                break
    if tiers:
        top = max(tiers, key=lambda x: x["value"])
        top["unpaid"] = top_left
        if top_total:
            top["total"] = top_total
    return {
        "game_number": n.group(1) if n else "",
        "name": text(name.group(1)) if name else "",
        "price": price,
        "odds": float(o.group(1)) if o else None,
        "odds_label": f"1 in {o.group(1)}" if o else "",
        "release_date": datetime.strptime(start.group(1), "%m/%d/%Y").date().isoformat() if start else "",
        "top_prize_remaining": top_left,
        "image": (SITE + img.group(1)) if img else None,
        "url": SITE + path,
        "tiers": tiers,
        "notes": ["Wisconsin publishes a remaining count only for the top prize; the rest is estimated from the printed prize structure."],
    }


def fetch_games() -> list[dict]:
    # Each listing item carries data-endd: empty while the game is on sale.
    today = date.today().isoformat()
    paths: list[str] = []
    for p in range(0, 25):
        h = get_text(LIST.format(p=p), timeout=60)
        items = re.findall(r'<div class="instant-listing-item[^"]*"[^>]*data-endd="([^"]*)"[^>]*>\s*<a href="(/games/instant-games/[a-z0-9-]+-\d{4})"', h)
        if not items:
            break
        paths += [u for end, u in items if (not end or end >= today) and u not in paths]
    recs = fetch_many(_game, paths, workers=4)
    return [g for g in recs if isinstance(g, dict) and g["game_number"] and g["tiers"]]
