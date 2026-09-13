"""Pennsylvania. The lottery site lists every game's six largest prizes with remaining
counts, and each game page gives the overall odds; neither says how many prizes were
printed. That structure is in the game's rules notice in the Pennsylvania Bulletin
(a table of prize, odds and approximate winners per print run), found by searching the
Bulletin for the game number. Lower tiers have no remaining count, so the return is an
estimate with a range (see lotto/metrics.py)."""
from __future__ import annotations

import re

from ..fetch import fetch_many, get_text
from ..html import money, num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "PA",
    "name": "Pennsylvania",
    "sources": [
        {"label": "palottery.pa.gov: Scratch-Offs Prizes Remaining", "url": "https://www.palottery.pa.gov/Scratch-Offs/Prizes-Remaining.aspx"},
        {"label": "Pennsylvania Bulletin: instant lottery game notices", "url": "https://www.pacodeandbulletin.gov/"},
    ],
}
SITE = "https://www.palottery.pa.gov"
REMAINING = SITE + "/Scratch-Offs/Prizes-Remaining.aspx"
GAME = SITE + "/Scratch-Offs/View-Scratch-Off.aspx?id={id}"
BULLETIN = "https://www.pacodeandbulletin.gov"
SEARCH = BULLETIN + "/webforms/searchbulletin.aspx?query=%22PA-{n}%22"
FLAGS = ("Second-Chance Eligible", "Available on iLottery", "NEW", "Second Chance Eligible")


def _notice_url(n: str) -> str | None:
    h = get_text(SEARCH.format(n=n), timeout=60)
    for u, t in re.findall(r'href="([^"]*Display/pabull[^"]*)"[^>]*>(.*?)</a>', h, re.S):
        title = text(t)
        if re.search(rf"Instant Lottery Game\s+{n}\b", title, re.I):
            return u.replace("http://", "https://").split("&search=")[0]
    return None


def _notice(n: str) -> dict:
    url = _notice_url(n)
    if not url:
        return {}
    h = get_text(url, timeout=60)
    t = text(h)
    printed = re.search(r"Approximately\s+([\d,]+)\s+tickets will be printed", t, re.I)
    structure: dict[float, int] = {}
    for tb in tables(h):
        if not tb or not tb[0]:
            continue
        head = [c.lower() for c in tb[0]]
        try:
            wi = next(i for i, c in enumerate(head) if c.startswith("win:") or c == "win")
            ci = next(i for i, c in enumerate(head) if "winners" in c)
        except StopIteration:
            continue
        for r in tb[1:]:
            if len(r) <= max(wi, ci) or not r[wi].strip().startswith("$"):
                continue
            v = money(r[wi])
            if v:
                structure[v] = structure.get(v, 0) + num(r[ci])
        if structure:
            break
    return {"url": url, "tickets_printed": num(printed.group(1)) if printed else 0, "structure": structure}


def _odds(gid: str) -> str:
    t = text(get_text(GAME.format(id=gid), timeout=40))
    m = re.search(r"Overall chances of winning a prize:?\s*1\s*[:in]+\s*([\d.]+)", t, re.I)
    return m.group(1) if m else ""


def fetch_games() -> list[dict]:
    h = get_text(REMAINING, timeout=90)
    rows = []
    for tr in re.findall(r"<tr[^>]*>.*?</tr>", h, re.S):
        cells = [r for t in tables("<table>" + tr + "</table>") for r in t]
        if not cells or len(cells[0]) < 5:
            continue
        n = re.search(r"\b(\d{3,4})\b", cells[0][0])
        if not n:
            continue
        gid = re.search(r"View-Scratch-Off\.aspx\?id=(\d+)", tr)
        rows.append((n.group(1), cells[0], gid.group(1) if gid else None))
    notices = dict(zip([r[0] for r in rows], fetch_many(lambda r: _notice(r[0]), rows)))
    page_odds = dict(zip([r[0] for r in rows], fetch_many(lambda r: _odds(r[2]) if r[2] else "", rows)))
    games = []
    for n, c, gid in rows:
        name = c[1]
        for f in FLAGS:
            name = name.replace(f, "")
        name = re.sub(r"\s+", " ", name).strip(" -™®")
        price = money(c[2])
        labels = re.findall(r"\$[\d,]+(?:\.\d+)?", c[3])
        counts = [num(x) for x in c[4].split()]
        remaining = {money(l): k for l, k in zip(labels, counts)}
        nt = notices.get(n) if isinstance(notices.get(n), dict) else {}
        tiers = []
        for v, total in sorted((nt.get("structure") or {}).items(), reverse=True):
            label = f"${v:,.0f}"
            value, annuity = parse_prize_label(label, price)
            left = remaining.get(v)
            # the notice's counts are approximate; a reorder can leave more prizes than it lists
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": max(total, left or 0), "unpaid": left})
        if not tiers:
            for v, k in remaining.items():
                label = f"${v:,.0f}"
                value, annuity = parse_prize_label(label, price)
                tiers.append({"label": label, "value": value, "annuity": annuity, "total": 0, "unpaid": k})
        o = page_odds.get(n) if isinstance(page_odds.get(n), str) else ""
        notes = ["Pennsylvania publishes remaining counts for its six largest prizes; the printed prize structure comes from the game's notice in the Pennsylvania Bulletin, and the rest is estimated."]
        if not nt.get("structure"):
            notes.append("No Pennsylvania Bulletin notice was found for this game, so there is no estimate.")
        games.append({
            "game_number": n,
            "name": name,
            "price": price,
            "odds": float(o) if o else None,
            "odds_label": f"1 in {o}" if o else "",
            "tickets_printed": nt.get("tickets_printed") or None,
            "top_prize_remaining": counts[0] if counts else 0,
            "url": GAME.format(id=gid) if gid else REMAINING,
            "pdf": nt.get("url", ""),
            "tiers": tiers,
            "notes": notes,
        })
    return games
