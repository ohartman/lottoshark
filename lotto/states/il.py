"""Illinois. illinoislottery.com sits behind a Cloudflare challenge that plain requests
cannot pass, so a headless browser loads the unpaid-prizes page (every game with every
tier's total and unclaimed counts, price and game number) and the game hub's pages, whose
game pages give the overall odds. Games no longer on the hub have no odds and no estimate."""
from __future__ import annotations

import re

from ..browser import Session
from ..html import money, num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "IL",
    "name": "Illinois",
    "sources": [{"label": "illinoislottery.com: Unpaid Instant Game Prizes", "url": "https://www.illinoislottery.com/about-the-games/unpaid-instant-games-prizes"}],
}
SITE = "https://www.illinoislottery.com"
UNPAID = SITE + "/about-the-games/unpaid-instant-games-prizes"
HUB = SITE + "/games-hub/instant-tickets"


def fetch_games() -> list[dict]:
    with Session() as br:
        h = br.load(UNPAID, "table", 1500, 45000)
        table = next((t for t in tables(h) if len(t) > 3 and t[0] and t[0][0].lower().startswith("name")), None)
        if not table:
            raise RuntimeError("the unpaid-prizes table did not render")
        links: set[str] = set()
        for pg in range(1, 12):  # the hub shows 20 games a page
            found = set(re.findall(r'href="(/games-hub/instant-tickets/[^"]+)"', br.load(f"{HUB}?filter=all&page={pg}", "a[href*='/games-hub/instant-tickets/']")))
            new = found - links
            links |= found
            if not new:
                break
        meta: dict[str, dict] = {}
        for link in sorted(links):
            gh = br.load(SITE + link, "text=Game Number", 500, 15000)
            t = text(gh)
            n = re.search(r"Game Number\s*(\d+)", t)
            if not n:
                continue
            # phrased either "Overall Odds 1 in 3.93" or "Overall Odds 4.08 to 1"
            o = re.search(r"Overall Odds\s*(?:1 in\s*([\d.]+)|([\d.]+)\s*to\s*1)", t)
            o_val = (o.group(1) or o.group(2)) if o else ""
            o = f"1 in {o_val}" if o_val else ""
            img = re.search(r'<img[^>]+src="([^"]*(?:instant|ticket)[^"]*\.(?:png|jpg|jpeg|webp)[^"]*)"', gh, re.I)
            meta[n.group(1)] = {"odds": o, "url": SITE + link, "image": (SITE + img.group(1)) if img and img.group(1).startswith("/") else (img.group(1) if img else None)}
    games = []
    for r in table[1:]:
        if len(r) < 6 or not r[2].strip():
            continue
        n = re.match(r"(\d+)", r[2].strip())
        if not n:
            continue
        n = n.group(1)
        price = money(r[1])
        labels = re.findall(r"\$[\d,]+", r[3])
        totals = [num(x) for x in r[4].split()]
        unclaimed = [num(x) for x in r[5].split()]
        tiers = []
        for label, total, left in zip(labels, totals, unclaimed):
            value, annuity = parse_prize_label(label, price)
            tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": left, "paid": max(total - left, 0)})
        m = meta.get(n, {})
        weeks = re.search(r"\((\d+)\)", r[2])
        games.append({
            "game_number": n,
            "name": re.sub(r"\s*\(\$[\d.]+\)\s*$", "", r[0]).strip(),
            "price": price,
            "odds": odds(m.get("odds")),
            "odds_label": m.get("odds", ""),
            "image": m.get("image"),
            "url": m.get("url", UNPAID),
            "tiers": tiers,
            "notes": ([] if m else ["Not on the Illinois Lottery game hub (likely off sale); odds unknown, so no estimate."])
                     + ([f"{weeks.group(1)} weeks in market."] if weeks else []),
        })
    return games
