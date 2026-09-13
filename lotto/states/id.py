"""Idaho. Drupal JSON:API on idaholottery.com: every scratch game with price, odds,
percent sold, dates, thumbnail and a full prize table (printed, amount, remaining, tier
odds). Tiers under $25 sometimes have no remaining count; those are filled in from the
state's own percent-sold figure, which is the same assumption the metrics use anyway."""
from __future__ import annotations

from datetime import date

from ..fetch import get_json
from ..html import odds
from ..metrics import parse_prize_label

STATE = {
    "code": "ID",
    "name": "Idaho",
    "sources": [{"label": "idaholottery.com: Scratch Games remaining prizes", "url": "https://www.idaholottery.com/games/scratch?view=remaining_prizes"}],
}
API = "https://www.idaholottery.com/jsonapi/node/games?filter[field_game_category.name]=Scratch&page[limit]=50&include=field_game_thumbnail"
SITE = "https://www.idaholottery.com"


def fetch_games() -> list[dict]:
    url, nodes, files = API, [], {}
    while url:
        d = get_json(url.replace("[", "%5B").replace("]", "%5D"))
        nodes += d.get("data", [])
        for inc in d.get("included", []):
            if inc.get("type") == "file--file":
                files[inc["id"]] = (inc.get("attributes", {}).get("uri") or {}).get("url")
        url = (d.get("links", {}).get("next") or {}).get("href")
    today = date.today().isoformat()
    games = []
    for n in nodes:
        a = n.get("attributes", {})
        exp = (a.get("field_expiration_date") or "")[:10]
        claim = (a.get("field_final_claim_date") or "")[:10]
        if exp and exp < today and (not claim or claim < today):
            continue
        price = float(a.get("field_price") or 0)
        pct_sold = float(a.get("field_percent_sold") or 0)
        rows = ((a.get("field_full_odds_and_prizes") or {}).get("value") or {})
        tiers, filled = [], False
        for k, r in rows.items():
            if k == "0" or not isinstance(r, dict) or not str(r.get("0", "")).strip().isdigit():
                continue
            total = int(r["0"])
            amt = str(r.get("1", "")).strip()
            label = f"${float(amt):,.0f}" if amt.replace(".", "").isdigit() else amt
            value, annuity = parse_prize_label(label, price)
            rem = str(r.get("2", "")).strip()
            if rem.isdigit():
                unpaid = int(rem)
            else:
                unpaid, filled = round(total * (1 - pct_sold)), True
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        thumb = ((n.get("relationships", {}).get("field_game_thumbnail") or {}).get("data") or {}).get("id")
        img = files.get(thumb)
        notes = []
        if filled:
            notes.append("Idaho does not publish remaining counts for prizes under $25; those are estimated from the state's percent-sold figure.")
        if exp and exp < today:
            notes.append("Sales have ended; prizes can still be claimed.")
        games.append({
            "game_number": str(a.get("field_game_id") or "").strip(),
            "name": (a.get("title") or "").strip(),
            "price": price,
            "odds": odds(a.get("field_odds")),
            "odds_label": (a.get("field_odds") or "").replace(":", " in ").strip(),
            "release_date": (a.get("field_entry_date") or "")[:10],
            "end_date": claim,
            "image": img.replace("http://", "https://") if img else None,
            "url": SITE + ((a.get("path") or {}).get("alias") or "/games/scratch"),
            "tiers": tiers,
            "notes": notes,
        })
    return games
