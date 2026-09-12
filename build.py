"""Fetch every registered state, compute metrics, and write site/data/*.js.

    python build.py        # all states
    python build.py NY     # one state

Output is plain JS (window.LOTTO[code] = {...}) rather than JSON so the site works when
opened straight from disk (file://) as well as from any static host.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from lotto.fetch import get
from lotto.metrics import compute
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


def build_state(mod) -> None:
    meta = mod.STATE
    t0 = time.time()
    games = mod.fetch_games()
    for g in games:
        g["metrics"] = compute(g["price"], g["odds"], g["tiers"])
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
    states = sorted(f.stem.upper() for f in OUT.glob("*.js") if f.name != "index.js")
    (OUT / "index.js").write_text(f"window.LOTTO_STATES = {json.dumps(states)};\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    want = {a.upper() for a in argv[1:]}
    mods = [m for m in ALL if not want or m.STATE["code"] in want]
    if not mods:
        print("no matching state; known:", ", ".join(m.STATE["code"] for m in ALL))
        return 1
    failed = 0
    for m in mods:
        try:
            build_state(m)
        except Exception as e:  # one broken state should not block the rest
            failed += 1
            print(f"{m.STATE['code']}: FAILED: {e}")
    write_index()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
