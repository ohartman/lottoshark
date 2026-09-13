# Survey E: SD, TN, TX, VT, VA, WA, WV, WI, WY — scratch-off "prizes remaining" data sources

All requests made 2026-09-12 with `curl -sL -A "<Chrome 128 UA>"` from this machine. No browser tools used.

---

## South Dakota (SD)

**Site:** https://lottery.sd.gov/scratch-games/ (Next.js front end over a headless WordPress at `lottery-admin.sd.gov`; prize data is proxied from an IGT instant-games API via a Next.js API route).

**Format:** JSON API (all tiers). Curl gets 200 with real content; no bot wall.

**Scraper URLs:**
- List (paged, 100/page, includes CLOSED/DISABLED games):
  `https://lottery.sd.gov/api/igt/games/v1/instant-games/games` → follow `nextPageUrl` by prefixing `https://lottery.sd.gov/api/igt/games` to the returned `/api/v1/instant-games/games/page?size=100&start-item=100` (i.e. `https://lottery.sd.gov/api/igt/games/v1/instant-games/games/page?size=100&start-item=100`). ~280 games total, ~9-10% ACTIVE.
- Single game: `https://lottery.sd.gov/api/igt/games/v1/instant-games/games/<gameId>` (gameId = IGT game number, e.g. 1194).
- Only GET on `v1/instant-games/...` and `v2/draw-games/...` paths is allowed through the proxy (other paths → 405 "Method GET not allowed").

**Sample (single game, all keys):**
```json
{"gameId":"1194","gameName":"$100 FRENZY","validationStatus":"ACTIVE","ticketPrice":200,
 "startDistributionDate":1780894800000,"endDistributionDate":2158981200000,"disableDate":2159067600000,
 "prizeTiers":[{"tierNumber":1,"prizeAmount":200,"winningTickets":42854,"paidTickets":13364},
               {"tierNumber":9,"prizeAmount":500000,"winningTickets":5,"paidTickets":1}]}
```
List response keys: `nextPageUrl, previousPageUrl, nextItems, previousItems, games[]` (same game record shape, tiers included in the list response too).

**Fields:** all tiers with total (`winningTickets`) and paid (`paidTickets`); `ticketPrice` and `prizeAmount` are in **cents** (200 = $2.00); game number; start/end/disable epoch-ms dates; status. **No overall odds and no image in the API.**
- Odds/images come from the WordPress side. WPGraphQL at `https://lottery-admin.sd.gov/graphql` (POST JSON, introspection disabled but queries work): `games(first:100, where:{taxQuery:{taxArray:{field:SLUG,operator:IN,taxonomy:GAMETYPE,terms:["scratch-tickets"]}}}){ pageInfo{hasNextPage endCursor} nodes{ slug title uri acf{igtIdentifier} gamePrices{nodes{slug}} gameOptions{nodes{slug}} featuredImage{node{sourceUrl}} } }` returns slug→`igtIdentifier` (= gameId), price, status tags (active/closed/upcoming), and ticket image URL. WP REST also works: `https://lottery-admin.sd.gov/wp-json/wp/v2/game?game_type=3&per_page=100` (but `acf` is empty there).
- Overall odds appear only as text inside the game page's ODDS tab ("Overall Odds: 1:4.51") embedded in `__NEXT_DATA__` on `https://lottery.sd.gov/game/<slug>/` (server-rendered, 200). Optional.

**Effort: Easy.**

---

## Tennessee (TN)

**Site:** https://tnlottery.com/remaining-prizes/ (WordPress). Also https://tnlottery.com/games/instant-games/.

**Bot block:** Every request (Chrome UA, curl UA, Googlebot UA, `www.` host, `/wp-json/`) returns **403 with `server: cloudflare`, `cf-mitigated: challenge`** ("Just a moment..." JS challenge page). WebFetch also gets 403. No API reachable without solving the Cloudflare challenge.

