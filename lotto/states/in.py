"""Indiana. hoosierlottery.com's scratch-off listing carries each game's number, name,
price, odds and art; each game page has a table of every tier (unclaimed, total)."""
from __future__ import annotations

import re
from datetime import datetime

from ..fetch import fetch_many, get_text
from ..html import num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "IN",
    "name": "Indiana",
    "sources": [{"label": "hoosierlottery.com: Scratch-offs", "url": "https://hoosierlottery.com/games/scratch-off/"}],
}
SITE = "https://hoosierlottery.com"
LIST = SITE + "/games/scratch-off/"


def _cards(html: str) -> list[dict]:
    out = []
    for m in re.finditer(r'<a[^>]*class="[^"]*\bgame\b[^"]*"[^>]*>(.*?)</a>', html, re.S):
        tag = m.group(0)
        attrs = dict(re.findall(r'data-([a-z-]+)="([^"]*)"', tag))
        href = re.search(r'href="([^"]+)"', tag)
        if not attrs.get("id") or not href or "game-visible" not in tag or any(c["id"] == attrs["id"] for c in out):
            continue
        img = re.search(r'src="([^"]+)"', m.group(1))
        o = re.search(r"Overall Odds:?\s*(1 in [\d.]+)", text(m.group(1)))
        out.append({"id": attrs["id"], "name": attrs.get("name", ""), "price": float(attrs.get("price") or 0),
                    "href": href.group(1), "image": (SITE + img.group(1) if img.group(1).startswith("/") else img.group(1)).replace("&amp;", "&") if img else None,
                    "odds": o.group(1) if o else ""})
    return out


def _page(card: dict) -> dict:
    url = card["href"] if card["href"].startswith("http") else SITE + card["href"]
    h = get_text(url, timeout=40)
    t = text(h)
    tiers = []
    for tb in tables(h):
        if tb and tb[0] and tb[0][0].lower().startswith("prize amount"):
            for r in tb[1:]:
                if len(r) < 3 or not r[0].startswith("$"):
                    continue
                value, annuity = parse_prize_label(r[0], card["price"])
                unpaid, total = num(r[1]), num(r[2])
                tiers.append({"label": r[0], "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
            break
    o = re.search(r"Overall Odds:?\s*(1 in [\d.]+)", t) or [None, card["odds"]]
    sale = re.search(r"Sale Date:?\s*(\d{1,2}/\d{1,2}/\d{4})", t)
    notes = []
    if tiers and min(t["value"] for t in tiers) > card["price"]:
        # The page lists only the larger prizes; without the small tiers the unsold share
        # and the return cannot be estimated, so leave the odds out to skip the metrics.
        notes.append("Indiana publishes counts only for the larger prize levels of this game, so no return estimate is possible.")
        o = [None, ""]
    return {
        "game_number": card["id"],
        "name": card["name"] or text((re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S) or [None, ""])[1]),
        "price": card["price"],
        "odds": odds(o[1]),
        "odds_label": o[1],
        "release_date": datetime.strptime(sale.group(1), "%m/%d/%Y").date().isoformat() if sale else "",
        "image": card["image"],
        "url": url,
        "tiers": tiers,
        "notes": notes,
    }


def fetch_games() -> list[dict]:
    cards = _cards(get_text(LIST, timeout=60))
    if not cards:
        raise RuntimeError("no game cards on the listing page")
    return [g for g in fetch_many(_page, cards) if isinstance(g, dict) and g["tiers"]]
