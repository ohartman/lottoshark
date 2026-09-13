"""Ohio. ohiolottery.com renders its scratch-off pages in the browser from an API the
page authorises itself. A headless browser loads the public prizes-remaining page (every
game with every tier's printed and remaining counts) and the scratch-offs listing (price,
odds, dates, page path); this code never touches the token."""
from __future__ import annotations

import re

from ..browser import browser, capture
from ..html import odds
from ..metrics import parse_prize_label

STATE = {
    "code": "OH",
    "name": "Ohio",
    "sources": [{"label": "ohiolottery.com: Scratch-Offs Prizes Remaining", "url": "https://www.ohiolottery.com/games/scratch-offs/prizes-remaining"}],
}
SITE = "https://www.ohiolottery.com"


def _date(s) -> str:
    s = (s or "")[:10]
    return "" if s.startswith("0001") else s


def fetch_games() -> list[dict]:
    with browser() as ctx:
        _, got = capture(ctx, SITE + "/games/scratch-offs/prizes-remaining", ("GetFullPrizesRemainingList",))
        prizes = next((j["data"] for _, j in got if isinstance(j, dict) and isinstance(j.get("data"), list)), None)
        if not prizes:
            raise RuntimeError("the prizes-remaining page did not load its prize list")
        _, got = capture(ctx, SITE + "/games/scratch-offs", ("GetAllGames",))
        meta = {}
        for _, j in got:
            d = j.get("data") if isinstance(j, dict) else None
            for lst in (d.values() if isinstance(d, dict) else []):
                for g in lst or []:
                    meta[str(g.get("gameNumber"))] = g
    games = []
    for p in prizes:
        n = str(p.get("gameCode") or "").strip()
        m = meta.get(n, {})
        price = float(p.get("ticketPrice") or m.get("gamePrice") or 0)
        tiers = []
        for t in p.get("prizeRemainingValues") or []:
            amt = float(t.get("prizeValue") or 0)
            label = f"${amt:,.0f}" if amt else "TV show entry"
            value, annuity = parse_prize_label(label, price) if amt else (0.0, False)
            total, unpaid = int(t.get("totalPrizes") or 0), int(t.get("prizesLeft") or 0)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        o = (m.get("oddsOfWinning") or "").strip()
        games.append({
            "game_number": n,
            "name": (p.get("gameName") or m.get("gameName") or "").strip(),
            "price": price,
            "odds": odds(o),
            "odds_label": (re.search(r"1 in [\d.]*\d", o) or [""])[0],
            "release_date": _date(m.get("onSaleDate")),
            "end_date": _date(m.get("lastDayToRedeem")),
            "url": SITE + m["nodeAliasPath"] if m.get("nodeAliasPath") else STATE["sources"][0]["url"],
            "tiers": tiers,
            "notes": ([] if m else ["Not on the Ohio Lottery game list (likely off sale); odds unknown."])
                     + (["Cash Explosion TV-show entries are prizes too, but they are counted at $0 here."] if any(t["value"] == 0 for t in tiers) else []),
        })
    return games