**What the page would contain (per search results, not verified):** TN publishes only the **top 3 prize tiers** per game, updated weekly, with one top prize per game reserved for a "Play It Again" drawing. Third-party mirrors (lottoedge.com/tennessee/scratch/remaining-prizes/, scratchsmarter.com) exist but are not official.

**Effort: Blocked** (Cloudflare challenge; and even if bypassed, data is top-3-tiers only).

---

## Texas (TX)

**Site:** https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/ (static export of a CMS; server-rendered). Curl gets 200; no bot wall (note: `/Games/Scratch_Tickets/` and `/Top_Prizes_Remaining/` are 404 — the real folder is `Scratch_Offs`).

**Format:** **CSV** (all tiers) + server-rendered HTML.

**Scraper URLs:**
- All-levels CSV (updated daily): `https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/scratchoff.csv` (200, text/csv, ~42 KB, 864 rows, 79 games)
  ```
  "Scratch-Off Prizes as of 09/11/2026"
  "Game Number","Game Name","Game Close Date","Ticket Price","Prize Level","Total Prizes in Level","Prizes Claimed"
  2124,"Winning 7s",,1,"1","142200",109494
  2658,"$1,000,000 CROSSWORD",,20,"1000000","6",5
  2658,"$1,000,000 CROSSWORD",,20,"TOTAL","4479942",4275072
  ```
  `Prize Level` is the **prize dollar amount** (not a tier index); a `TOTAL` row per game must be skipped. `Game Close Date` is blank unless the game is closing. `Ticket Price` in dollars.
- HTML equivalents: `.../Scratch_Offs/all.html` (table: Game Number, Start Date, Ticket Price, Game Name, Prize Amount, Prizes Printed, Prizes Claimed — only the top 3 tiers per game), `.../Scratch_Offs/closing.html` (Game Name, Game Number, Game Call Date, End of Game Date), and per-game `.../Scratch_Offs/details.html_<id>.html` (all tiers "Amount / No. in Game / No. Prizes Claimed", plus text "Overall odds of winning any prize in <name> are 1 in 3.99", start date, approx. tickets printed, ticket images). The detail-page ids are opaque (e.g. `details.html_252698556.html`); scrape links from `all.html` (79 detail links).
- Open data portal (data.texas.gov) has only sales-by-price-point and winners-list datasets, **no per-tier prizes-remaining dataset**.

**Fields:** all tiers total + claimed (CSV); price; game number; close date (CSV, when set) / start date (all.html); overall odds only on the per-game detail page (text); ticket images on detail page.

**Effort: Easy** (CSV) — plus optional one-request-per-game for odds.

---

## Vermont (VT)

**Site:** https://vtlottery.com/games/instant-tickets/outstanding-prizes (Drupal 10, server-rendered). Curl 200; no bot wall.

**Format:** HTML table (server-rendered), one row per game, 82 rows.

**Sample rows** (cells joined with `|`):
```
Price | Game # | Game Name | Top Prizes | Unclaimed Top Prizes | Total Unclaimed | % Sold | # Of Tickets
$30 | 1891 | 300x The Cash | $150,000 $30,000 $10,000 $5,000 $1,000 $500 | 4 18 32 41 70 150 | $6,611,000 | 2 | 300,000
$10 | 1887 | Full of $100s | $100 | 6099 | $1,950,265 | 5 | 294,000
```
The "Top Prizes" cell lists several upper tiers (sub-list) with matching unclaimed counts, but **no printed counts** and no low tiers; the useful aggregates are `Total Unclaimed` ($) and `% Sold`.

Per-game pages `https://vtlottery.com/games/instant-tickets/<slug>` (e.g. `bank-vault`, 200) give: Top Prize, Game #, Ticket Price, Start Date, Last Day To Cash, **Overall Odds (1:4.22)**, and "Unclaimed Top Prizes" for the top few tiers only. No full odds/prize table found in HTML. Game slugs are linked from `/games/instant-tickets`.

