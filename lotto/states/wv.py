"""West Virginia. wvlottery.com is a Next.js site; asking for the server-component payload
(RSC: 1 header) returns the game list as JSON text, and each game's payload adds
prizeDetails with every tier's total and remaining."""
from __future__ import annotations

import json
import re
from datetime import date

from ..fetch import fetch_many, get_text
from ..html import odds
from ..metrics import parse_prize_label

STATE = {
    "code": "WV",
    "name": "West Virginia",
    "sources": [{"label": "wvlottery.com: Scratch-Offs", "url": "https://wvlottery.com/games/scratch-offs"}],
}
LIST = "https://wvlottery.com/games/scratch-offs"
RSC = {"RSC": "1"}


FIELDS = ("gameNumber", "slug", "title", "startDate", "endDate", "claimEndDate", "odds", "rulesPdf")


def _records(payload: str) -> list[dict]:
    """One record per "gameId":N chunk of the RSC text; the flat fields are pulled out
    with regexes because records nest rich-text objects that defeat a simple brace match."""
    txt = payload.replace('\\"', '"')
    out = {}
    for chunk in txt.split('"gameId":')[1:]:
        chunk = chunk[:4000]
        r = {}
        for k in FIELDS:
            m = re.search(r'"%s":"((?:[^"\\]|\\.)*)"' % k, chunk)
            if m:
                r[k] = m.group(1)
        m = re.search(r'"ticketPrice":([\d.]+)', chunk)
        if m:
            r["ticketPrice"] = float(m.group(1))
        m = re.search(r'"image":\{"url":"([^"]+)"', chunk)
        if m:
            r["image"] = {"url": m.group(1)}
        if r.get("gameNumber") and r.get("slug"):
            out.setdefault(r["gameNumber"], {}).update(r)
    return list(out.values())


def _detail(rec: dict) -> list[dict]:
    p = get_text(f"{LIST}/{rec['slug']}", timeout=40, headers=RSC).replace('\\"', '"')
    m = re.search(r'"prizeDetails":(\[[^\]]*\])', p)
    return json.loads(m.group(1)) if m else []


def fetch_games() -> list[dict]:
    recs = _records(get_text(LIST, headers=RSC))
    today = date.today().isoformat()
    live = [r for r in recs if not r.get("endDate") or r["endDate"][:10] >= today or (r.get("claimEndDate") or "")[:10] >= today]
    details = fetch_many(_detail, live)
    games = []
    for r, d in zip(live, details):
        if not isinstance(d, list) or not d:
            continue
        price = float(r.get("ticketPrice") or 0)
        tiers = []
        for t in d:
            amt = float(t.get("prize") or 0)
            label = f"${amt:,.0f}"
            value, annuity = parse_prize_label(label, price)
            total, unpaid = int(t.get("totalPrizes") or 0), int(t.get("remainingPrizes") or 0)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        games.append({
            "game_number": r["gameNumber"],
            "name": (r.get("title") or "").strip(),
            "price": price,
            "odds": odds(r.get("odds")) or (float(r["odds"]) if re.fullmatch(r"[\d.]+", (r.get("odds") or "").strip()) else None),
            "odds_label": ("1 in " + r["odds"].strip()) if re.fullmatch(r"[\d.]+", (r.get("odds") or "").strip()) else (r.get("odds") or "").strip(),
            "release_date": (r.get("startDate") or "")[:10],
            "end_date": (r.get("claimEndDate") or "")[:10],
            "image": ((r.get("image") or {}).get("url")) if isinstance(r.get("image"), dict) else None,
            "url": f"{LIST}/{r['slug']}",
            "pdf": r.get("rulesPdf") if isinstance(r.get("rulesPdf"), str) else "",
            "tiers": tiers,
            "notes": ["Sales have ended; prizes can still be claimed."] if (r.get("endDate") or "9999")[:10] < today else [],
        })
    return games
