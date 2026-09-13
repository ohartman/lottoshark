"""Louisiana. The top-prizes page embeds a JSON list of current scratch-offs (number,
price, art, start date, link); each game page has a table of every tier with total,
claimed and remaining, plus the overall odds."""
from __future__ import annotations

import json
import re
from datetime import datetime

from ..fetch import fetch_many, get_text
from ..html import money, num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "LA",
    "name": "Louisiana",
    "sources": [{"label": "louisianalottery.com: Top Prizes Remaining", "url": "https://louisianalottery.com/top-prizes-remaining/"}],
}
URL = "https://louisianalottery.com/top-prizes-remaining/"


def _date(s: str) -> str:
    try:
        return datetime.strptime((s or "").strip(), "%m/%d/%Y").date().isoformat()
    except ValueError:
        return ""


def _game(row: dict) -> dict:
    link = row["game"]["link"]
    h = get_text(link, timeout=60)
    price = money(row.get("price"))
    tiers = []
    for t in tables(h):
        if not t or not t[0] or not t[0][0].lower().startswith("tier"):
            continue
        for r in t[1:]:
            if len(r) < 5:
                continue
            value, annuity = parse_prize_label(r[0], price)
            total, paid, unpaid = num(r[2]), num(r[3]), num(r[4])
            tiers.append({"label": r[0], "value": value, "annuity": annuity, "total": total, "paid": paid, "unpaid": unpaid})
        break
    t = text(h)
    o = re.search(r"(1 in [\d.,]+)\s*Overall Odds", t) or re.search(r"Overall Odds[^\d]*(1 in [\d.,]+)", t)
    close = re.search(r"Close Date[^\d]*(\d{2}/\d{2}/\d{4})", t)
    redeem = re.search(r"Final Redemption Date[^\d]*(\d{2}/\d{2}/\d{4})", t)
    notes = []
    if close and _date(close.group(1)) <= datetime.now().date().isoformat():
        notes.append("Sales have ended; prizes can still be claimed.")
    return {
        "game_number": str(row.get("number") or "").strip(),
        "name": row["game"]["name"].strip(),
        "price": price,
        "odds": odds(o.group(1)) if o else None,
        "odds_label": o.group(1) if o else "",
        "release_date": _date(row.get("start_date")),
        "end_date": _date(redeem.group(1)) if redeem else "",
        "image": row.get("image"),
        "url": link,
        "tiers": tiers,
        "notes": notes,
    }


def fetch_games() -> list[dict]:
    h = get_text(URL, timeout=60)
    m = re.search(r'<prize-table>\s*<script type="application/json">(.*?)</script>', h, re.S)
    if not m:
        raise RuntimeError("no embedded prize-table JSON on the top-prizes page")
    rows = [r for r in json.loads(m.group(1))["data"] if "/game/" in (r.get("game") or {}).get("link", "")]
    return [g for g in fetch_many(_game, rows, workers=4) if isinstance(g, dict)]