**Fields:** price, game number, top-tier unclaimed only, overall odds (per-game page), start/last-day dates (per-game page), total unclaimed $, % sold, tickets printed.

**Effort: Blocked** for a full-tier EV model (top-prize-only); Medium if you accept `% Sold` + `Total Unclaimed` as a proxy.

---

## Virginia (VA)

**Site:** https://www.valottery.com/scratchers and https://www.valottery.com/scratcher-search (Sitecore + jQuery front end). Curl 200; no bot wall.

**Format:** JSON list API (top prize only) + server-rendered HTML per-game page (all tiers).

**Scraper URLs:**
- Game list: `POST https://www.valottery.com/api/v1/scratchers` with form body `page=0&totalPages=0&pageSize=14` (optionally `&filters[prices][]=5`, `filters[categories][]=...`). JSON body also accepted. Paged (`totalPages`=7 at pageSize 14 → ~95 games). Response:
  ```json
  {"currentPage":0,"totalPages":7,"data":[{"Title":"500X THE MONEY   ","GameID":2267,"TicketPrice":"$50","TopPrize":"$7M*",
   "PayoutNumber":1,"RolloverImageUrl":"https://cdnprodpaasmedia-valottery-com.azureedge.net/-/media/val/images/scratcher-teaser/2267_teaser.jpg?rev=...",
   "IsClosingSoon":false,"Game_TopPrizeDisclaimer":0}]}
  ```
  (`PayoutNumber` = top prizes remaining; titles are padded with trailing spaces.)
- Per-game page: `https://www.valottery.com/scratchers/<GameID>` (e.g. `/scratchers/2267`, 200, 167 KB). One `<table>` with all tiers:
  ```
  Prize Amount | Winning Tickets At Start | Winning Tickets Unclaimed
  $7,000,000* | 3 | 1
  $50,000 | 66 | 11
  ...
  $50 | 775,686 | 112,029
  ```
  Text also has "Odds of Winning Overall: 1 in 3.39", "Odds of Winning Top Prize: 1 in 2,611,200", "Ticket Price $50", "Start Date 3/5/2024", game number ("#2267"), and ticket image `.../scratcher-scratched/2267_scratched.jpg`.
- `/api/v1/prizesandodds` exists (POST `gameId=...`) but is used for draw games.

**Fields:** all tiers printed + unclaimed; price; overall & top-prize odds; game number; start date; images. No end date (only `IsClosingSoon`).

**Effort: Medium** (list JSON + one HTML request per game, ~95 games).

---

## Washington (WA)

**Site:** https://www.walottery.com/Scratch/ (ASP.NET WebForms). Curl 200; no bot wall.

**Format:** **JSON embedded in HTML** (all tiers, all games in one request) + server-rendered HTML tables.

**Scraper URLs:**
- Best: `https://www.walottery.com/Scratch/Explorer.aspx` (200, 340 KB). Contains an inline script `WaLottery.Scratch.data = { all: JSON.parse('{"Games":[...]}'), featured: JSON.parse('...') }`. Extract the `all: JSON.parse('...')` string literal, unescape `\'`, `json.loads`. 57 games (prices 1,2,3,5,10,20,30).
  Game keys: `Id, GameName, Cost, Featured, HasScratchableBack, FeaturedGameOrder, GridImageUrl, ScratchedImageUrl, UnscratchedImageUrl, BackScratchedImageUrl, BackUnscratchedImageUrl, OverallOdds, TicketsPrinted, SalesStartDate, SalesEndDate, RedeemEndDate, Prizes, LastUpdated`
  Tier keys: `PrizeAmount ("$2,000"), TotalPrizes ("4"), PrizesRemaining ("2"), TotalPrizesNumber (4), PrizesRemainingNumber (2), PrizesPaid ("2"), PrizesPaidNumber (2)`
  ```json
  {"Id":2016,"GameName":"MONSTER MONEY","Cost":1,"OverallOdds":"1 in 3.91","TicketsPrinted":"1,590,400",
   "SalesStartDate":null,"SalesEndDate":"","RedeemEndDate":"",
   "GridImageUrl":"https://walottery.com/scratch/assets/imgs/tickets/grid/2016.jpg",
   "Prizes":[{"PrizeAmount":"$2,000","TotalPrizesNumber":4,"PrizesRemainingNumber":2,"PrizesPaidNumber":2}, ...]}
  ```
