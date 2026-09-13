"""South Dakota. lottery.sd.gov proxies IGT's instant-games API (all tiers, printed and
paid, cents) and runs a headless WordPress whose GraphQL gives the slug, status and art
for each game. Overall odds appear only as text on the game's page."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from ..fetch import fetch_many, get_json, get_text
from ..metrics import parse_prize_label

STATE = {
    "code": "SD",
    "name": "South Dakota",
    "sources": [{"label": "lottery.sd.gov: Scratch Games", "url": "https://lottery.sd.gov/scratch-games/"}],
}
API = "https://lottery.sd.gov/api/igt/games/v1/instant-games/games"
API_PAGE = "https://lottery.sd.gov/api/igt/games/v1/instant-games/games/page?size=100&start-item={n}"
GQL = "https://lottery-admin.sd.gov/graphql"
QUERY = """{ games(first:100, after:%s, where:{taxQuery:{taxArray:{field:SLUG,operator:IN,taxonomy:GAMETYPE,terms:["scratch-tickets"]}}}){
  pageInfo{hasNextPage endCursor} nodes{ slug title acf{igtIdentifier} gameOptions{nodes{slug}} featuredImage{node{sourceUrl}} } } }"""


def _ms(v) -> str:
    return datetime.fromtimestamp(v / 1000, tz=timezone.utc).date().isoformat() if v else ""


def _wp() -> dict[str, dict]:
    out, after = {}, "null"
    while True:
        d = get_json(GQL, json_body={"query": QUERY % after})["data"]["games"]
        for n in d["nodes"]:
            gid = ((n.get("acf") or {}).get("igtIdentifier") or "").strip()
            if gid:
                out[gid] = n
        if not d["pageInfo"]["hasNextPage"]:
            return out
        after = '"%s"' % d["pageInfo"]["endCursor"]


def _odds(slug: str) -> str:
    m = re.search(r"Overall Odds:\s*1\s*[:in]+\s*([\d.]+)", get_text(f"https://lottery.sd.gov/game/{slug}/", timeout=40))
    return m.group(1) if m else ""


def fetch_games() -> list[dict]:
    recs, start = [], 0
    data = get_json(API)
    while True:
        recs += data.get("games", [])
        if not data.get("nextPageUrl"):
            break
        start += 100
        data = get_json(API_PAGE.format(n=start))
    active = [s for s in recs if s.get("validationStatus") == "ACTIVE"]
    wp = _wp()
    slugs = [wp.get(str(s["gameId"]), {}).get("slug") for s in active]
    odds_txt = fetch_many(lambda sl: _odds(sl) if sl else "", slugs)
    games = []
    for s, slug, o in zip(active, slugs, odds_txt):
        gid = str(s["gameId"])
        price = (s.get("ticketPrice") or 0) / 100
        tiers = []
        for t in s.get("prizeTiers") or []:
            amt = (t.get("prizeAmount") or 0) / 100
            label = f"${amt:,.0f}"
            value, annuity = parse_prize_label(label, price)
            total, paid = int(t.get("winningTickets") or 0), int(t.get("paidTickets") or 0)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "paid": paid, "unpaid": max(total - paid, 0)})
        o = o if isinstance(o, str) else ""
        w = wp.get(gid, {})
        games.append({
            "game_number": gid,
            "name": (w.get("title") or s.get("gameName") or "").strip(),
            "price": price,
            "odds": float(o) if o else None,
            "odds_label": f"1 in {o}" if o else "",
            "release_date": _ms(s.get("startDistributionDate")),
            "end_date": _ms(s.get("disableDate")),
            "image": ((w.get("featuredImage") or {}).get("node") or {}).get("sourceUrl"),
            "url": f"https://lottery.sd.gov/game/{slug}/" if slug else STATE["sources"][0]["url"],
            "tiers": tiers,
            "notes": [],
        })
    return games
