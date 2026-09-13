"""Kansas. playonkansas.com is a Next.js site; the listing's server payload carries every
game (number, price, dates, art) and each game page has a table of remaining prizes for
every level, but no printed counts. Tickets unsold are taken as prizes remaining times
the overall odds (compute_remaining_only)."""
from __future__ import annotations

import re
from datetime import date, datetime

from ..fetch import fetch_many, get_text
from ..html import money, num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "KS",
    "name": "Kansas",
    "sources": [{"label": "playonkansas.com: Scratch and Pull Tabs", "url": "https://playonkansas.com/games/scratch-and-pull-tabs"}],
}
LIST = "https://playonkansas.com/games/scratch-and-pull-tabs"
FIELDS = ("gameNumber", "slug", "title", "startDate", "endDate", "claimEndDate")


def _undouble(s: str) -> str:
    """Cells repeat their text in a hidden span for screen readers: '$500$500' -> '$500'."""
    s = s.strip()
    h = len(s) // 2
    return s[:h] if len(s) % 2 == 0 and s[:h] == s[h:] else s


def _records(payload: str) -> list[dict]:
    txt = payload.replace('\\"', '"')
    out = {}
    for chunk in txt.split('"gameId":')[1:]:
        chunk = chunk[:3000]
        r = {}
        for k in FIELDS:
            m = re.search(r'"%s":"((?:[^"\\]|\\.)*)"' % k, chunk)
            if m:
                r[k] = m.group(1)
        m = re.search(r'"ticketPrice":([\d.]+)', chunk)
        if m:
            r["ticketPrice"] = float(m.group(1))
        r["pullTab"] = '"pullTab":true' in chunk
        m = re.search(r'"image":\{"url":"([^"]+)"', chunk)
        if m:
            r["image"] = m.group(1)
        if r.get("gameNumber") and r.get("slug"):
            out.setdefault(r["gameNumber"], {}).update(r)
    return list(out.values())


def _game(r: dict) -> dict:
    url = f"{LIST}/{r['slug']}"
    h = get_text(url, timeout=40)
    t = text(h)
    o = re.search(r"Overall Odds\s*(1 in [\d.]+)", t)
    price = r.get("ticketPrice") or money((re.search(r"Price\s*\$([\d.]+)", t) or [None, "0"])[1])
    tiers = []
    for tb in tables(h):
        rows = [(_undouble(x[0]), num(_undouble(x[1]))) for x in tb if len(x) >= 2 and (x[0].startswith("$") or "FREE" in x[0].upper())]
        if rows:
            for label, left in rows:
                value, annuity = parse_prize_label(label, price)
                tiers.append({"label": label, "value": value, "annuity": annuity, "total": 0, "unpaid": left})
            break
    return {
        "game_number": r["gameNumber"],
        "name": (r.get("title") or "").strip(),
        "price": price,
        "odds": odds(o.group(1)) if o else None,
        "odds_label": o.group(1) if o else "",
        "release_date": (r.get("startDate") or "")[:10],
        "end_date": (r.get("claimEndDate") or "")[:10],
        "image": r.get("image"),
        "url": url,
        "tiers": tiers,
        "notes": ["Kansas publishes remaining counts for every prize but not how many were printed."],
    }


def fetch_games() -> list[dict]:
    recs = [r for r in _records(get_text(LIST, headers={"RSC": "1"})) if not r.get("pullTab")]
    today = date.today().isoformat()
    recs = [r for r in recs if not r.get("endDate") or r["endDate"][:10] >= today]
    return [g for g in fetch_many(_game, recs) if isinstance(g, dict) and g["tiers"]]
