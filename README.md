# LottoShark

Which scratch-off games are still worth a ticket? State lotteries publish how many prizes at
each tier were printed and how many are still unclaimed, and they print the overall odds on
every ticket. This project turns those public numbers into an expected value per ticket and
ranks every game in a state.

```
python build.py          # fetch every state, compute metrics, write site/data/*.js
python build.py NY       # just one state
python -m http.server 8765 -d site     # then open http://localhost:8765
```

No dependencies beyond Python 3.11+ (Pillow is optional; it shrinks the game logos).
`site/` is a plain static site and can be dropped on any host. Opening `site/index.html`
straight from disk also works because the data ships as JS, not JSON.

## Hosting

`.github/workflows/pages.yml` rebuilds the data every day at 13:30 UTC (after New York
posts its morning report), on every push to `main`, and on demand, then publishes `site/`
to GitHub Pages. The repository's Pages setting must be "Source: GitHub Actions".

For a custom domain, add a `CNAME` file to `site/` containing the domain, and point the
domain's DNS at GitHub Pages (a CNAME record to `<user>.github.io`, or the four A records
GitHub documents for apex domains).

## Layout

```
build.py               runs the scrapers, computes metrics, writes site/data/
lotto/fetch.py         tiny stdlib HTTP helper
lotto/metrics.py       the math (documented at the top of the file) and prize-label parsing
lotto/states/<code>.py one scraper per state
lotto/html.py          stdlib HTML table/text helpers for scrapers
lotto/states/__init__  registry (auto-discovers <code>.py modules)
site/index.html        the page
site/app.js            filter / sort / render, no framework
site/styles.css
site/data/             generated, one file per state plus index.js
```

## States

| State | Status | Sources |
| ----- | ------ | ------- |
| Maryland | Live | One AJAX call behind [mdlottery.com/games/scratch-offs](https://www.mdlottery.com/games/scratch-offs/): every game with printed / remaining per tier, price, odds, launch date, art. |
| Massachusetts | Live | masslottery.com JSON API: `/api/v1/games` (price, odds, dates, art) and `/api/v1/instant-game-prizes?gameID=N` (per-tier printed / paid / remaining). |
| New York | Live | [data.ny.gov nzqa-7unk](https://data.ny.gov/d/nzqa-7unk) (per-tier printed / paid / unpaid, daily) and the NY Lottery site's own JSON API (`/drupal-api/api/v2/scratch_off_data`) for price, odds, dates and art. |
| Texas | Live | [scratchoff.csv](https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/scratchoff.csv) (per-tier printed / claimed, daily) plus one detail page per game for odds and art. |
| Washington | Live | [Scratch Explorer](https://www.walottery.com/Scratch/Explorer.aspx) embeds every game with all tiers, price, odds and tickets printed as JSON. |

`docs/survey/` has verified notes on the data every other state publishes, with endpoints and
sample payloads, from a survey done in September 2026. In short: 24 states publish full
per-tier counts; CO, DE, ME, NE, PA, VT, WI publish only top-prize counts; AR, IL, TN sit
behind Cloudflare challenges; OH, OR, RI need credentials; ND and WY sell no scratch tickets;
AL, AK, HI, NV, UT have no lottery.

### Adding a state

Create `lotto/states/<code>.py` exposing `STATE` (code, name, sources) and
`fetch_games()` returning the normalized shape described in `lotto/states/__init__.py`,
and it is picked up automatically. The metrics and the site need nothing else.

Most other states publish the same information but as HTML tables or PDFs rather than a
feed; a scraper for those needs an HTML parser and a network that can reach the lottery
site (many school and office networks block gambling domains, which is why this was built
on New York's open-data portal first).

## The math

See the docstring in `lotto/metrics.py`. In short: tickets printed = prizes printed × overall
odds; share unsold = unclaimed ÷ printed on the plentiful small tiers; return per $1 = value
of unclaimed prizes ÷ tickets unsold ÷ price. Annuities are counted at their undiscounted
total, for-life prizes at the state's 20-year minimum, free plays at the ticket price.
