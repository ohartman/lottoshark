"""Georgia. galottery.com's instant-games API returns every game with all tiers
(winningTickets printed, paidTickets claimed). Prices are in cents and prize amounts in
dollars x 10,000. Annuitised top prizes are encoded as amount 0; the top-prizes page
carries their label. Overall odds live only in each game's page JSON."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from ..fetch import fetch_many, get_json, get_text
from ..html import odds
from ..metrics import parse_prize_label

STATE = {
    "code": "GA",
    "name": "Georgia",
    "sources": [
        {"label": "galottery.com: Scratchers Top Prizes Claimed", "url": "https://www.galottery.com/en-us/games/scratchers/scratchers-top-prizes-claimed.html"},
    ],
}
API = "https://www.galottery.com/api/v1/instant-games/games?size=500"
TOP = "https://www.galottery.com/en-us/games/scratchers/scratchers-top-prizes-claimed.html"
PAGE = "https://www.galottery.com/en-us/games/scratchers/{gid}.html"
INFO = "https://www.galottery.com/en-us/games/scratchers/{gid}.infinity.json"
IMG = "https://www.galottery.com/content/dam/portal/images/scratchers-games/{gid}/thumb.png"


def _ms(v) -> str:
    return datetime.fromtimestamp(v / 1000, tz=timezone.utc).date().isoformat() if v else ""


def _odds(gid: str) -> str:
    c = get_json(INFO.format(gid=gid), timeout=40).get("jcr:content", {})
    return (c.get("gameOddsAndLike", {}).get("scratchersoddsandlik", {}).get("odds") or "").strip()


def fetch_games() -> list[dict]:
    recs = get_json(API).get("games", [])
    active = [r for r in recs if r.get("validationStatus") == "ACTIVE"]
    top = {m.group(1): m.group(2) for m in re.finditer(r'"gameId":"(\d+)","gameName":"[^"]*","ticketPrice":"[^"]*","topPrize":"([^"]*)"', get_text(TOP))}
    odd = dict(zip([r["gameId"] for r in active], fetch_many(_odds, [r["gameId"] for r in active])))
    games = []
    for s in active:
        gid = str(s["gameId"])
        price = (s.get("ticketPrice") or 0) / 100
        tiers = []
        for t in s.get("prizeTiers") or []:
            amt = (t.get("prizeAmount") or 0) / 10_000
            label = f"${amt:,.0f}" if amt else (top.get(gid) or "Top prize")
            value, annuity = parse_prize_label(label, price)
            total, paid = int(t.get("winningTickets") or 0), int(t.get("paidTickets") or 0)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "paid": paid, "unpaid": max(total - paid, 0)})
        o = odd.get(gid)
        o = o if isinstance(o, str) else ""
        games.append({
            "game_number": gid,
            "name": (s.get("gameName") or "").strip(),
            "price": price,
            "odds": odds(o),
            "odds_label": o,
            "release_date": _ms(s.get("launchDate")),
            "end_date": _ms(s.get("disableDate")),
            "image": IMG.format(gid=gid),
            "url": PAGE.format(gid=gid),
            "tiers": tiers,
            "notes": [],
        })
    return games
