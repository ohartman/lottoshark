"""Oklahoma. oklottery.com is a Next.js site; the server-component payload (RSC: 1
header) of each game page embeds prizeDetails with every tier's total and remaining,
plus odds, price, dates, tickets printed and art."""
from __future__ import annotations

import json
import re
from datetime import date

from ..fetch import fetch_many, get_text
from ..html import odds
from ..metrics import parse_prize_label

STATE = {
    "code": "OK",
    "name": "Oklahoma",
    "sources": [{"label": "oklottery.com: Scratchers", "url": "https://oklottery.com/games/scratchers"}],
}
LIST = "https://oklottery.com/games/scratchers"
RSC = {"RSC": "1"}


def _clean(payload: str) -> str:
    return payload.replace('\\"', '"').replace("$$", "$")


def _slugs(payload: str) -> list[str]:
    return sorted(set(re.findall(r'"slug":"(\d+-[a-z0-9-]+)"', _clean(payload))))


def _game(slug: str) -> dict:
    p = _clean(get_text(f"{LIST}/{slug}", timeout=40, headers=RSC))
    i = p.find('{"howToPlay"')
    if i < 0:
        raise RuntimeError(f"no game record for {slug}")
    depth = 0
    for j in range(i, len(p)):
        if p[j] == "{":
            depth += 1
        elif p[j] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(p[i:j + 1])
    raise RuntimeError(f"unterminated game record for {slug}")


def fetch_games() -> list[dict]:
    slugs = _slugs(get_text(LIST, headers=RSC))
    recs = fetch_many(_game, slugs)
    today = date.today().isoformat()
    games = []
    for slug, g in zip(slugs, recs):
        if not isinstance(g, dict) or g.get("pullTab") or not g.get("prizeDetails"):
            continue  # pull tabs, and ended games whose prize table the state has removed
        claim = (g.get("claimEndDate") or "")[:10]
        price = float(g.get("ticketPrice") or 0)
        tiers = []
        for block in g.get("prizeDetails") or []:
            for t in block.get("matches") or []:
                label = str(t.get("prize") or "").strip()
                if re.fullmatch(r"\$\d+", label):
                    label = f"${int(label[1:]):,}"
                value, annuity = parse_prize_label(label, price)
                total, unpaid = int(t.get("totalPrizes") or 0), int(t.get("remainingPrizes") or 0)
                tiers.append({"label": label, "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
        end = (g.get("endDate") or "")[:10]
        games.append({
            "game_number": str(g.get("gameNumber") or slug.split("-")[0]),
            "name": (g.get("title") or "").strip(),
            "price": price,
            "odds": odds(g.get("odds")),
            "odds_label": (g.get("odds") or "").strip(),
            "tickets_printed": int(g.get("totalTickets") or 0) or None,
            "release_date": (g.get("startDate") or "")[:10],
            "end_date": (g.get("claimEndDate") or "")[:10],
            "image": ((g.get("image") or {}).get("url")) if isinstance(g.get("image"), dict) else None,
            "url": f"{LIST}/{slug}",
            "pdf": g.get("rulesPdf") if isinstance(g.get("rulesPdf"), str) else "",
            "tiers": tiers,
            "notes": (["Past its prize-claim deadline."] if claim and claim < today else
                      ["Sales have ended; prizes can still be claimed."] if end and end < today else []),
        })
    return games
