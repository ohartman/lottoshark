"""State-agnostic expected-value math for a scratch-off game.

Inputs per game (normalized by each state scraper):
  price   ticket price in dollars
  odds    overall odds denominator, e.g. 4.89 for "1 in 4.89" (tickets per prize at launch)
  tiers   list of {label, value, total, unpaid}; value is the cash value in dollars
          (annuities converted to an undiscounted lump sum, see parse_prize_label).
          unpaid may be None when the state publishes no remaining count for that tier
          (several states list only their top prizes).
  pct_sold  optional share of tickets sold (0-1) when the state publishes it directly

Method:
  total tickets printed = total prizes at launch * overall odds
  fraction unsold       = unpaid / printed, measured on the plentiful low tiers (the top tiers
                          are too few to be statistically useful). Prizes are randomly spread
                          through the print run, so the share of small prizes still unclaimed
                          tracks the share of tickets still unsold.
  tickets remaining     = total tickets * fraction unsold
  EV of one ticket now  = sum(value * unpaid) / tickets remaining
  EV at launch          = sum(value * total) / total tickets

Tiers without a published remaining count are assumed to deplete in step with ticket
sales, so their share of the return is exactly what it was at launch; only the published
tiers move the figure. The unsold share is then estimated from the published tiers alone,
which are a random sample of the print run: with N such prizes printed and k still out,
k ~ Binomial(N, share unsold), and a Beta(k+1/2, N-k+1/2) posterior gives a 90% interval.
The return is monotone in the unsold share, so the interval maps straight onto it.
Full-data states get the same interval, which is very tight because N is in the
thousands; states that publish only a handful of top prizes get honest, wide bars.
"""
from __future__ import annotations

import math
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


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    fpmin, eps = 1e-300, 3e-14
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = fpmin if abs(d) < fpmin else d
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = fpmin if abs(d) < fpmin else d
        c = 1.0 + aa / c
        c = fpmin if abs(c) < fpmin else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = fpmin if abs(d) < fpmin else d
        c = 1.0 + aa / c
        c = fpmin if abs(c) < fpmin else c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def beta_cdf(x: float, a: float, b: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1 - x) / b


