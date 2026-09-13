"""Mississippi. mslottery.com's WordPress REST API lists active instant games with the
prize table (original and remaining counts) as HTML in the post body; the ticket price
is a taxonomy term and the overall odds and game number are on each game's page."""
from __future__ import annotations

import re

from ..fetch import fetch_many, get_json, get_text
from ..html import money, num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "MS",
    "name": "Mississippi",
    "sources": [{"label": "mslottery.com: Active Instant Games", "url": "https://www.mslottery.com/gamestatus/active/"}],
}
API = "https://www.mslottery.com/wp-json/wp/v2/instantgames?per_page=100&gamestatus=25"
PRICES = "https://www.mslottery.com/wp-json/wp/v2/gamevalue?per_page=100"


def _page(link: str) -> dict:
    t = text(get_text(link, timeout=40))
    o = re.search(r"Overall Odds\s*(1\s*[:in]+\s*[\d.]+)", t)
    g = re.search(r"Game Number\s*(\d+)", t)
    return {"odds": o.group(1).replace(":", " in ") if o else "", "game_number": g.group(1) if g else ""}


def fetch_games() -> list[dict]:
    posts, page = [], 1
    while True:
        batch = get_json(f"{API}&page={page}")
        posts += batch
        if len(batch) < 100:
            break
        page += 1
    prices = {p["id"]: money(p.get("name")) for p in get_json(PRICES)}
    extra = fetch_many(lambda p: _page(p["link"]), posts)
    games = []
    for p, e in zip(posts, extra):
        e = e if isinstance(e, dict) else {"odds": "", "game_number": ""}
        price = next((prices[i] for i in p.get("gamevalue") or [] if i in prices), 0.0)
        tiers = []
        for tb in tables(p.get("content", {}).get("rendered", "")):
            if tb and any(r and r[0].startswith("$") for r in tb):
                for r in tb:
                    if len(r) < 3 or not r[0].startswith("$"):
                        continue
                    value, annuity = parse_prize_label(r[0], price)
                    total, unpaid = num(r[1]), num(r[2])
                    tiers.append({"label": r[0], "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
                break
        img = (p.get("yoast_head_json") or {}).get("og_image") or []
        games.append({
            "game_number": e["game_number"] or str(p["id"]),
            "name": text(p.get("title", {}).get("rendered", "")),
            "price": price,
            "odds": odds(e["odds"]),
            "odds_label": e["odds"],
            "image": img[0].get("url") if img else None,
            "url": p.get("link", STATE["sources"][0]["url"]),
            "tiers": tiers,
            "notes": [],
        })
    return games
