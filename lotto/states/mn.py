"""Minnesota. The lottery's GameOn API lists every scratch game with price, odds, dates
and art, and gives total and remaining counts for prizes of $500 and up. Each game page
on mnlottery.com carries the full printed prize structure, so the smaller prizes get a
printed count and an estimated remaining count (see lotto/metrics.py)."""
from __future__ import annotations

import re

from ..fetch import fetch_many, get_json, get_text
from ..html import money, num, tables
from ..metrics import parse_prize_label

STATE = {
    "code": "MN",
    "name": "Minnesota",
    "sources": [{"label": "mnlottery.com: Scratch Games", "url": "https://www.mnlottery.com/games/scratch"}],
}
GW = "https://gateway.gameon.mnlottery.com/services/game/api/published-games"
LIST = GW + "?gameTypeId.in=1&sort=gameId,desc&excludeFeatured=false&page=0&size=200"
SITE = "https://www.mnlottery.com"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("$", "").replace(",", "")).strip("-")


def _structure(url: str) -> dict[str, int]:
    h = get_text(url, timeout=40)
    # each cell repeats its column label in a span for narrow screens: drop those
    h = re.sub(r'<span class="bulletin-matrix-table__label">.*?</span>', "", h, flags=re.S)
    for tb in tables(h):
        rows = {("$" + f"{money(r[0]):,.0f}"): num(r[2]) for r in tb if len(r) >= 3 and r[0].strip().startswith("$") and num(r[2])}
        if rows:
            return rows
    return {}


def fetch_games() -> list[dict]:
    recs = get_json(LIST).get("content", [])
    links = set(re.findall(r'href="(?:https://www\.mnlottery\.com)?(/games/scratch/[a-z0-9-]+)"', get_text(SITE + "/games/scratch")))
    by_suffix = {l.rsplit("-", 1)[1]: l for l in links if re.search(r"-\d{4}$", l)}
    by_slug = {l.rsplit("/", 1)[1]: l for l in links}
    # the same link with any trailing "-2026" / "-2107" removed: "xtreme-cash-2026" -> "xtreme-cash"
    by_base = {re.sub(r"-\d+$", "", l.rsplit("/", 1)[1]): l for l in links}

    def _slug_k(name: str) -> str:
        """"$500,000 Multiplier" -> "500k-multiplier", "$1,000,000 Cash" -> "1m-cash"."""
        n = re.sub(r"\$?(\d+),000,000", lambda m: m.group(1) + "m", name)
        n = re.sub(r"\$?(\d+),000", lambda m: m.group(1) + "k", n)
        return _slug(n)

    def candidates(g: dict) -> list[str]:
        gid = str(g.get("gameId") or "")
        s = _slug(g.get("name") or "")
        out = []
        if gid in by_suffix:
            out.append(SITE + by_suffix[gid])
        for k in (s, s + "-" + gid, _slug_k(g.get("name") or "")):
            if k in by_slug:
                out.append(SITE + by_slug[k])
            if k in by_base:
                out.append(SITE + by_base[k])
        out += [f"{SITE}/games/scratch/{s}-{gid}", f"{SITE}/games/scratch/{s}"]  # new games not yet listed
        return list(dict.fromkeys(out))

    def structure_for(g: dict) -> tuple[str | None, dict]:
        for u in candidates(g):
            try:
                st = _structure(u)
            except Exception:  # noqa: BLE001
                continue
            if st:
                return u, st
        return None, {}

    prizes = fetch_many(lambda g: get_json(f"{GW}/{g['id']}/prizes", timeout=40), recs)
    found = fetch_many(structure_for, recs)
    pages = [f[0] if isinstance(f, tuple) else None for f in found]
    structs = [f[1] if isinstance(f, tuple) else {} for f in found]
    games = []
    for g, page, pz, st in zip(recs, pages, prizes, structs):
        price = float(g.get("retailPrice") or 0)
        known = {}
        if isinstance(pz, list):
            for t in pz:
                known["$" + f"{money(t.get('prize')):,.0f}"] = (int(t.get("totalPrizes") or 0), int(t.get("remainingPrizes") or 0))
        st = st if isinstance(st, dict) else {}
        tiers = []
        for label, total in (st or {}).items():
            value, annuity = parse_prize_label(label, price)
            if label in known:
                total, unpaid = known[label][0] or total, known[label][1]
            else:
                unpaid = None
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid})
        for label, (total, unpaid) in known.items():
            if label not in st:
                value, annuity = parse_prize_label(label, price)
                tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid})
        notes = ["Minnesota publishes remaining counts only for prizes of $500 and up; smaller prizes are estimated."]
        if not st:
            notes.append("The full prize structure for this game was not found on the state's site, so only the published tiers are shown.")
        games.append({
            "game_number": str(g.get("gameId") or g["id"]),
            "name": (g.get("name") or "").strip(),
            "price": price,
            "odds": float(g["overallOdds"]) if g.get("overallOdds") else None,
            "odds_label": f"1 in {g['overallOdds']}" if g.get("overallOdds") else "",
            "release_date": (g.get("playBegin") or "")[:10],
            "end_date": (g.get("playExpiry") or "")[:10],
            "image": g.get("ticketPosImage") or g.get("ticketFullImage"),
            "url": page or STATE["sources"][0]["url"],
            "tiers": tiers,
            "notes": notes,
        })
    return games
