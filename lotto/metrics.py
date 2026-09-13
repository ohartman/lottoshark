"""State-agnostic expected-value math for a scratch-off game.

Inputs per game (normalized by each state scraper):
  price   ticket price in dollars
  odds    overall odds denominator, e.g. 4.89 for "1 in 4.89" (tickets per prize at launch)
  tiers   list of {label, value, total, unpaid}; value is the cash value in dollars
          (annuities converted to an undiscounted lump sum, see parse_prize_label)

Method:
  total tickets printed = total prizes at launch * overall odds
  fraction unsold       = unpaid / printed, measured on the plentiful low tiers (the top tiers
                          are too few to be statistically useful). Prizes are randomly spread
                          through the print run, so the share of small prizes still unclaimed
                          tracks the share of tickets still unsold.
  tickets remaining     = total tickets * fraction unsold
  EV of one ticket now  = sum(value * unpaid) / tickets remaining
  EV at launch          = sum(value * total) / total tickets
"""
from __future__ import annotations

import re

# Years assumed for "for life" prizes. NY guarantees a 20-year minimum on its for-life games,
# so we use that floor rather than guessing at longevity.
LIFE_YEARS = 20
# Minimum prizes printed in a tier before we trust it to estimate the unsold fraction.
STABLE_TIER_MIN = 500


def parse_prize_label(label: str, ticket_price: float = 0.0) -> tuple[float, bool]:
    """Return (cash value, is_annuity_or_assumed) for prize strings such as
    "$50", "$2,500", "$500000/YR/20YRS", "$1,000/WK/LIFE", "$1,000 A Week for Life",
    "Jackpot ($250K/YR/20", "Take 5FP" (a free play, valued at the ticket price).
    Returns (0, False) when the label carries no amount at all (e.g. a bare "LIFE")."""
    s = label.strip().upper().replace(",", "")
    if re.search(r"\bFP\b|FREE|\d+FP\b|TICKET", s):
        return float(ticket_price), False
    # "$1,000,000 ($50K/YR/20YRS)": the leading figure is already the annuity's total.
    m = re.match(r"\$?\s*(\d+(?:\.\d+)?)\s*(K|M)?\s*\(.*(?:/YR|/WK|LIFE|\bLF\b|YEAR|WEEK)", s)
    if m:
        return float(m.group(1)) * {"K": 1_000, "M": 1_000_000}.get(m.group(2) or "", 1), True
    m = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(MILLION|THOUSAND|MIL|K|M)?\b", s)
    if not m:
        return 0.0, False
    base = float(m.group(1)) * {"K": 1_000, "THOUSAND": 1_000, "M": 1_000_000, "MIL": 1_000_000, "MILLION": 1_000_000}.get(m.group(2) or "", 1)
    weekly = re.search(r"\bWK\b|/WK|WEEK", s) is not None
    m2 = re.search(r"/YR/(\d+)", s) or re.search(r"(?:A|PER)\s*YEAR\s*FOR\s*(\d+)\s*Y", s)
    if m2:
        return base * int(m2.group(1)), True
    if "LIFE" in s or re.search(r"\bLF\b", s):
        if weekly:
            return base * 52 * LIFE_YEARS, True
        if re.search(r"\bDAY\b|/DAY", s):
            return base * 365 * LIFE_YEARS, True
        if re.search(r"\bMO\b|/MO|MONTH", s):
            return base * 12 * LIFE_YEARS, True
        return base * LIFE_YEARS, True
    if weekly:
        m3 = re.search(r"(\d+)\s*(?:YRS|YEARS)", s)
        yrs = int(m3.group(1)) if m3 else LIFE_YEARS
        return base * 52 * yrs, True
    return base, False


def compute(price: float, odds: float | None, tiers: list[dict]) -> dict | None:
    """Return a metrics dict, or None if the inputs can't support an estimate."""
    tiers = [t for t in tiers if t.get("total")]
    # No real game has better than about 1 in 2.5 overall odds; anything under 2 is a
    # placeholder record the state has not filled in yet.
    if not tiers or not odds or odds < 2 or not price:
        return None
    total_prizes = sum(t["total"] for t in tiers)
    unpaid_prizes = sum(t["unpaid"] for t in tiers)
    total_tickets = total_prizes * odds

    stable = [t for t in tiers if t["total"] >= STABLE_TIER_MIN] or tiers
    frac_unsold = sum(t["unpaid"] for t in stable) / sum(t["total"] for t in stable)
    frac_unsold = min(max(frac_unsold, 0.0), 1.0)
    tickets_remaining = total_tickets * frac_unsold

    launch_value = sum(t["value"] * t["total"] for t in tiers)
    remaining_value = sum(t["value"] * t["unpaid"] for t in tiers)
    launch_ev = launch_value / total_tickets if total_tickets else 0.0
    current_ev = remaining_value / tickets_remaining if tickets_remaining > 0 else 0.0
    # Real games pay back roughly 50-80% at launch. Far outside that, the published odds
    # or prize table for this game are wrong, and an estimate would mislead.
    if not 0.25 <= launch_ev / price <= 1.2:
        return None

    top = max(tiers, key=lambda t: t["value"])
    top_odds_now = (tickets_remaining / top["unpaid"]) if top["unpaid"] > 0 and tickets_remaining > 0 else None
    # The same figures with the top tier stripped out: what a ticket is worth if you assume
    # you won't be the one hitting the jackpot. Far less swingy for nearly sold-out games.
    launch_ex_top = (launch_value - top["value"] * top["total"]) / total_tickets if total_tickets else 0.0
    current_ex_top = (
        (remaining_value - top["value"] * top["unpaid"]) / tickets_remaining if tickets_remaining > 0 else 0.0
    )

    return {
        "total_prizes": total_prizes,
        "unpaid_prizes": unpaid_prizes,
        "total_tickets": round(total_tickets),
        "tickets_remaining": round(tickets_remaining),
        "pct_sold": round((1 - frac_unsold) * 100, 1),
        "launch_ev": round(launch_ev, 4),
        "current_ev": round(current_ev, 4),
        "launch_return": round(launch_ev / price, 4),
        "current_return": round(current_ev / price, 4),
        "edge": round((current_ev - launch_ev) / price, 4),
        "launch_return_ex_top": round(launch_ex_top / price, 4),
        "current_return_ex_top": round(current_ex_top / price, 4),
        "odds_any_now": round(tickets_remaining / unpaid_prizes, 2) if unpaid_prizes else None,
        "top_prize_odds_now": round(top_odds_now) if top_odds_now else None,
        "remaining_prize_money": round(remaining_value),
        "has_annuity": any(t.get("annuity") for t in tiers),
    }
