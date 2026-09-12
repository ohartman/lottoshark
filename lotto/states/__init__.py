"""Registry of state scrapers.

Each module exposes STATE (metadata dict) and fetch_games() -> list[dict]. A normalized game:

  {
    "game_number": "1711", "name": "MONEY BAGS", "price": 1.0, "odds": 4.89, "odds_label": "1 in 4.89",
    "release_date": "2026-09-01", "end_date": "", "top_prize_label": "$5,000", "top_prize_remaining": 9,
    "image": "https://...", "url": "https://...", "pdf": "https://...",
    "tiers": [{"label": "$5,000", "value": 5000.0, "total": 40, "paid": 31, "unpaid": 9, "annuity": False}, ...],
    "notes": []
  }

To add a state: create lotto/states/<code>.py with the same two names and append it to ALL.
"""
from . import ny

ALL = [ny]
