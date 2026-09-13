"""Arizona. The lottery's public JSON API (api.arizonalottery.com/v2) lists every active
scratcher with all prize tiers: totalCount printed, count remaining, odds, price, dates.
The www site itself sits behind a bot challenge, so there are no ticket images."""
from __future__ import annotations

from ..fetch import fetch_many, get_json
from ..metrics import parse_prize_label

STATE = {
    "code": "AZ",
    "name": "Arizona",
    "sources": [{"label": "arizonalottery.com: Scratchers prizes remaining", "url": "https://www.arizonalottery.com/scratchers/"}],
}
API = "https://api.arizonalottery.com/v2"


def fetch_games() -> list[dict]:
    nums = sorted({int(r["gameNum"]) for r in get_json(f"{API}/scratchers/topprizes")})
    recs = fetch_many(lambda n: get_json(f"{API}/scratchers/{n}", timeout=40), nums)
    games = []
    for n, s in zip(nums, recs):
        if isinstance(s, Exception) or not isinstance(s, dict):
            continue
        price = float(s.get("ticketValue") or 0)
        tiers = []
        for t in s.get("prizeTiers") or []:
            label = (t.get("description") or t.get("displayTitle") or "").strip()
            value, annuity = parse_prize_label(label, price)
            if not value and t.get("prizeAmount"):
                value = float(t["prizeAmount"])
            total, unpaid = int(t.get("totalCount") or 0), int(t.get("count") or 0)
            tiers.append({"label": label, "value": value, "annuity": annuity or bool(s.get("hasAnnuityPrize") and t.get("tierLevel") == 1),
                          "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        end = (s.get("lastDate") or "")[:10]
        games.append({
            "game_number": str(s.get("gameNum") or n),
            "name": (s.get("gameName") or "").strip(),
            "price": price,
            "odds": float(s["gameOdds"]) if s.get("gameOdds") else None,
            "odds_label": f"1 in {s['gameOdds']}" if s.get("gameOdds") else "",
            "release_date": (s.get("beginDate") or "")[:10],
            "end_date": "" if end.startswith("2099") else end,
            "url": f"https://www.arizonalottery.com/scratchers/{n}/",
            "tiers": tiers,
            "notes": [],
        })
    return games
