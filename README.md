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

No dependencies beyond Python 3.11+ for most states. Pillow is optional (it shrinks the
game logos). Ohio and Oregon need a headless browser: `pip install playwright &&
python -m playwright install chromium`; without it those two states are skipped.
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

| State | Sources |
| ----- | ------- |
| Arizona | [arizonalottery.com: Scratchers prizes remaining](https://www.arizonalottery.com/scratchers/). The lottery's public JSON API (api.arizonalottery.com/v2) lists every active scratcher with all prize tiers: totalCount printed, count remaining, odds, price, dates. The www site itself sits behind a bot challenge, so there are no ticket images. |
| California | [calottery.com: Scratchers](https://www.calottery.com/scratchers). calottery.com's Sitecore JSON list gives every scratcher with price, odds, launch date and art; each game page has a server-rendered table of every tier with "remaining of total". |
| Colorado | [coloradolottery.com: Scratch Insider](https://www.coloradolottery.com/en/player-tools/scratch-insider/). The Scratch Insider table lists every game with price, odds, dates, payout percentage and how many top prizes remain; each game page has the full printed prize structure. Only the top prize has a remaining count, so the return is an estimate with a range (see lotto/metrics.py). |
| Connecticut | [ctlottery.com: Scratch Games](https://ctlottery.com/games/scratch-games). ctlottery.com is a Next.js site whose server payload embeds the game list and, on each game page, a "game" record with every prize tier (total, remaining), the overall odds and the number of tickets printed. The JSON is pulled out of the payload string with regexes; dollar signs are doubled in it. |
| District of Columbia | [dclottery.com: DC Scratchers](https://dclottery.com/dc-scratchers). dclottery.com's JSON:API lists every scratcher (path, odds, claim deadline); each game page carries price, game number, start date and a table of every tier with total, paid and remaining. |
| Florida | [floridalottery.com: Top Remaining Prizes](https://floridalottery.com/games/scratch-offs/top-remaining-prizes). One JSON call (the site's own scratch-games API, which wants an x-partner header) returns every game with all tiers: printed, paid, remaining, plus price, odds and dates. Ticket art comes from the site's content JSON. |
| Georgia | [galottery.com: Scratchers Top Prizes Claimed](https://www.galottery.com/en-us/games/scratchers/scratchers-top-prizes-claimed.html). galottery.com's instant-games API returns every game with all tiers (winningTickets printed, paidTickets claimed). Prices are in cents and prize amounts in dollars x 10,000. Annuitised top prizes are encoded as amount 0; the top-prizes page carries their label. Overall odds live only in each game's page JSON. |
| Idaho | [idaholottery.com: Scratch Games remaining prizes](https://www.idaholottery.com/games/scratch?view=remaining_prizes). Drupal JSON:API on idaholottery.com: every scratch game with price, odds, percent sold, dates, thumbnail and a full prize table (printed, amount, remaining, tier odds). Tiers under $25 sometimes have no remaining count; those are filled in from the state's own percent-sold figure, which is the same assumption the metrics use anyway. |
| Indiana | [hoosierlottery.com: Scratch-offs](https://hoosierlottery.com/games/scratch-off/). hoosierlottery.com's scratch-off listing carries each game's number, name, price, odds and art; each game page has a table of every tier (unclaimed, total). |
| Iowa | [ialottery.com: Remaining Prizes](https://ialottery.com/Pages/Games/RemainingPrizes.aspx). One page lists claimed and unclaimed counts for every prize of $50 and up; each game's detail page lists the odds of every prize level and the overall odds. Printed counts for the small prizes are reconstructed from their odds and the print run implied by the published tiers; their remaining counts are estimated (see lotto/metrics.py). |
| Kansas | [playonkansas.com: Scratch and Pull Tabs](https://playonkansas.com/games/scratch-and-pull-tabs). playonkansas.com is a Next.js site; the listing's server payload carries every game (number, price, dates, art) and each game page has a table of remaining prizes for every level, but no printed counts. Tickets unsold are taken as prizes remaining times the overall odds (compute_remaining_only). |
| Kentucky | [kylottery.com: Scratch-offs available](https://www.kylottery.com/apps/scratch_offs/available_games.html). One page lists every game on sale with price, odds, dates, art and a table of prizes remaining for every level, but no printed counts. Tickets unsold are taken as prizes remaining times the overall odds (compute_remaining_only). |
| Louisiana | [louisianalottery.com: Top Prizes Remaining](https://louisianalottery.com/top-prizes-remaining/). The top-prizes page embeds a JSON list of current scratch-offs (number, price, art, start date, link); each game page has a table of every tier with total, claimed and remaining, plus the overall odds. |
| Maine | [mainelottery.com: Unclaimed Prizes](https://www.mainelottery.com/players_info/unclaimed_prizes.html). The unclaimed-prizes table gives each game's price, percent unsold, total unclaimed prize value and top-prize counts; the state's news articles for each game give tickets printed, overall odds and art. No prize structure is published, so the return is unclaimed value over unsold tickets (compute_aggregate). |
| Maryland | [mdlottery.com: Scratch-Offs](https://www.mdlottery.com/games/scratch-offs/). The scratch-off finder on mdlottery.com is a WordPress shortcode loaded by AJAX; one POST returns every game as an HTML fragment with a full prize table (Prize Amount | Start | Remaining) per game. |
| Massachusetts | [masslottery.com: Instant Tickets](https://www.masslottery.com/games/instant). The masslottery.com site is a React app over a public JSON API: /api/v1/games every game with price, odds, start date, art /api/v1/instant-game-prizes?gameID=N one game's prize tiers: printed, paid, remaining |
| Michigan | [michiganlottery.com: Instant Games prizes remaining](https://www.michiganlottery.com/games/instant-games). michiganlottery.com is a React app over a GraphQL endpoint. Two queries: prizes remaining for every retail instant game (all tiers: starting and remaining) and the CMS game list (price, overall odds, art, launch date), joined on the IGT game id. |
| Minnesota | [mnlottery.com: Scratch Games](https://www.mnlottery.com/games/scratch). The lottery's GameOn API lists every scratch game with price, odds, dates and art, and gives total and remaining counts for prizes of $500 and up. Each game page on mnlottery.com carries the full printed prize structure, so the smaller prizes get a printed count and an estimated remaining count (see lotto/metrics.py). |
| Mississippi | [mslottery.com: Active Instant Games](https://www.mslottery.com/gamestatus/active/). mslottery.com's WordPress REST API lists active instant games with the prize table (original and remaining counts) as HTML in the post body; the ticket price is a taxonomy term and the overall odds and game number are on each game's page. |
| Missouri | [molottery.com: Scratchers](https://www.molottery.com/scratchers-list.do). molottery.com's scratchers list page links every active game; each detail page has a table of every tier (total, unclaimed), the price, overall odds and dates. |
| Nebraska | [nelottery.com: Scratch prizes remaining](https://nelottery.com/homeapp/scratch/prizesremaining/web). The prizes-remaining page lists each game's price, number, art and the remaining count for its top two or three prize levels; each game's detail page has the full printed prize structure (one row per winning combination, summed per prize) and the overall odds. Lower tiers have no remaining count, so the return is an estimate. |
| New Jersey | [njlottery.com: Scratch-Offs](https://www.njlottery.com/en-us/scratch-offs.html). njlottery.com's instant-games API lists every game with all tiers (winningTickets printed, paidTickets claimed) and the total tickets printed. Amounts are in cents, dates epoch-ms. The state publishes no overall odds; build.py derives them from tickets printed. |
| New Mexico | [nmlottery.com: Scratchers](https://www.nmlottery.com/games/scratchers/). nmlottery.com/games/scratchers/ is one server-rendered page with a block per game: price, game number, start date, overall odds, art, and a table of every tier (prize, odds, printed, remaining). |
| New York | [data.ny.gov: Scratch-Off Game Daily Prize Status Report](https://data.ny.gov/d/nzqa-7unk); [nylottery.ny.gov: Scratch-Off Games](https://nylottery.ny.gov/scratch-off-games).  |
| North Carolina | [nclottery.com: Scratch-Off Prizes Remaining](https://nclottery.com/scratch-off-prizes-remaining). nclottery.com/scratch-off-prizes-remaining is one server-rendered page with a table per game: value, odds, total, remaining for every tier, plus price, game number, name and thumbnail. Overall odds are derived from the print run implied by the biggest tier's odds. |
| Ohio | [ohiolottery.com: Scratch-Offs Prizes Remaining](https://www.ohiolottery.com/games/scratch-offs/prizes-remaining). ohiolottery.com renders its scratch-off pages in the browser from an API the page authorises itself. A headless browser loads the public prizes-remaining page (every game with every tier's printed and remaining counts) and the scratch-offs listing (price, odds, dates, page path); this code never touches the token. |
| Oklahoma | [oklottery.com: Scratchers](https://oklottery.com/games/scratchers). oklottery.com is a Next.js site; the server-component payload (RSC: 1 header) of each game page embeds prizeDetails with every tier's total and remaining, plus odds, price, dates, tickets printed and art. |
| Oregon | [oregonlottery.org: Scratch-its](https://www.oregonlottery.org/scratch-its/list/). oregonlottery.org fills its scratch-its pages in the browser from the lottery's game-info API, which the page authorises itself. A headless browser loads the public list page (every game with price, odds, dates, sell-through and unclaimed value) and each current game's page, whose API response carries every prize tier's total and remaining. |
| Pennsylvania | [palottery.pa.gov: Scratch-Offs Prizes Remaining](https://www.palottery.pa.gov/Scratch-Offs/Prizes-Remaining.aspx); [Pennsylvania Bulletin: instant lottery game notices](https://www.pacodeandbulletin.gov/). The lottery site lists every game's six largest prizes with remaining counts, and each game page gives the overall odds; neither says how many prizes were printed. That structure is in the game's rules notice in the Pennsylvania Bulletin (a table of prize, odds and approximate winners per print run), found by searching the Bulletin for the game number. Lower tiers have no remaining count, so the return is an estimate with a range (see lotto/metrics.py). |
| South Dakota | [lottery.sd.gov: Scratch Games](https://lottery.sd.gov/scratch-games/). lottery.sd.gov proxies IGT's instant-games API (all tiers, printed and paid, cents) and runs a headless WordPress whose GraphQL gives the slug, status and art for each game. Overall odds appear only as text on the game's page. |
| Texas | [texaslottery.com: Scratch Ticket Prizes Remaining (CSV)](https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/scratchoff.csv); [texaslottery.com: Scratch Tickets](https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/all.html).  |
| Vermont | [vtlottery.com: Outstanding Prizes](https://vtlottery.com/games/instant-tickets/outstanding-prizes). One table lists every game with price, tickets printed, percent sold, total unclaimed prize value and the unclaimed counts for its top prize levels. No prize structure is published, so the return comes straight from unclaimed value divided by unsold tickets (compute_aggregate), with a range from the whole-percent rounding. |
| Virginia | [valottery.com: Scratchers](https://www.valottery.com/scratchers). valottery.com's scratcher list API gives game ids, price and art; each game page has a table of every tier (winning tickets at start, unclaimed) plus overall odds, start date and game number. |
| Washington | [walottery.com: Scratch Explorer](https://www.walottery.com/Scratch/Explorer.aspx). Explorer.aspx embeds the whole game list, all prize tiers included, as a JSON string inside an inline script (WaLottery.Scratch.data = { all: JSON.parse('...') }). |
| West Virginia | [wvlottery.com: Scratch-Offs](https://wvlottery.com/games/scratch-offs). wvlottery.com is a Next.js site; asking for the server-component payload (RSC: 1 header) returns the game list as JSON text, and each game's payload adds prizeDetails with every tier's total and remaining. |
| Wisconsin | [wilottery.com: Scratch Games](https://wilottery.com/games/instant-games/scratch-games). Each game page gives price, odds, start date and the top prize's printed and remaining counts; its features-and-procedures page gives the approximate printed count for every prize level. Only the top prize has a remaining count, so the return is an estimate with a range. |

`docs/survey/` has verified notes on the data every other state publishes, with endpoints and
sample payloads, from a survey done in September 2026. Not included: AR, IL, TN sit behind Cloudflare
challenges; RI needs a player session; DE publishes no printed counts; ND and WY sell no scratch
tickets; AL, AK, HI, NV, UT have no lottery.

### Adding a state

Create `lotto/states/<code>.py` exposing `STATE` (code, name, sources) and
`fetch_games()` returning the normalized shape described in `lotto/states/__init__.py`,
and it is picked up automatically. The metrics and the site need nothing else.

Most other states publish the same information but as HTML tables or PDFs rather than a
feed; a scraper for those needs an HTML parser and a network that can reach the lottery
site (many school and office networks block gambling domains, which is why this was built
on New York's open-data portal first).

## Estimated states

Colorado, Nebraska and Wisconsin publish remaining counts only for their top prize levels
but do publish the full printed prize structure; Iowa and Minnesota publish them only
for prizes of $50 and $500 and up, with the rest of the structure on their game pages. Unpublished levels are assumed to deplete
in step with sales, so their share of the return equals their launch share; the unsold
share is estimated from the published prizes with a Beta(k+½, N−k+½) posterior and the
site shows the 90% interval. Vermont and Maine publish total unclaimed prize money and
percent sold instead of a prize table; the return is unclaimed value ÷ unsold tickets ÷
price, with a range from the state's rounding of percent sold. Kansas and Kentucky publish
remaining counts for every prize but no printed totals, so tickets unsold are taken as
prizes unclaimed × overall odds and the launch figures are left blank. Pennsylvania's six
remaining counts are paired with the printed structure from each game's notice in the
Pennsylvania Bulletin. Delaware publishes neither printed counts nor a prize structure and is
not included.

## The math

See the docstring in `lotto/metrics.py`. In short: tickets printed = prizes printed × overall
odds; share unsold = unclaimed ÷ printed on the plentiful small tiers; return per $1 = value
of unclaimed prizes ÷ tickets unsold ÷ price. Annuities are counted at their undiscounted
total, for-life prizes at the state's 20-year minimum, free plays at the ticket price.
