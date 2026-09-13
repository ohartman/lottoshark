"""Massachusetts. The masslottery.com site is a React app over a public JSON API:
  /api/v1/games                         every game with price, odds, start date, art
  /api/v1/instant-game-prizes?gameID=N  one game's prize tiers: printed, paid, remaining
"""
from __future__ import annotations

from ..fetch import fetch_many, get_json
from ..html import odds
from ..metrics import parse_prize_label

STATE = {
    "code": "MA",
    "name": "Massachusetts",
    "sources": [{"label": "masslottery.com: Instant Tickets", "url": "https://www.masslottery.com/games/instant"}],
}
API = "https://www.masslottery.com/api/v1"


def _img(g: dict) -> str | None:
    u = (g.get("icon") or {}).get("url") or ((g.get("gameCollectionIcon") or {}).get("mobileImage") or {}).get("url")
    return "https:" + u if u and u.startswith("//") else u


def fetch_games() -> list[dict]:
    listing = [g for g in get_json(f"{API}/games") if g.get("gameType") == "Scratch"]
    prizes = fetch_many(lambda g: get_json(f"{API}/instant-game-prizes?gameID={g['id']}", timeout=40), listing)
    games = []
    for g, p in zip(listing, prizes):
        price = float(g.get("price") or 0)
        notes, tiers = [], []
        if isinstance(p, Exception):
            notes.append("Prize-tier data could not be fetched today.")
        else:
            price = float(p.get("ticketCost") or price)
            for t in p.get("prizeTiers") or []:
                label = (t.get("prizeDescription") or f"${t.get('prizeAmount')}").strip()
                value, annuity = parse_prize_label(label, price)
                if value == 0 and t.get("prizeAmount"):
                    value = float(t["prizeAmount"])
                total = int(t.get("totalPrizes") or 0)
                unpaid = int(t.get("prizesRemaining") or 0)
                tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": int(t.get("paidPrizes") or total - unpaid)})
        games.append({
            "game_number": str(g["id"]),
            "name": (g.get("name") or "").strip(),
            "price": price,
            "odds": odds(g.get("odds")),
            "odds_label": (g.get("odds") or "").strip(),
            "release_date": g.get("startDate") or "",
            "end_date": g.get("expirationDate") or "",
            "top_prize_label": (g.get("topPrizeDescription") or "").strip() or None,
            "image": _img(g),
            "url": f"https://www.masslottery.com/games/instant/{g.get('identifier', '')}",
            "tiers": tiers,
            "notes": notes,
        })
    return games
