"""Maryland. The scratch-off finder on mdlottery.com is a WordPress shortcode loaded by
AJAX; one POST returns every game as an HTML fragment with a full prize table
(Prize Amount | Start | Remaining) per game."""
from __future__ import annotations

import re
from datetime import datetime

from ..fetch import get_text
from ..html import money, num, tables, text
from ..metrics import parse_prize_label

STATE = {
    "code": "MD",
    "name": "Maryland",
    "sources": [{"label": "mdlottery.com: Scratch-Offs", "url": "https://www.mdlottery.com/games/scratch-offs/"}],
}
AJAX = "https://www.mdlottery.com/wp-admin/admin-ajax.php"


def _field(block: str, cls: str) -> str:
    m = re.search(rf'class="{cls}"[^>]*>(.*?)</', block, re.S)
    return text(m.group(1)) if m else ""


def fetch_games() -> list[dict]:
    html = get_text(AJAX, data={"action": "jquery_shortcode", "shortcode": "scratch_offs", "atts": '{"null":"null"}'})
    blocks = re.split(r'(?=<li class="ticket" id="ticket_\d+")', html)
    games = []
    for b in blocks:
        m = re.match(r'<li class="ticket" id="ticket_(\d+)"', b)
        if not m:
            continue
        num_ = m.group(1)
        price = money(_field(b, "price"))
        name = _field(b, "name")
        prob = _field(b, "probability")
        launch = _field(b, "launchdate")
        try:
            release = datetime.strptime(launch, "%m/%d/%Y").date().isoformat()
        except ValueError:
            release = ""
        img = re.search(r'<img[^>]+src="([^"]+)"', b)
        tiers = []
        for t in tables(b):
            if t and t[0] and t[0][0].lower().startswith("prize"):
                for r in t[1:]:
                    if len(r) < 3:
                        continue
                    value, annuity = parse_prize_label(r[0], price)
                    total, unpaid = num(r[1]), num(r[2])
                    tiers.append({"label": r[0], "value": value, "annuity": annuity, "total": total, "unpaid": unpaid, "paid": max(total - unpaid, 0)})
                break
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        games.append({
            "game_number": num_,
            "name": name,
            "price": price,
            "odds": float(prob) if re.fullmatch(r"[\d.]+", prob) else None,
            "odds_label": f"1 in {prob}" if prob else "",
            "release_date": release,
            "top_prize_label": _field(b, "topprize") or None,
            "top_prize_remaining": num(_field(b, "topremaining")),
            "image": img.group(1) if img else None,
            "url": f"https://www.mdlottery.com/scratch-off/{slug}-{num_}/",
            "tiers": tiers,
            "notes": [],
        })
    return games
