"""Washington. Explorer.aspx embeds the whole game list, all prize tiers included, as a
JSON string inside an inline script (WaLottery.Scratch.data = { all: JSON.parse('...') })."""
from __future__ import annotations

import json
import re
from datetime import datetime

from ..fetch import get_text
from ..html import num, odds
from ..metrics import parse_prize_label

STATE = {
    "code": "WA",
    "name": "Washington",
    "sources": [{"label": "walottery.com: Scratch Explorer", "url": "https://www.walottery.com/Scratch/Explorer.aspx"}],
}
URL = "https://www.walottery.com/Scratch/Explorer.aspx"


def _date(s) -> str:
    if not s:
        return ""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(s))
    if m:
        return datetime(int(m.group(3)), int(m.group(1)), int(m.group(2))).date().isoformat()
    m = re.match(r"\d{4}-\d{2}-\d{2}", str(s))
    return m.group(0) if m else ""


def fetch_games() -> list[dict]:
    html = get_text(URL)
    m = re.search(r"all:\s*JSON\.parse\('((?:[^'\\]|\\.)*)'\)", html)
    if not m:
        raise RuntimeError("could not find the embedded game JSON on Explorer.aspx")
    blob = m.group(1).encode("utf-8").decode("unicode_escape")
    data = json.loads(blob)
    games = []
    for s in data["Games"]:
        price = float(s.get("Cost") or 0)
        tiers = []
        for t in s.get("Prizes") or []:
            label = str(t.get("PrizeAmount") or "").strip()
            value, annuity = parse_prize_label(label, price)
            total = int(t.get("TotalPrizesNumber") or num(t.get("TotalPrizes")))
            unpaid = int(t.get("PrizesRemainingNumber") or num(t.get("PrizesRemaining")))
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        gid = str(s["Id"])
        games.append({
            "game_number": gid,
            "name": (s.get("GameName") or "").strip(),
            "price": price,
            "odds": odds(s.get("OverallOdds")),
            "odds_label": (s.get("OverallOdds") or "").strip(),
            "tickets_printed": num(s.get("TicketsPrinted")) or None,
            "release_date": _date(s.get("SalesStartDate")),
            "end_date": _date(s.get("RedeemEndDate")),
            "image": s.get("GridImageUrl") or s.get("UnscratchedImageUrl"),
            "url": URL,
            "tiers": tiers,
            "notes": ["Sales have ended; prizes can still be claimed."] if s.get("SalesEndDate") else [],
        })
    return games
