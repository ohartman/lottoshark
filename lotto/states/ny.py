"""New York.

Two official, public, machine-readable sources:
  1. data.ny.gov dataset nzqa-7unk "Scratch-Off Game Daily Prize Status Report":
     one row per (game, prize tier) with prizes printed / paid / unpaid. Refreshed daily.
  2. nylottery.ny.gov Drupal JSON API api/v2/scratch_off_data: the list the website itself
     renders, with ticket price, overall odds, release date, claim deadline, art and the
     official odds PDF.
"""
from __future__ import annotations

import re
from datetime import date

from ..fetch import get_json
from ..metrics import parse_prize_label

STATE = {
    "code": "NY",
    "name": "New York",
    "sources": [
        {
            "label": "data.ny.gov: Scratch-Off Game Daily Prize Status Report",
            "url": "https://data.ny.gov/d/nzqa-7unk",
        },
        {
            "label": "nylottery.ny.gov: Scratch-Off Games",
            "url": "https://nylottery.ny.gov/scratch-off-games",
        },
    ],
}

TIERS_URL = "https://data.ny.gov/resource/nzqa-7unk.json?$limit=50000"
GAMES_URL = "https://nylottery.ny.gov/drupal-api/api/v2/scratch_off_data?_format=json"
GAME_PAGE = "https://nylottery.ny.gov/scratch-off-game?game={n}"


def _num(s) -> int:
    return int(str(s).replace(",", "").strip() or 0)


def _odds(s: str) -> float | None:
    m = re.search(r"1\s*in\s*([\d.]+)", s or "", re.I)
    return float(m.group(1)) if m else None


def fetch_games() -> list[dict]:
    rows = get_json(TIERS_URL)
    site = get_json(GAMES_URL)["rows"]

    tiers_by_game: dict[str, list[dict]] = {}
    names: dict[str, str] = {}
    for r in rows:
        g = str(r["game_number"]).strip()
        tiers_by_game.setdefault(g, []).append(
            {
                "label": r["prize_amount"].strip(),
                "total": _num(r["total"]),
                "paid": _num(r["paid"]),
                "unpaid": _num(r["unpaid"]),
            }
        )
        names[g] = r["game_name"].strip()

    def resolve(tiers: list[dict], price: float, top_label: str) -> list[dict]:
        """Attach cash values. A tier whose label carries no amount (NY prints a bare "LIFE"
        for one game) borrows the site's top-prize label."""
        for t in tiers:
            value, annuity = parse_prize_label(t["label"], price)
            if value == 0 and top_label:
                value, annuity = parse_prize_label(top_label, price)
                t["label"] = f"{t['label']} ({top_label})"
            t["value"], t["annuity"] = value, annuity
        return sorted(tiers, key=lambda t: -t["value"])

    today = date.today().isoformat()
    games: list[dict] = []
    seen: set[str] = set()
    for s in site:
        g = str(s["game_number"]).strip()
        seen.add(g)
        price = float(s.get("ticket_price") or 0)
        top_label = (s.get("top_prize_amount") or "").strip()
        tiers = resolve(tiers_by_game.get(g, []), price, top_label)
        end = (s.get("prizes_thru_date") or "").strip()
        notes = []
        if not tiers:
            notes.append("No prize-tier rows in the daily status report yet; only the top-prize count is known.")
        if end and end < today:
            notes.append("Past its prize-claim deadline.")
        art = s.get("cropped_art") or {}
        image = art.get("uri") if isinstance(art, dict) else None
        if not image and s.get("art"):
            image = s["art"][0].get("uri")
        games.append(
            {
                "game_number": g,
                "name": (s.get("title") or names.get(g) or "").strip(),
                "price": price,
                "odds": _odds(s.get("overall_odds")),
                "odds_label": (s.get("overall_odds") or "").strip(),
                "release_date": s.get("release_date") or "",
                "end_date": end,
                "top_prize_label": top_label,
                "top_prize_remaining": _num(s.get("top_prize_remaining") or 0),
                "image": image,
                "url": GAME_PAGE.format(n=g),
                "pdf": s.get("pdf") or "",
                "tiers": tiers,
                "notes": notes,
            }
        )

    # Games that only appear in the daily report (usually off-sale games still paying prizes).
    for g, tiers in tiers_by_game.items():
        if g in seen:
            continue
        tiers = resolve(tiers, 0.0, "")
        games.append(
            {
                "game_number": g,
                "name": names[g],
                "price": 0.0,
                "odds": None,
                "odds_label": "",
                "release_date": "",
                "end_date": "",
                "top_prize_label": tiers[0]["label"] if tiers else "",
                "top_prize_remaining": tiers[0]["unpaid"] if tiers else 0,
                "image": None,
                "url": GAME_PAGE.format(n=g),
                "pdf": "",
                "tiers": tiers,
                "notes": ["Not on the NY Lottery game list (likely off sale); price and odds unknown."],
            }
        )
    return games
