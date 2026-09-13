"""Registry of state scrapers.

Every module in this package whose name is a two-letter code (ny.py, tx.py, ...) is a state
scraper. Each exposes STATE (metadata dict) and fetch_games() -> list[dict]. A normalized game:

  {
    "game_number": "1711", "name": "MONEY BAGS", "price": 1.0, "odds": 4.89, "odds_label": "1 in 4.89",
    "release_date": "2026-09-01", "end_date": "", "top_prize_label": "$5,000", "top_prize_remaining": 9,
    "image": "https://...", "url": "https://...", "pdf": "https://...",
    "tiers": [{"label": "$5,000", "value": 5000.0, "total": 40, "paid": 31, "unpaid": 9, "annuity": False}, ...],
    "notes": []
  }

Optional keys a scraper may add:
  "tickets_printed": int   when the state publishes the print run but no overall odds;
                           build.py derives odds = tickets_printed / total prizes.
  "pct_sold": float        share of tickets sold (0-1) when the state publishes it.
  "unclaimed_value": float total dollar value of unclaimed prizes, when the state publishes that
                           instead of a prize table (with tickets_printed and pct_sold it gives the
                           return directly; "pct_step" is the state's rounding of pct_sold).
A tier may have "unpaid": None when the state publishes no remaining count for it (top-prize-only
states); the metrics then estimate it and report a return interval.

Only game_number, name, price, tiers are required; everything else defaults to empty.
Dates are ISO (YYYY-MM-DD) strings or "". tiers must be sorted by value, largest first.

To add a state: create lotto/states/<code>.py with the same two names. Nothing else to register.
"""
from __future__ import annotations

import importlib
import pkgutil

ALL = []
for _m in sorted(pkgutil.iter_modules(__path__)):
    if len(_m.name) == 2 and _m.name.isalpha():
        ALL.append(importlib.import_module(f"{__name__}.{_m.name}"))
