"""California. calottery.com's Sitecore JSON list gives every scratcher with price, odds,
launch date and art; each game page has a server-rendered table of every tier with
"remaining of total"."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from ..fetch import fetch_many, get_json, get_text
from ..html import money, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "CA",
    "name": "California",
    "sources": [{"label": "calottery.com: Scratchers", "url": "https://www.calottery.com/scratchers"}],
}
SITE = "https://www.calottery.com"
MODEL = "0dc0c687-836a-43d3-aa8b-a0491dbf4001"
LIST = SITE + "/api/Sitecore/ScratchersFilteredList/GetScratchers?modelId={m}&sortBy=&page=1&size=200&show=&gametype=&price=&nameOrNumber="


def _list():
    d = get_json(LIST.format(m=MODEL))
    if not d.get("SerializedScratcherCardList"):
        m = re.search(r"modelId\s*=\s*'([0-9a-f-]{36})'", get_text(SITE + "/scratchers"))
        if m:
            d = get_json(LIST.format(m=m.group(1)))
    return d.get("SerializedScratcherCardList") or []


def _page(rec: dict) -> dict:
    url = SITE + rec["GameProductPage"]
    h = get_text(url, timeout=40)
    price = money(rec.get("GamePrice"))
    tiers = []
    for t in tables(h):
        if not t or not t[0] or not t[0][0].lower().startswith("prize"):
            continue
        for r in t[1:]:
            if len(r) < 3:
                continue
            m = re.match(r"([\d,]+)\s*of\s*([\d,]+)", r[2])
            if not m:
                continue
            value, annuity = parse_prize_label(r[0], price)
            unpaid, total = int(m.group(1).replace(",", "")), int(m.group(2).replace(",", ""))
            tiers.append({"label": r[0], "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        break
    o = re.search(r"Overall odds:?\s*(1 in [\d.]+)", text(h), re.I)
    return {"tiers": tiers, "odds_label": o.group(1) if o else "", "url": url}


def fetch_games() -> list[dict]:
    recs = _list()
    pages = fetch_many(_page, recs)
    games = []
    for rec, p in zip(recs, pages):
        price = money(rec.get("GamePrice"))
        ms = re.search(r"\d+", rec.get("GotoMarketDate") or "")
        p = p if isinstance(p, dict) else {"tiers": [], "odds_label": "", "url": SITE + rec.get("GameProductPage", "")}
        o = float(rec["OverallOdds"]) if rec.get("OverallOdds") else None
        games.append({
            "game_number": str(rec["GameNumber"]),
            "name": (rec.get("GameName") or "").strip(),
            "price": price,
            "odds": o,
            "odds_label": p["odds_label"] or (f"1 in {o:.2f}" if o else ""),
            "release_date": datetime.fromtimestamp(int(ms.group(0)) / 1000, tz=timezone.utc).date().isoformat() if ms else "",
            "top_prize_label": rec.get("TopPrizeDollarAmt") or None,
            "image": rec.get("ScratchersImage"),
            "url": p["url"],
            "tiers": p["tiers"],
            "notes": [] if p["tiers"] else ["Prize table could not be read from the game page today."],
        })
    return games
