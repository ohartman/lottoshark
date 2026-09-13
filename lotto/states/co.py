"""Colorado. The Scratch Insider table lists every game with price, odds, dates, payout
percentage and how many top prizes remain; each game page has the full printed prize
structure. Only the top prize has a remaining count, so the return is an estimate
with a range (see lotto/metrics.py)."""
from __future__ import annotations

import re
from datetime import datetime

from ..fetch import fetch_many, get_text
from ..html import money, num, odds, tables
from ..metrics import parse_prize_label

STATE = {
    "code": "CO",
    "name": "Colorado",
    "sources": [{"label": "coloradolottery.com: Scratch Insider", "url": "https://www.coloradolottery.com/en/player-tools/scratch-insider/"}],
}
SITE = "https://www.coloradolottery.com"
INSIDER = SITE + "/en/player-tools/scratch-insider/"


def _date(s: str) -> str:
    s = s.replace(".", "").replace("Sept ", "Sep ").strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return ""


def _structure(url: str) -> list[tuple[str, int]]:
    h = get_text(url, timeout=40)
    for tb in tables(h):
        rows = [(r[0], num(r[1])) for r in tb if len(r) >= 2 and r[0].startswith("$")]
        if rows:
            return rows
    return []


def fetch_games() -> list[dict]:
    h = get_text(INSIDER)
    # Each row links to its game page; the table's "game number" is not the one in the URL.
    rows, links = [], {}
    for tr in re.findall(r"<tr[^>]*>.*?</tr>", h, re.S):
        cells = [r for t in tables("<table>" + tr + "</table>") for r in t]
        if not cells or len(cells[0]) < 11 or not cells[0][1].isdigit():
            continue
        u = re.search(r'href="([^"]*games/scratch/game/[^"]*)"', tr)
        rows.append(cells[0])
        if u:
            links[cells[0][1]] = u.group(1) if u.group(1).startswith("http") else SITE + u.group(1)
    structs = dict(zip([r[1] for r in rows], fetch_many(lambda r: _structure(links[r[1]]) if r[1] in links else [], rows)))
    games = []
    for r in rows:
        n, price = r[1], money(r[2])
        top_label, top_total, top_left = r[5].strip(), num(r[6]), num(r[7])
        tiers = []
        for label, total in (structs.get(n) if isinstance(structs.get(n), list) else []):
            value, annuity = parse_prize_label(label, price)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": None})
        if tiers:
            top = max(tiers, key=lambda t: t["value"])
            top["unpaid"] = top_left
            if top_total and top_total != top["total"]:
                top["total"] = top_total
        else:
            value, annuity = parse_prize_label(top_label, price)
            tiers = [{"label": top_label, "value": value, "annuity": annuity, "total": top_total, "unpaid": top_left}]
        payout = re.search(r"[\d.]+", r[10] or "")
        notes = ["Colorado publishes a remaining count only for the top prize; the rest is estimated."]
        if payout:
            notes.append(f"The state's stated payout is {payout.group(0)}% of sales.")
        games.append({
            "game_number": n,
            "name": r[0].replace("➞", "").strip(),
            "price": price,
            "odds": odds(r[8]),
            "odds_label": (re.search(r"1 in [\d.]+", r[8]) or [""])[0],
            "release_date": _date(r[3]),
            "end_date": _date(r[4]),
            "top_prize_label": top_label or None,
            "top_prize_remaining": top_left,
            "image": None,
            "url": links.get(n, INSIDER),
            "tiers": tiers,
            "notes": notes,
        })
    return games