- Fallback HTML: `https://www.walottery.com/Scratch/TopPrizesRemaining.aspx?price=%245` (one page per price point `$1..$30`, URL-encoded `$`), each game as "NAME $5 | 2011" heading + table `Prize Amount | Total Prizes | Prizes Paid | Prizes Remaining` for all tiers, plus "Last Day To Redeem" when set. Despite the name, it lists **all** tiers.
- `PrizeOdds.aspx` is just an explanatory page (no data).

**Fields:** all tiers total/paid/remaining; price; overall odds; game number (`Id`); tickets printed; start/end/redeem dates (often empty); image URLs; `LastUpdated`.

**Effort: Easy.**

---

## West Virginia (WV)

**Site:** https://wvlottery.com/games/scratch-offs (Next.js App Router; content from Contentful — images on `images.ctfassets.net`). Curl 200; no bot wall.

**Format:** JSON embedded in the React Server Components (RSC) payload — either in `self.__next_f.push([1,"..."])` script strings in the HTML, or cleaner via `curl -H 'RSC: 1'` which returns `text/x-component` (200, ~187 KB list / ~57 KB detail).

**Scraper URLs:**
- List: `https://wvlottery.com/games/scratch-offs` with header `RSC: 1`. Contains 130 game records (each `"gameNumber":"1269"` etc.). Record keys: `howToPlay, rulesPdf, gameId, gameNumber, topPrize, slug, title, imageAltText, startDate, endDate, claimEndDate, order, theme, ticketPrice, odds, image{url}, appImage{url}`.
  ```json
  {"gameId":215,"gameNumber":"1269","topPrize":2000,"slug":"1269-mothman-fortune-merry-little-cryptids",
   "title":"MOTHMAN FORTUNE-MERRY LITTLE CRYPTIDS","startDate":"2026-08-25T00:00:00.000-04:00","endDate":"2036-07-29T00:00:00.000-04:00",
   "claimEndDate":null,"ticketPrice":5,"odds":"1 in 3.79","image":{"url":"https://images.ctfassets.net/nm98451qj5dg/.../1269_P1_4x4.png"}}
  ```
  **The list does not include prize tiers.**
- Detail: `https://wvlottery.com/games/scratch-offs/<slug>` (with or without `RSC: 1`) adds `prizeDetails` (all tiers):
  ```json
  "gameNumber":"1269","topPrize":2000,"prizeDetails":[{"prize":5,"totalPrizes":64057,"remainingPrizes":56822},
    {"prize":10,"totalPrizes":35625,"remainingPrizes":31372}, ... {"prize":2000,"totalPrizes":4,"remainingPrizes":4}]
  ```
  Parsing: regex for `"prizeDetails":\[...\]` in the RSC text (or unescape the `\"` inside the `__next_f` strings in HTML), then `json.loads`.

**Fields:** all tiers total + remaining; price; overall odds; game number; start/end/claim-end dates; image URL. Also exposes a NEO web API base (`https://westvirginiawebapi.npi.wvlottery.com`) but that is used for jackpots/eInstants, not scratch tiers.

**Effort: Medium** (one request per game, ~130 games incl. some ended; RSC payload is regex-parsable with stdlib).

---

## Wisconsin (WI)

**Site:** https://wilottery.com/games/instant-games/scratch-games (Drupal, server-rendered; paged `?page=0..21`, 100 links/page so page 0 covers most). Curl 200; no bot wall. JSON:API is disabled (`/jsonapi` → 404).

