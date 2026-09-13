"""Connecticut. ctlottery.com is a Next.js site whose server payload embeds the game list
and, on each game page, a "game" record with every prize tier (total, remaining), the
overall odds and the number of tickets printed. The JSON is pulled out of the payload
string with regexes; dollar signs are doubled in it."""
from __future__ import annotations

import json
import re

from ..fetch import fetch_many, get_text
from ..html import odds
from ..metrics import parse_prize_label

STATE = {
    "code": "CT",
    "name": "Connecticut",
    "sources": [{"label": "ctlottery.com: Scratch Games", "url": "https://ctlottery.com/games/scratch-games"}],
}
SITE = "https://ctlottery.com"
LIST = SITE + "/games/scratch-games"


def _unescape(s: str) -> str:
    """The RSC payload is a JS string literal: \\" for quotes, $$ for $."""
    return s.replace('\\"', '"').replace("\\\\", "\\").replace("$$", "$")


def _find_obj(payload: str, key: str) -> dict | None:
    """Find "key":{...} in the escaped payload and parse the balanced object."""
    m = re.search(r'\\"' + key + r'\\":\{', payload)
    if not m:
        return None
    i, depth, start = m.end() - 1, 0, m.end() - 1
    while i < len(payload):
        c = payload[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(_unescape(payload[start:i + 1]))
        i += 1
    return None


def _game(no: int) -> dict:
    h = get_text(f"{LIST}/{no}", timeout=40)
    g = _find_obj(h, "game")
    if not g or "prizes" not in g:
        raise RuntimeError(f"no game payload for {no}")
    return g


def fetch_games() -> list[dict]:
    h = get_text(LIST)
    nos = sorted({int(x) for x in re.findall(r'\\"gameNo\\":(\d+)', h)})
    recs = fetch_many(_game, nos)
    games = []
    for no, g in zip(nos, recs):
        if not isinstance(g, dict):
            continue
        price = float(g.get("ticketCostRaw") or 0)
        tiers = []
        for t in g.get("prizes") or []:
            label = (t.get("amount") or "").strip()
            value, annuity = parse_prize_label(label, price)
            if not value and t.get("amountRaw"):
                value = float(t["amountRaw"])
            total, unpaid = int(t.get("total") or 0), int(t.get("remaining") or 0)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        stop = (g.get("stopDate") or "")[:10]
        img = ((g.get("images") or {}).get("thumbnail") or (g.get("images") or {}).get("full") or "")
        games.append({
            "game_number": str(no),
            "name": (g.get("gameName") or "").strip(),
            "price": price,
            "odds": odds(g.get("overallOdds")),
            "odds_label": (g.get("overallOdds") or "").strip(),
            "tickets_printed": int(g.get("totalTickets") or 0) or None,
            "release_date": (g.get("launchDate") or g.get("startDate") or "")[:10],
            "end_date": "" if (g.get("endValDate") or "").startswith("2099") else (g.get("endValDate") or "")[:10],
            "image": SITE + img if img.startswith("/") else (img or None),
            "url": f"{LIST}/{no}",
            "tiers": tiers,
            "notes": [] if stop.startswith("2099") or not stop else ["Sales end " + stop + "; prizes can still be claimed after."],
        })
    return games
