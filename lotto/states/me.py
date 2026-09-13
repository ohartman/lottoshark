"""Maine. The unclaimed-prizes table gives each game's price, percent unsold, total
unclaimed prize value and top-prize counts; the state's news articles for each game give
tickets printed, overall odds and art. No prize structure is published, so the return is
unclaimed value over unsold tickets (compute_aggregate)."""
from __future__ import annotations

import re

from ..fetch import fetch_many, get_text
from ..html import attr_all, money, num, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "ME",
    "name": "Maine",
    "sources": [{"label": "mainelottery.com: Unclaimed Prizes", "url": "https://www.mainelottery.com/players_info/unclaimed_prizes.html"}],
}
URL = "https://www.mainelottery.com/players_info/unclaimed_prizes.html"
PRICE_PAGES = ["https://www.mainelottery.com/instant/scratch%sdollar.html" % n for n in (1, 2, 3, 5, 10, 20, 25, 30, 50)]


def _article(url: str) -> dict:
    h = get_text(url, timeout=40)
    t = text(h)
    g = re.search(r"Game\s*#\s*(\d+)", t)
    printed = re.search(r"Tickets Printed[:\s]*([\d,]+)", t, re.I)
    o = re.search(r"OVERALL ODDS[:\s]*1\s*[:in]+\s*([\d.]+)", t, re.I)
    img = next((s for s in attr_all(h, "img", "src") if "attach.php" in s), None)
    return {
        "game_number": g.group(1) if g else "",
        "tickets_printed": num(printed.group(1)) if printed else 0,
        "odds": float(o.group(1)) if o else None,
        "image": ("https://www.maine.gov" + img) if img and img.startswith("/") else img,
        "url": url,
    }


def fetch_games() -> list[dict]:
    h = get_text(URL)
    table = next((t for t in tables(h) if len(t) > 5), [])
    rows: list[list[str]] = []
    for r in table:
        if len(r) >= 7 and r[1].strip().isdigit():
            rows.append(r)
        elif rows and len(r) >= 7 and not any(x.strip() for x in r[:5]):  # continuation: extra top tier
            rows[-1] = rows[-1] + [r[5], r[6]]
    links = []
    for p in fetch_many(lambda u: get_text(u, timeout=40), PRICE_PAGES, workers=4):
        if isinstance(p, str):
            links += [x.replace("&amp;", "&") for x in re.findall(r'href="([^"]*whatsnew[^"]*v=article)"', p)]
    arts = {a["game_number"]: a for a in fetch_many(_article, sorted(set(links))) if isinstance(a, dict) and a["game_number"]}
    games = []
    for r in rows:
        n, price = r[1].strip(), money(r[0])
        a = arts.get(n, {})
        tiers = []
        for label, left in zip(r[5::2], r[6::2]):
            if not label.strip():
                continue
            value, annuity = parse_prize_label(label, price)
            tiers.append({"label": label.strip(), "value": value, "annuity": annuity, "total": 0, "unpaid": num(left)})
        notes = ["Maine publishes total unclaimed prize money and percent unsold rather than a prize table; the return is computed from those."]
        if float(r[3] or 0) <= 10:
            notes.append("Nearly sold out: what is left unclaimed is mostly sold winners not yet cashed, so no estimate.")
        if not a.get("tickets_printed"):
            notes.append("Tickets printed for this game was not found on the state's site, so there is no estimate.")
        games.append({
            "game_number": n,
            "name": r[2].strip(),
            "price": price,
            "odds": a.get("odds"),
            "odds_label": f"1 in {a['odds']}" if a.get("odds") else "",
            "tickets_printed": a.get("tickets_printed") or None,
            "pct_sold": 1 - float(r[3] or 0) / 100,
            "pct_step": 0.001,
            "unclaimed_value": money(r[4]),
            "top_prize_remaining": tiers[0]["unpaid"] if tiers else 0,
            "image": a.get("image"),
            "url": a.get("url", URL),
            "tiers": tiers,
            "notes": notes,
        })
    return games