def beta_quantile(p: float, a: float, b: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if beta_cdf(mid, a, b) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def compute(price: float, odds: float | None, tiers: list[dict], pct_sold: float | None = None) -> dict | None:
    """Return a metrics dict, or None if the inputs can't support an estimate."""
    tiers = [t for t in tiers if t.get("total")]
    # No real game has better than about 1 in 2.5 overall odds; anything under 2 is a
    # placeholder record the state has not filled in yet.
    if not tiers or not odds or odds < 2 or not price:
        return None
    known = [t for t in tiers if t.get("unpaid") is not None]
    unknown = [t for t in tiers if t.get("unpaid") is None]
    if not known and pct_sold is None:
        return None
    total_prizes = sum(t["total"] for t in tiers)
    total_tickets = total_prizes * odds
    launch_value = sum(t["value"] * t["total"] for t in tiers)
    launch_ev = launch_value / total_tickets
    # Real games pay back roughly 50-80% at launch. Far outside that, the published odds
    # or prize table for this game are wrong, and an estimate would mislead.
    if not 0.25 <= launch_ev / price <= 1.2:
        return None

    # ---- share of tickets unsold: point estimate and 90% interval
    u_floor = 1.0 / total_tickets  # at least one ticket left, or the ratio is meaningless
    if pct_sold is not None:
        u = u_lo = u_hi = min(max(1.0 - pct_sold, u_floor), 1.0)
        pool_n = None
    else:
        # Non-cash tiers (TV-show entries, valued at 0) are not claimed like cash and would
        # distort the sample, so they stay in the ticket count but out of the pool.
        cash = [t for t in known if t["value"] > 0] or known
        if unknown:
            pool = cash  # every published tier counts when the low tiers are missing
        else:
            pool = [t for t in cash if t["total"] >= STABLE_TIER_MIN] or cash
        pool_n = sum(t["total"] for t in pool)
        pool_k = min(sum(t["unpaid"] for t in pool), pool_n)
        a, b = pool_k + 0.5, pool_n - pool_k + 0.5
        u = pool_k / pool_n if pool_n >= STABLE_TIER_MIN else a / (a + b)
        u = min(max(u, u_floor), 1.0)
        u_lo = min(max(beta_quantile(0.05, a, b), u_floor), 1.0)
        u_hi = min(max(beta_quantile(0.95, a, b), u_floor), 1.0)
    estimated = bool(unknown) or (pool_n is not None and pool_n < STABLE_TIER_MIN)
    for t in unknown:
        t["unpaid_est"] = round(t["total"] * u)

    known_value = sum(t["value"] * t["unpaid"] for t in known)
    unknown_launch_value = sum(t["value"] * t["total"] for t in unknown)
    top = max(tiers, key=lambda t: t["value"])
    top_known = top.get("unpaid") is not None
    top_known_value = top["value"] * top["unpaid"] if top_known else 0.0
    top_unknown_value = 0.0 if top_known else top["value"] * top["total"]

    def ev(share: float, ex_top: bool = False) -> float:
        remaining = known_value + unknown_launch_value * share
        if ex_top:
            remaining -= top_known_value + top_unknown_value * share
        return remaining / (total_tickets * share)

    current_ev = ev(u)
    tickets_remaining = total_tickets * u
    unpaid_prizes = sum(t["unpaid"] for t in known) + sum(t["total"] * u for t in unknown)
    remaining_value = known_value + unknown_launch_value * u
    top_unpaid = top["unpaid"] if top_known else top["total"] * u
    top_odds_now = (tickets_remaining / top_unpaid) if top_unpaid > 0 else None
    launch_ex_top = (launch_value - top["value"] * top["total"]) / total_tickets

    return {
        "total_prizes": total_prizes,
        "unpaid_prizes": round(unpaid_prizes),
        "total_tickets": round(total_tickets),
        "tickets_remaining": round(tickets_remaining),
        "pct_sold": round((1 - u) * 100, 1),
        "pct_sold_low": round((1 - u_hi) * 100, 1),
        "pct_sold_high": round((1 - u_lo) * 100, 1),
        "launch_ev": round(launch_ev, 4),
        "current_ev": round(current_ev, 4),
        "launch_return": round(launch_ev / price, 4),
        "current_return": round(current_ev / price, 4),
        "return_low": round(ev(u_hi) / price, 4),
        "return_high": round(ev(u_lo) / price, 4),
        "edge": round((current_ev - launch_ev) / price, 4),
        "launch_return_ex_top": round(launch_ex_top / price, 4),
        "current_return_ex_top": round(ev(u, True) / price, 4),
        "return_ex_top_low": round(ev(u_hi, True) / price, 4),
        "return_ex_top_high": round(ev(u_lo, True) / price, 4),
        "odds_any_now": round(tickets_remaining / unpaid_prizes, 2) if unpaid_prizes else None,
        "top_prize_odds_now": round(top_odds_now) if top_odds_now else None,
        "remaining_prize_money": round(remaining_value),
        "has_annuity": any(t.get("annuity") for t in tiers),
        "estimated": estimated,
        "unknown_tiers": len(unknown),
        "published_prizes": pool_n,
    }


def compute_aggregate(
    price: float,
    tickets_printed: int,
    pct_sold: float,
    unclaimed_value: float,
    top_tiers: list[dict],
    pct_step: float = 0.01,
) -> dict | None:
    """Return metrics for states that publish, per game, the total value of unclaimed prizes
    and the share of tickets sold rather than a prize table (Vermont, Maine).

      return now = unclaimed value / (tickets printed * share unsold) / price

    The launch return is unknown without the prize structure. The state rounds the share
    sold (to a whole percent in Vermont, a tenth in Maine); pct_step is that rounding, and
    the interval covers it. top_tiers is [{value, unpaid}] for the "no jackpot" figure."""
    if not price or not tickets_printed or unclaimed_value is None or pct_sold is None:
        return None
    if unclaimed_value <= 0:
        return None
    # "Unclaimed" includes sold winners not yet cashed. Once almost everything is sold that
    # is most of what is left, and dividing it by a handful of unsold tickets is fiction.
    if pct_sold >= 0.90:
        return None
    u_floor = 1.0 / tickets_printed

    def ev(share: float, ex_top: bool = False) -> float:
        share = max(share, u_floor)
        v = unclaimed_value - (sum(t["value"] * t["unpaid"] for t in top_tiers) if ex_top else 0.0)
        return max(v, 0.0) / (tickets_printed * share)

    u = min(max(1.0 - pct_sold, u_floor), 1.0)
    u_lo, u_hi = min(max(1.0 - pct_sold - pct_step / 2, u_floor), 1.0), min(max(1.0 - pct_sold + pct_step / 2, u_floor), 1.0)
    current_ev = ev(u)
    top = max(top_tiers, key=lambda t: t["value"]) if top_tiers else None
    tickets_remaining = tickets_printed * u
    return {
        "total_prizes": None,
        "unpaid_prizes": None,
        "total_tickets": tickets_printed,
        "tickets_remaining": round(tickets_remaining),
        "pct_sold": round(pct_sold * 100, 1),
        "pct_sold_low": round((1 - u_hi) * 100, 1),
        "pct_sold_high": round((1 - u_lo) * 100, 1),
        "launch_ev": None,
        "current_ev": round(current_ev, 4),
        "launch_return": None,
        "current_return": round(current_ev / price, 4),
        "return_low": round(ev(u_hi) / price, 4),
        "return_high": round(ev(u_lo) / price, 4),
        "edge": None,
        "launch_return_ex_top": None,
        "current_return_ex_top": round(ev(u, True) / price, 4),
        "return_ex_top_low": round(ev(u_hi, True) / price, 4),
        "return_ex_top_high": round(ev(u_lo, True) / price, 4),
        "odds_any_now": None,
        "top_prize_odds_now": round(tickets_remaining / top["unpaid"]) if top and top["unpaid"] else None,
        "remaining_prize_money": round(unclaimed_value),
        "has_annuity": any(t.get("annuity") for t in top_tiers),
        "estimated": True,
        "unknown_tiers": 0,
        "published_prizes": None,
        "aggregate": True,
    }


def compute_remaining_only(price: float, odds: float | None, tiers: list[dict]) -> dict | None:
    """Return metrics for states that publish remaining counts for every tier but no
    printed totals (Kansas, Kentucky). Prizes are spread evenly through the print run,
    so the tickets still unsold are simply the prizes still unclaimed times the overall
    odds; the return follows without knowing the print run. Launch figures and the share
    sold are unknown."""
    tiers = [t for t in tiers if t.get("unpaid") is not None]
    if not tiers or not odds or odds < 2 or not price:
        return None
    unpaid_prizes = sum(t["unpaid"] for t in tiers)
    if unpaid_prizes <= 0:
        return None
    tickets_remaining = unpaid_prizes * odds
    remaining_value = sum(t["value"] * t["unpaid"] for t in tiers)
    current_ev = remaining_value / tickets_remaining
    if not 0.2 <= current_ev / price <= 3:
        return None
    top = max(tiers, key=lambda t: t["value"])
    ex_top = (remaining_value - top["value"] * top["unpaid"]) / tickets_remaining
    return {
        "total_prizes": None,
        "unpaid_prizes": unpaid_prizes,
        "total_tickets": None,
        "tickets_remaining": round(tickets_remaining),
        "pct_sold": None,
        "pct_sold_low": None,
        "pct_sold_high": None,
        "launch_ev": None,
        "current_ev": round(current_ev, 4),
        "launch_return": None,
        "current_return": round(current_ev / price, 4),
        "return_low": round(current_ev / price, 4),
        "return_high": round(current_ev / price, 4),
        "edge": None,
        "launch_return_ex_top": None,
        "current_return_ex_top": round(ex_top / price, 4),
        "return_ex_top_low": round(ex_top / price, 4),
        "return_ex_top_high": round(ex_top / price, 4),
        "odds_any_now": round(odds, 2),
        "top_prize_odds_now": round(tickets_remaining / top["unpaid"]) if top["unpaid"] else None,
        "remaining_prize_money": round(remaining_value),
        "has_annuity": any(t.get("annuity") for t in tiers),
        "estimated": False,
        "unknown_tiers": 0,
        "published_prizes": None,
        "remaining_only": True,
    }
