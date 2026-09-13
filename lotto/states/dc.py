"""District of Columbia. dclottery.com's JSON:API lists every scratcher (path, odds,
claim deadline); each game page carries price, game number, start date and a table of
every tier with total, paid and remaining."""
from __future__ import annotations

import re
from datetime import date, datetime

from ..fetch import fetch_many, get_json, get_text
from ..html import money, num, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "DC",
    "name": "District of Columbia",
    "sources": [{"label": "dclottery.com: DC Scratchers", "url": "https://dclottery.com/dc-scratchers"}],
}
SITE = "https://dclottery.com"
API = SITE + "/jsonapi/node/game_scratchers?page%5Blimit%5D=50"


def _page(node: dict) -> dict:
    a = node["attributes"]
    url = SITE + a["path"]["alias"]
    h = get_text(url, timeout=40)
    t = text(h)
    field = lambda k: (re.search(re.escape(k) + r"\s*:?\s*([^\n]+?)\s{2,}|" + re.escape(k) + r"\s*:?\s*(\S[^\n]*)", t) or [None, "", ""])
    price = money((re.search(r"Price\s*\$?([\d.]+)", t) or [None, "0"])[1])
    gno = re.search(r"Game No\.?\s*(\d+)", t)
    start = re.search(r"Start Date\s*(\d{2}/\d{2}/\d{4})", t)
    o = re.search(r"\bOdds\s*1:([\d.,]+)", t)
    tiers = []
    for tb in tables(h):
        if tb and tb[0] and tb[0][0].lower().startswith("prize amount"):
            for r in tb[1:]:
                if len(r) < 4:
                    continue
                value, annuity = parse_prize_label(r[0], price)
                total, paid, unpaid = num(r[1]), num(r[2]), num(r[3])
                tiers.append({"label": r[0], "value": value, "annuity": annuity, "total": total, "paid": paid, "unpaid": unpaid})
            break
    img = re.search(r'<img[^>]*src="([^"]*sites/default/files/styles[^"]*)"', h)
    claim = (a.get("field_last_date_to_claim") or "")[:10]
    return {
        "game_number": gno.group(1) if gno else "",
        "name": (a.get("title") or "").strip(),
        "price": price,
        "odds": float(o.group(1).replace(",", "")) if o else None,
        "odds_label": f"1 in {o.group(1)}" if o else (a.get("field_odds") or "").replace(":", " in "),
        "release_date": datetime.strptime(start.group(1), "%m/%d/%Y").date().isoformat() if start else (a.get("field_date") or [{}])[0].get("value", "")[:10],
        "end_date": claim,
        "image": (SITE + img.group(1)) if img and img.group(1).startswith("/") else (img.group(1) if img else None),
        "url": url,
        "tiers": tiers,
        "notes": [],
    }


def fetch_games() -> list[dict]:
    url, nodes = API, []
    while url:
        d = get_json(url)
        nodes += d.get("data", [])
        url = (d.get("links", {}).get("next") or {}).get("href")
    today = date.today().isoformat()
    live = [n for n in nodes if n["attributes"].get("status") and not (
        (n["attributes"].get("field_last_date_to_claim") or "9999") < today)]
    pages = fetch_many(_page, live)
    return [p for p in pages if isinstance(p, dict) and p["game_number"] and p["tiers"]]
