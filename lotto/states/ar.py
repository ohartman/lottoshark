"""Arkansas. myarkansaslottery.com sits behind a Cloudflare challenge that plain requests
cannot pass, so a headless browser loads the instant-games listing and each game page,
which has a table of every tier's total and estimated remaining prizes, plus price,
overall odds, game number and launch date."""
from __future__ import annotations

import re
from datetime import datetime

from ..browser import Session
from ..html import money, num, odds, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "AR",
    "name": "Arkansas",
    "sources": [{"label": "myarkansaslottery.com: Instant Games", "url": "https://www.myarkansaslottery.com/games/instant"}],
}
SITE = "https://www.myarkansaslottery.com"


def _tier_table(gh: str):
    return next((x for x in tables(gh) if x and x[0] and "tier" in x[0][0].lower()), None)


def fetch_games() -> list[dict]:
    games = []
    with Session() as br:
        # the listing renders its cards lazily as the page scrolls
        page = br.ctx.new_page()
        try:
            page.goto(SITE + "/games/instant", wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_selector("a[href^='/games/']", timeout=45000)
            except Exception:  # noqa: BLE001
                pass
            for _ in range(8):
                page.mouse.wheel(0, 4000)
                page.wait_for_timeout(1200)
            h = page.content()
        finally:
            page.close()
        links = [l for l in sorted(set(re.findall(r'href="(/games/[a-z0-9-]+)"', h))) if l not in ("/games/instant", "/games/draw")]
        if not links:
            raise RuntimeError("the instant-games listing did not load (challenge not cleared)")
        for link in links:
            gh = br.load(SITE + link, "table", 500, 30000)
            tb = _tier_table(gh)
            if not tb:
                continue  # draw games and the odd nav link have no tier table
            t = text(gh)
            price = money((re.search(r"Ticket price:?\s*\$([\d.]+)", t, re.I) or [None, "0"])[1])
            o = re.search(r"Overall odds of winning:?\s*(1 in [\d.]+)", t, re.I)
            n = re.search(r"Game No\.?\s*(\d+)", t)
            launch = re.search(r"Launch Date:?\s*(\d{1,2}/\d{1,2}/\d{4})", t)
            redeem = re.search(r"Last Redeem Date:?\*?\s*(\d{1,2}/\d{1,2}/\d{4})", t)
            name = re.search(r"<h1[^>]*>(.*?)</h1>", gh, re.S)
            img = re.search(r'src="([^"]*/instant/front/[^"]*)"', gh)
            tiers = []
            for r in tb[1:]:
                if len(r) < 3 or not re.match(r"[\d,]+(\.\d+)?$", r[0].strip()):
                    continue
                label = f"${money(r[0]):,.0f}"
                value, annuity = parse_prize_label(label, price)
                total, unpaid = num(r[1]), num(r[2])
                tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
            fmt = lambda m: datetime.strptime(m.group(1), "%m/%d/%Y").date().isoformat() if m else ""
            games.append({
                "game_number": n.group(1) if n else link.rsplit("/", 1)[1],
                "name": text(name.group(1)) if name else link.rsplit("/", 1)[1].replace("-", " ").title(),
                "price": price,
                "odds": odds(o.group(1)) if o else None,
                "odds_label": o.group(1) if o else "",
                "release_date": fmt(launch),
                "end_date": fmt(redeem),
                "image": img.group(1) if img else None,
                "url": SITE + link,
                "tiers": tiers,
                "notes": [],
            })
    return games
