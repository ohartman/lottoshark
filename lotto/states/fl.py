"""Florida. One JSON call (the site's own scratch-games API, which wants an x-partner
header) returns every game with all tiers: printed, paid, remaining, plus price, odds and
dates. Ticket art comes from the site's content JSON."""
from __future__ import annotations

from datetime import date

from ..fetch import get_json
from ..html import money
from ..metrics import parse_prize_label

STATE = {
    "code": "FL",
    "name": "Florida",
    "sources": [{"label": "floridalottery.com: Top Remaining Prizes", "url": "https://floridalottery.com/games/scratch-offs/top-remaining-prizes"}],
}
API = "https://apim-website-prod-eastus.azure-api.net/scratchgamesapp/getscratchinfo"
ART = "https://floridalottery.com/content/flalottery-web/us/en/games/scratch-offs.scratch-offs.json"


def fetch_games() -> list[dict]:
    recs = get_json(API, headers={"x-partner": "web"})
    art = {}
    try:
        for a in get_json(ART).get("data", []):
            if a.get("teaserImage"):
                art[str(a["id"])] = "https://floridalottery.com" + a["teaserImage"]
    except Exception:  # noqa: BLE001 - art is optional
        pass
    games = []
    for s in recs:
        price = float(s.get("TicketPrice") or 0)
        tiers = []
        for t in s.get("OddsTiers") or []:
            raw = (t.get("PrizeAmount") or "").strip()
            label = f"${money(raw):,.0f}" if raw.startswith("$") and money(raw) else raw
            value, annuity = parse_prize_label(label, price)
            total, unpaid = int(t.get("TotalPrizes") or 0), int(t.get("PrizesRemaining") or 0)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": int(t.get("PrizesPaid") or total - unpaid)})
        gid = str(s["Id"])
        notes = []
        if any(t["total"] == 0 for t in tiers):
            notes.append("The state's prize table for this game is incomplete (some tiers show zero prizes printed).")
            tiers = [t for t in tiers if t["total"]]
        if s.get("EndDate") and (s.get("EndDate") or "")[:10] < date.today().isoformat():
            notes.append("Sales have ended; prizes can still be claimed.")
        games.append({
            "game_number": gid,
            "name": (s.get("GameName") or "").strip(),
            "price": price,
            "odds": float(s["OverallOdds"]) if s.get("OverallOdds") else None,
            "odds_label": f"1 in {s['OverallOdds']}" if s.get("OverallOdds") else "",
            "release_date": (s.get("LaunchDate") or "")[:10],
            "end_date": (s.get("RedemptionDate") or "")[:10],
            "image": art.get(gid),
            "url": f"https://floridalottery.com/games/scratch-offs/{gid}",
            "pdf": f"https://files.floridalottery.com/exptkt/{gid}_WinningTicketInformation.pdf",
            "tiers": tiers,
            "notes": notes,
        })
    return games