**Format:** server-rendered HTML per-game pages, **top prize only**.

**Scraper URLs:**
- Per-game: `https://wilottery.com/games/instant-games/<slug>-<gameNumber>` (e.g. `/games/instant-games/10-packers-2781`, 200). No `<table>`; key/value text: "Total Top Prizes 3 / Remaining Top Prizes 2 / Overall Odds 1:3.9 / Price $10.00 / Game Number 2781 / Start Date 07/24/2026 / Top prize counts verified weekly".
- Prize structure (no remaining counts): `https://wilottery.com/games/instant-games/<slug>-features-procedures` has a table `PRIZE AMOUNT | APPROXIMATE NUMBER OF PRIZES | ODDS OF WINNING` for all tiers.
  ```
  $10 | 71,300 | 1:8
  $20 | 29,900 | 1:19
  ```

**Fields:** price, game number, overall odds, start date, top-prize total/remaining only; full tier counts printed (approximate) via the features page, but **no remaining counts below the top prize**.

**Effort: Blocked** for full-tier EV (top-prize-only remaining data); Medium to collect what exists (2 requests per game).

---

## Wyoming (WY)

**Confirmed: Wyoming sells no scratch/instant tickets.** The Wyoming Lottery Act (2013 HB0077) limits games to draw games and excludes instant/scratch tickets and VLTs. https://wyolotto.com/games lists only 2by2, Cowboy Draw, Keno, Lucky for Life, Mega Millions, Millionaire for Life, Powerball. (The site's redux state has an empty `instantGames` slice from the vendor template.) Curl gets 200 with no bot wall, but there is nothing to scrape.

**Effort: N/A** (no product).

---

## Summary

| State | Format | All tiers? | Price | Odds | Bot block | Effort | Main URL |
|---|---|---|---|---|---|---|---|
| SD | JSON API (IGT proxy) | Yes (total + paid) | Yes (cents) | No (CMS page text only) | None | Easy | `https://lottery.sd.gov/api/igt/games/v1/instant-games/games` (+ `/page?size=100&start-item=N`, `/<gameId>`) |
| TN | WordPress HTML (unverified) | No (top 3 tiers) | ? | ? | **Cloudflare JS challenge (403, cf-mitigated: challenge)** | Blocked | `https://tnlottery.com/remaining-prizes/` |
| TX | CSV (+ HTML detail pages) | Yes (total + claimed) | Yes | Detail page text only | None | Easy | `https://www.texaslottery.com/export/sites/lottery/Games/Scratch_Offs/scratchoff.csv` |
| VT | HTML table | No (top tiers unclaimed only; total unclaimed $, % sold) | Yes | Per-game page | None | Blocked (top-prize-only) | `https://vtlottery.com/games/instant-tickets/outstanding-prizes` |
| VA | JSON list + HTML per-game table | Yes (at start + unclaimed) | Yes | Yes (overall + top) | None | Medium | `POST https://www.valottery.com/api/v1/scratchers` + `https://www.valottery.com/scratchers/<GameID>` |
| WA | JSON embedded in HTML (single request) | Yes (total/paid/remaining) | Yes | Yes | None | Easy | `https://www.walottery.com/Scratch/Explorer.aspx` (fallback `TopPrizesRemaining.aspx?price=%245`) |
| WV | JSON in RSC payload (`RSC: 1`) | Yes (total + remaining), per-game only | Yes | Yes | None | Medium | `https://wvlottery.com/games/scratch-offs` (list) + `/games/scratch-offs/<slug>` (tiers) |
| WI | HTML per-game pages | No (top prize only; printed counts on features page) | Yes | Yes | None | Blocked (top-prize-only) | `https://wilottery.com/games/instant-games/scratch-games` + `/games/instant-games/<slug>-<n>` |
| WY | — | — | — | — | None | N/A (no scratch tickets by law) | `https://wyolotto.com/games` |
