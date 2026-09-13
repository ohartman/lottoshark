"""Michigan. michiganlottery.com is a React app over a GraphQL endpoint. Two queries:
prizes remaining for every retail instant game (all tiers: starting and remaining) and
the CMS game list (price, overall odds, art, launch date), joined on the IGT game id."""
from __future__ import annotations

from ..fetch import get_json
from ..html import money, odds
from ..metrics import parse_prize_label

STATE = {
    "code": "MI",
    "name": "Michigan",
    "sources": [{"label": "michiganlottery.com: Instant Games prizes remaining", "url": "https://www.michiganlottery.com/games/instant-games"}],
}
GQL = "https://www.michiganlottery.com/api/graphql"
Q_PRIZES = '{ getRetailTopPrizesRemainingByGameType(gameType: "INSTANT"){ cms_game_igt_id game_name prizesRemainingData { prize_level prize_amount prizes_remaining starting_amount } } }'
Q_CMS = "{ getCMSGames(removeHiddenGames: true){ name identifier igtId isInstantGame displayedTicketPrice displayedTopPrize overallOdds logoUrl dateAdded gameCategoryIdentifier } }"


def _q(query: str):
    d = get_json(GQL, json_body={"query": query})
    if "errors" in d and not d.get("data"):
        raise RuntimeError(f"GraphQL error: {d['errors']}")
    return d["data"]


def fetch_games() -> list[dict]:
    prizes = _q(Q_PRIZES)["getRetailTopPrizesRemainingByGameType"]
    cms = {c["igtId"]: c for c in _q(Q_CMS)["getCMSGames"] if c.get("gameCategoryIdentifier") == "RETAIL_INSTANT_GAMES_CATEGORY"}
    games = []
    for p in prizes:
        gid = p.get("cms_game_igt_id")
        c = cms.get(gid)
        if not c:
            continue  # ended games with no CMS listing have no price or odds
        price = money(c.get("displayedTicketPrice"))
        tiers = []
        for t in p.get("prizesRemainingData") or []:
            amt = float(t.get("prize_amount") or 0)
            label = f"${amt:,.0f}"
            value, annuity = parse_prize_label(label, price)
            total, unpaid = int(t.get("starting_amount") or 0), int(t.get("prizes_remaining") or 0)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        # The CMS top-prize label ("$1,000 a week for life") is more informative than the flat amount.
        top = (c.get("displayedTopPrize") or "").strip()
        if tiers and top and any(w in top.upper() for w in ("LIFE", "YEAR", "WEEK", "MONTH")):
            t0 = max(tiers, key=lambda t: t["value"])
            t0["label"], (t0["value"], t0["annuity"]) = f"{t0['label']} ({top})", parse_prize_label(top, price)
        logo = c.get("logoUrl") or ""
        games.append({
            "game_number": str(gid),
            "name": (c.get("name") or p.get("game_name") or "").strip(),
            "price": price,
            "odds": odds(c.get("overallOdds")),
            "odds_label": (c.get("overallOdds") or "").strip(),
            "release_date": (c.get("dateAdded") or "")[:10],
            "image": ("https:" + logo) if logo.startswith("//") else (logo or None),
            "url": f"https://www.michiganlottery.com/games/{c.get('identifier', '')}",
            "tiers": tiers,
            "notes": [],
        })
    return games
