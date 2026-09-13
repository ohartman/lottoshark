"""Oregon. oregonlottery.org fills its scratch-its pages in the browser from the lottery's
game-info API, which the page authorises itself. A headless browser loads the public
list page (every game with price, odds, dates, sell-through and unclaimed value) and each
current game's page, whose API response carries every prize tier's total and remaining."""
from __future__ import annotations

import re
from datetime import date

from ..browser import browser, capture
from ..metrics import parse_prize_label

STATE = {
    "code": "OR",
    "name": "Oregon",
    "sources": [{"label": "oregonlottery.org: Scratch-its", "url": "https://www.oregonlottery.org/scratch-its/list/"}],
}
LIST = "https://www.oregonlottery.org/scratch-its/list/"
API = "api.oregonlottery.org/gameinfo"


def fetch_games() -> list[dict]:
    today = date.today().isoformat()
    games = []
    with browser() as ctx:
        html, got = capture(ctx, LIST, (API,))
        listing = next((j["InstantGames"] for u, j in got if isinstance(j, dict) and "count=" in u and j.get("InstantGames")), None)
        if not listing:
            raise RuntimeError("the list page did not load its game list")
        links = sorted(set(re.findall(r'href="(https://www\.oregonlottery\.org/scratch-its/[a-z0-9-]+/)"', html)))
        links = [l for l in links if not l.endswith("/list/")]
        current = {str(g["GameNumber"]): g for g in listing if not g.get("GameEndDate") or g["GameEndDate"][:10] >= today}
        for link in links:
            try:
                _, got = capture(ctx, link, (API,), settle_ms=1500)
            except Exception:  # noqa: BLE001
                continue
            rec = next((j["InstantGames"][0] for u, j in got if "includePrizeTiers=true" in u and isinstance(j, dict) and j.get("InstantGames")), None)
            if not rec or str(rec.get("GameNumber")) not in current:
                continue
            n = str(rec["GameNumber"])
            current.pop(n)
            price = float(rec.get("TicketPrice") or 0)
            tiers = []
            for t in rec.get("PrizeTiers") or []:
                amt = float(t.get("PrizeAmount") or 0)
                label = f"${amt:,.0f}"
                value, annuity = parse_prize_label(label, price)
                total, unpaid = int(t.get("PrizesTotal") or 0), int(t.get("PrizesRemaining") or 0)
                tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": int(t.get("PrizesWon") or total - unpaid)})
            games.append({
                "game_number": n,
                "name": (rec.get("GameNameTitle") or "").strip(),
                "price": price,
                "odds": float(rec["OverallOdds"]) if rec.get("OverallOdds") else None,
                "odds_label": f"1 in {rec['OverallOdds']}" if rec.get("OverallOdds") else "",
                "release_date": (rec.get("DateAvailable") or "")[:10],
                "end_date": (rec.get("ValidationEndDate") or "")[:10],
                "top_prize_remaining": int(rec.get("TopPrizesRemaining") or 0),
                "url": link,
                "tiers": tiers,
                "notes": [],
            })
    return games
