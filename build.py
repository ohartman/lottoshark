"""Fetch every registered state, compute metrics, and write site/data/*.js.

    python build.py        # all states
    python build.py NY     # one state

Output is plain JS (window.LOTTO[code] = {...}) rather than JSON so the site works when
opened straight from disk (file://) as well as from any static host.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from lotto.fetch import get
from lotto.metrics import compute, compute_aggregate
from lotto.states import ALL

SITE = Path(__file__).parent / "site"
OUT = SITE / "data"
LOGOS = SITE / "logos"


def shrink(raw: bytes) -> tuple[bytes, str]:
    """Return (bytes, extension). With Pillow installed, a 240px JPEG (a few KB);
    otherwise the original file untouched."""
    try:
        from io import BytesIO
        from PIL import Image
    except ImportError:
        return raw, ".webp"
    im = Image.open(BytesIO(raw)).convert("RGB")
    im.thumbnail((240, 240))
    buf = BytesIO()
    im.save(buf, "JPEG", quality=72, optimize=True)
    return buf.getvalue(), ".jpg"


def fetch_logos(code: str, games: list[dict]) -> int:
    """Download each game's ticket art once into site/logos/ and point g['logo'] at it.
    Shipping the logos with the site keeps it self-contained and fast on phones."""
    LOGOS.mkdir(parents=True, exist_ok=True)
    n = 0
    for g in games:
        if not g.get("image"):
            continue
        stem = f"{code.lower()}-{g['game_number']}"
        existing = next(LOGOS.glob(stem + ".*"), None)
        if existing is None:
            try:
                data, ext = shrink(get(g["image"], timeout=30))
            except Exception as e:
                print(f"  logo {stem}: skipped ({e})")
                continue
            existing = LOGOS / (stem + ext)
            existing.write_bytes(data)
            n += 1
        g["logo"] = f"logos/{existing.name}"
    return n


DEFAULTS = {
    "odds": None, "odds_label": "", "release_date": "", "end_date": "", "top_prize_label": "",
    "top_prize_remaining": 0, "image": None, "url": "", "pdf": "", "notes": [],
}


def normalize(g: dict) -> dict:
    """Fill optional keys so scrapers only have to supply what the state publishes."""
    for k, v in DEFAULTS.items():
        if g.get(k) is None:
            g[k] = list(v) if isinstance(v, list) else v
    g["game_number"] = str(g["game_number"]).strip()
    g["price"] = float(g.get("price") or 0)
    for t in g["tiers"]:
        # unpaid None = the state publishes no remaining count for this tier
        if t.get("unpaid") is None and t.get("paid") is not None:
            t["unpaid"] = max(t.get("total", 0) - t["paid"], 0)
        t.setdefault("unpaid", None)
        t.setdefault("paid", None if t["unpaid"] is None else max(t.get("total", 0) - t["unpaid"], 0))
        t.setdefault("annuity", False)
    g["tiers"].sort(key=lambda t: -t["value"])
    if g["tiers"]:
        g.setdefault("top_prize_label", g["tiers"][0]["label"])
        if not g["top_prize_label"]:
            g["top_prize_label"] = g["tiers"][0]["label"]
        if not g.get("top_prize_remaining") and g["tiers"][0]["unpaid"] is not None:
            g["top_prize_remaining"] = g["tiers"][0]["unpaid"]
    # States that publish the print run but not the overall odds: derive one.
    total_prizes = sum(t["total"] for t in g["tiers"])
    if not g["odds"] and g.get("tickets_printed") and total_prizes:
        g["odds"] = round(g["tickets_printed"] / total_prizes, 2)
        g["odds_label"] = g["odds_label"] or f"1 in {g['odds']:.2f} (derived)"
    return g


def build_state(mod) -> None:
    meta = mod.STATE
    t0 = time.time()
    games = [normalize(g) for g in mod.fetch_games()]
    if not games:
        raise RuntimeError("scraper returned no games")
    for g in games:
        if g.get("unclaimed_value") is not None and g.get("tickets_printed") and g.get("pct_sold") is not None:
            g["metrics"] = compute_aggregate(g["price"], g["tickets_printed"], g["pct_sold"], g["unclaimed_value"],
                                             [t for t in g["tiers"] if t.get("unpaid") is not None], g.get("pct_step", 0.01))
        else:
            g["metrics"] = compute(g["price"], g["odds"], g["tiers"], g.get("pct_sold"))
    new_logos = fetch_logos(meta["code"], games)
    if new_logos:
        print(f"  downloaded {new_logos} new logos")
    games.sort(key=lambda g: -(g["metrics"]["current_return"] if g["metrics"] else -1))
    payload = {
        **meta,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "games": games,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{meta['code'].lower()}.js").write_text(
        "window.LOTTO = window.LOTTO || {};\n"
        f"window.LOTTO[{json.dumps(meta['code'])}] = {json.dumps(payload, separators=(',', ':'))};\n",
        encoding="utf-8",
    )
    n_ok = sum(1 for g in games if g["metrics"])
    print(f"{meta['code']}: {len(games)} games ({n_ok} with full metrics) in {time.time() - t0:.1f}s")


def write_index() -> None:
    """index.js lists every state that has a data file (code + name), so the page can
    fill its dropdown and then load only the selected state's file."""
    states = []
    for f in sorted(OUT.glob("*.js")):
        if f.name == "index.js":
            continue
        head = f.read_text(encoding="utf-8")[:2000]
        m = re.search(r'"name":"((?:[^"\\]|\\.)*)"', head)
        states.append({"code": f.stem.upper(), "name": json.loads('"' + m.group(1) + '"') if m else f.stem.upper()})
    states.sort(key=lambda s: s["name"])
    (OUT / "index.js").write_text(f"window.LOTTO_STATES = {json.dumps(states)};\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    want = {a.upper() for a in argv[1:]}
    mods = [m for m in ALL if not want or m.STATE["code"] in want]
    if not mods:
        print("no matching state; known:", ", ".join(m.STATE["code"] for m in ALL))
        return 1
    failed: list[tuple[str, str]] = []
    for m in mods:
        try:
            build_state(m)
        except Exception as e:  # one broken state should not block the rest
            failed.append((m.STATE["code"], f"{type(e).__name__}: {e}"))
            print(f"{m.STATE['code']}: FAILED: {e}")
    write_index()
    # A failed state keeps its previous data file (the site shows its date as stale).
    # build-failures.txt is read by the GitHub workflow, which opens an issue listing them.
    report = Path(__file__).parent / "build-failures.txt"
    report.write_text("".join(f"{code}: {err}\n" for code, err in failed), encoding="utf-8")
    if failed:
        print(f"{len(failed)} of {len(mods)} states failed: " + ", ".join(c for c, _ in failed))
    # Exit non-zero only when nothing was built at all; partial failures still deploy.
    return 1 if len(failed) == len(mods) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
