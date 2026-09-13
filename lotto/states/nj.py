"""New Jersey. njlottery.com's instant-games API lists every game with all tiers
(winningTickets printed, paidTickets claimed) and the total tickets printed. Amounts are
in cents, dates epoch-ms. The state publishes no overall odds; build.py derives them
from tickets printed."""
from __future__ import annotations

from datetime import datetime, timezone

from ..fetch import get_json
from ..metrics import parse_prize_label

STATE = {
    "code": "NJ",
    "name": "New Jersey",
    "sources": [{"label": "njlottery.com: Scratch-Offs", "url": "https://www.njlottery.com/en-us/scratch-offs.html"}],
}
API = "https://www.njlottery.com/api/v1/instant-games/games?size=200"
PAGE = "https://www.njlottery.com/api/v1/instant-games/games/page?size=200&start-item={n}"


def _ms(v) -> str:
    return datetime.fromtimestamp(v / 1000, tz=timezone.utc).date().isoformat() if v else ""


def fetch_games() -> list[dict]:
    recs, start = [], 1
    data = get_json(API)
    while True:
        recs += data.get("games", [])
        if not data.get("nextPageUrl"):
            break
        start += 200
        data = get_json(PAGE.format(n=start))
    games = []
    for s in recs:
        if s.get("validationStatus") != "ACTIVE":
            continue
        gid = str(s["gameId"])
        price = (s.get("ticketPrice") or 0) / 100
        tiers = []
        for t in s.get("prizeTiers") or []:
            amt = (t.get("prizeAmount") or 0) / 100
            desc = (t.get("prizeDescription") or "").strip()
            label = desc if desc and not desc.startswith("$") or "FREE" in desc.upper() else f"${amt:,.0f}"
            value, annuity = parse_prize_label(label, price)
            if not value and amt:
                value = amt
            total, paid = int(t.get("winningTickets") or 0), int(t.get("paidTickets") or 0)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "paid": paid, "unpaid": max(total - paid, 0)})
        games.append({
            "game_number": gid,
            "name": (s.get("gameName") or "").strip(),
            "price": price,
            "tickets_printed": int(s.get("totalTicketsPrinted") or 0) or None,
            "release_date": _ms(s.get("launchDate")),
            "end_date": _ms(s.get("disableDate")),
            "image": f"https://www.njlottery.com/content/dam/portal/images/instant-games/{int(gid):05d}/ticket.png",
            "url": f"https://www.njlottery.com/en-us/scratch-offs/{int(gid):05d}.html",
            "tiers": tiers,
            "notes": ["New Jersey does not publish overall odds; they are derived from tickets printed."],
        })
    return games
