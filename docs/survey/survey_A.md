# Survey A: scratch-off "prizes remaining" data sources (AZ, AR, CA, CO, CT, DE, DC, FL, GA)

Surveyed 2026-09-12 with curl (Chrome UA, `-L`) from this machine, plus WebFetch/WebSearch where curl was blocked.
Every URL below was actually requested; response shapes are pasted from real responses.

---

## Arizona (AZ)

**Main URL(s) (JSON API, no auth):**
- Top prizes for all active games: `https://api.arizonalottery.com/v2/scratchers/topprizes`
- Full per-game tiers: `https://api.arizonalottery.com/v2/scratchers/{gameNum}` (e.g. `/v2/scratchers/1489`)
- Game-number list: `https://api.arizonalottery.com/v2/lookup/games` (key `Scratchers` = 79 strings like `"$100 Grand Crossword #1562"`; parse the trailing `#NNNN`). `topprizes` also yields the 77 game numbers that still have a top prize.
- Unclaimed draw prizes (not scratchers): `/v2/unclaimedprizes`

**Format:** JSON (AWS API Gateway, fronted by Cloudflare but no challenge; curl → 200). Found by reading the site's `/scripts/api-integration-v3.js` (`CONFIG.api.baseUrl = 'https://api.arizonalottery.com/v2/'`, `endpoints.scratchers = "scratchers"`).

**Bot block:** The main site `www.arizonalottery.com` returns **403 Cloudflare managed challenge** (`cf-mitigated: challenge`, "Just a moment...") for curl, Python urllib, and WebFetch alike — so ticket images/page HTML are not reachable. A staging host `https://autoscalestg.arizonalottery.com/` serves the same Umbraco site without the challenge (200), but don't build on it. The API host is NOT challenged.

**Fields:** all tiers. Game record: `id, gameNum, gameName, beginDate, endDate, lastDate, gameOdds (3.44), ticketValue (10.00), hasAnnuityPrize, annuityDetails, dateModified, prizeTiers[]`. Tier: `id, gameNum, tierLevel, description ("$100,000"), displayTitle, count (=REMAINING), totalCount (=printed), prizeAmount (100000.00), odds (305082.90 = "1 in"), isOther, dateModified`. The site JS renders `count + " of " + totalCount` as "Prizes Remaining". No image URL in the API. `topprizes` rows: `{gameNum, topPrizeDivision, description, displayTitle, prizesRemaining, prizeAmount}`.

**Sample** (`/v2/scratchers/1489`):
```json
{"id":"f97e5447-...","gameNum":1489,"gameName":"Money","beginDate":"2025-05-06","endDate":"2099-12-31","lastDate":"2099-12-31","gameOdds":3.44,"ticketValue":10.00,"hasAnnuityPrize":false,"dateModified":"2026-09-12T08:00:37.563",
 "prizeTiers":[{"tierLevel":1,"description":"$100,000","count":5,"totalCount":7,"prizeAmount":100000.00,"odds":305082.90,"isOther":false}, ... {"tierLevel":11,"description":"$10","count":88687,"totalCount":231405,"prizeAmount":10.0,"odds":9.23}]}
```
**Effort: Easy** (1 list call + ~79 per-game JSON calls, all tiers, price, odds, dates). Updated daily (`dateModified` 08:00).

---

## Arkansas (AR)

**Main URL(s):** list `https://www.myarkansaslottery.com/games/instant` (12 per page, 6 pages, `?page=N`); per-game `https://www.myarkansaslottery.com/games/{slug}` (e.g. `/games/100x-0`). Drupal site.

**Format:** server-rendered HTML per game (seen via WebFetch). `/jsonapi` → 404 (JSON:API disabled).

**Fields (per game page):** Game Number (885), Ticket Price ($10), Overall Odds (1 in 3.02), Launch Date (3/3/2026), and a full tier table `Prize | Total in Game | Remaining | Total Amount | Remaining Amount` for ALL tiers, plus "Prizes remaining are updated daily." Ticket thumbnail on the list page.

**Bot block: YES — Cloudflare managed challenge (403, `cf-mitigated: challenge`)** on `www.`, apex, and http:// for curl (with full Chrome header set, HTTP/2) and for Python urllib. WebFetch (Anthropic's fetcher) got through, so the challenge is fingerprint/IP based, not a hard block.

**Effort: Blocked** for stdlib scrapers (would be Medium — one request per game — if fetched through something that passes the Cloudflare JS challenge).

---

## California (CA)

**Main URL(s):**
- Game list JSON: `https://www.calottery.com/api/Sitecore/ScratchersFilteredList/GetScratchers?modelId=0dc0c687-836a-43d3-aa8b-a0491dbf4001&sortBy=&page=1&size=200&show=&gametype=&price=&nameOrNumber=` (GET; `show=` must be blank — `show=all` returns 0 rows). `modelId` is a Sitecore rendering GUID embedded in the `/scratchers` page HTML (`modelId = '...'`); hard-code it but fall back to scraping it.
- Per-game tiers: the `GameProductPage` from the list, e.g. `https://www.calottery.com/scratchers/$10/mystery-crossword-1743` (server-rendered HTML).

**Format:** JSON list + HTML table per game. curl → 200, no bot wall.

**Fields:** list record: `ScratchersImage (thumb URL), MarketingTitle, GameName, GameNumber (1744), GameType, GameShows[], GamePrice ("$20"), GotoMarketDate ("/Date(1787554800000)/"), TopPrizeDollarAmt, OverallOdds ("3.00"), AltText, GameProductPage`. Game page: "Game Number: 1743", "Overall odds: 1 in 3.47", "Cash odds", "Last Updated Sep 12, 2026 02:35:24 a.m.", table `Prizes | Odds 1 in | Prizes Remaining` for ALL tiers with remaining rendered as `23 of 25` (remaining of total), down to the "Ticket" (free ticket) tier. No end date.

**Sample** (list, 54 games):
```json
{"TotalScratcherCards":54,"TotalPages":1,"CurrentPage":1,"SerializedScratcherCardList":[{"ScratchersImage":"https://static.www.calottery.com/-/media/project/calottery/pws/scratchers/1744205000000extremecashthumbnail.jpg?rev=...","GameName":"$5,000,000 Extreme Cash","GameNumber":1744,"GameType":"Key Number Match","GamePrice":"$20","GotoMarketDate":"/Date(1787554800000)/","TopPrizeDollarAmt":"$5,000,000","OverallOdds":"3.00","GameProductPage":"/scratchers/$20/$5000000-extreme-cash-1744"}]}
```
Game page table (tags stripped): `Prizes | Odds 1 in | Prizes Remaining | $750,000 | 1,200,000 | 23 of 25 | $10,000 | 600,000 | 47 of 50 | ... | Ticket | 6 | 4,356,792 of 4,800,000` — container class `odds-available-prizes`.

**Effort: Medium** (JSON list + 1 HTML request per game, ~54 games, all tiers).

---

## Colorado (CO)

**Main URL(s):**
- Top-prizes table (server-rendered HTML): `https://www.coloradolottery.com/en/player-tools/scratch-insider/` (84 rows, `<th id="th_1..th_11">`; "Results are updated once a day").
- Per-game page: `https://www.coloradolottery.com/en/games/scratch/game/{slug}-{gameNum}/` e.g. `/en/games/scratch/game/100x-2923/`; list of links on `https://www.coloradolottery.com/en/games/scratch/`.

**Format:** HTML tables (Django site; `?format=json` just returns HTML; no API found in the bundled JS). curl → 200, no bot wall.

**Fields:** insider table columns: `Game name | Game number | Ticket price | Game start | Last day to claim | Top prize | Total top prizes | Top prizes remaining | Overall odds | Number of Eligible Drawings | Payout percentage`. Game page: Ticket Price, Top Prize, **Top Prizes Remaining**, Last Day to Claim, Overall Odds ("1 in 3.52"), Payout Percentage, and a tier table `Prize Amount | Winning Tickets | Probability` (printed count and odds for ALL tiers, but **no per-tier remaining** — only the top prize has a remaining count).

**Sample** (insider row, tags stripped): `Casino Ca$h Chips | 280 | $20 | April 3, 2023 | Not Set | $1,000,000 | 2 | 2 | 1 in 3.02 | 1 | 74.5%`
Game page tier rows: `$250,000 | 2 | 1 in 720,000 | $50,000 | 3 | 1 in 480,000 | ... | $50 | 14,400 | 1 in 100`

**Effort: Blocked (top-prize-only remaining data)** — scraping itself is easy (one HTML table for all games + optional per-game page for full printed-tier structure + payout %).

---

## Connecticut (CT)

**Main URL(s):**
- Landing: `https://ctlottery.com/games/scratch-games` (old `ctlottery.org/ScratchGamesTable` 301s here). Next.js SSR; the RSC payload (`self.__next_f.push(...)`) embeds a `"games":[...]` JSON array with all 74 active games.
- Per-game: `https://ctlottery.com/games/scratch-games/{gameNo}` e.g. `/games/scratch-games/1853` — RSC payload embeds `"game":{...,"prizes":[...]}` with ALL tiers, and the same data is server-rendered as an HTML table `Prize Amount | Total Prizes | Unclaimed Prizes` under "Prizes Remaining — As of September 11, 2026".
- Headless Drupal backend (JSON:API, open): `https://app-clc-prod-drupal.azurewebsites.net/jsonapi/node/scratch_games?page[limit]=50` (use `curl -g`) → `title, field_game_no, field_scratch_overall_odds ("9.19"), field_scratch_status, field_scratch_hidden, …` but **no prize tiers** (only a `field_scratch_prize_pdf` relation; PDFs at `https://ctlottery.com/sites/default/files/scratch-prize-pdfs/1853.pdf`).

**Format:** JSON embedded in HTML (regex out of the RSC string; note `$` is escaped as `$$` and quotes as `\"`). curl → 200, no bot wall.

**Fields:** landing game record: `gameNo, gameName, displayNameHtml, ticketCost ("$$10.00"), ticketCostRaw (10), topPrize, topPrizeRaw, displayTopPrize, wideFormat, startDate, stopDate, endValDate, totalTopPrizes, topPrizesRemaining, featured, secondChance, status ("new"/"active"), images{full,thumbnail,rollover}`. Game record adds: `overallOdds ("1 in 3.74"), launchDate, asOf ("2026-09-11"), totalTickets (11416200), prizes:[{level, amount, amountRaw, total, remaining}]`.

**Sample** (game 1853, RSC payload, unescaped):
```json
"game":{"gameNo":1853,"gameName":"$30,000 CA$HWORD 2ND EDITION","status":"active","ticketCostRaw":3,"topPrizeRaw":30000,"overallOdds":"1 in 3.74","launchDate":"2026-07-24","startDate":"2026-07-24","stopDate":"2099-12-31","endValDate":"2099-12-30","asOf":"2026-09-11","totalTickets":11416200,
 "images":{"full":"/Content/images/Scratch/1853.jpg","thumbnail":"/Content/images/Scratch/thumbnails/1853.jpg"},
 "prizes":[{"level":8,"amount":"$30,000","amountRaw":30000,"total":21,"remaining":21},{"level":7,"amount":"$1,000","amountRaw":1000,"total":332,"remaining":317},{"level":6,"amount":"$100","amountRaw":100,"total":10331,"remaining":9795}, ...]}
```
**Effort: Medium** (1 landing request for the game list + 1 request per game, ~74 games; JSON is embedded so parsing is clean).

---

## Delaware (DE)

**Main URL(s):**
- `https://www.delottery.com/Instant-Games/Top-Prizes-Remaining` (and a simpler `/Instant-Games/Top-Prizes-Remaining/Print`) — HTML table, "as of 9/9/2026 8:22:05 AM", ~41 rows (`*` = game closing).
- Game list `https://www.delottery.com/Instant-Games` — 36 `<div data-toggle="modal" data-gamenumber="512" data-topprize="1,000" data-amount="1" data-gamename="MONOPOLY 5X" data-image="https://delotterywebcontent.blob.core.windows.net/.../DE512CVv4.jpg" data-imagedetailinfo=".../instant-details/DE512OSv3.jpg">`. There are **no per-game pages**; odds/prize structure exist only as an image (`data-imagedetailinfo` JPG).

**Format:** HTML table (ASP.NET). curl → 200, no bot wall. No JSON found.

**Fields:** `Game Number | Game Name | Dollar Amount (price) | Top Prize | Total Top Prizes | Prizes Remaining` — top prize only. No overall odds (image only), no dates (separate Close-Out-Schedule page). Ticket image URL via `data-image`.

**Sample:** `512 | MONOPOLY 5X | $1 | $1,000 | 7 | 1 | 508* | Grand Slam!! | $1 | $1,000 | 12 | 0 | 507 | Cash Smash | $1 | $3,000 | 8 | 5`

**Effort: Blocked (top-prize-only; odds only in images)** — trivially scrapable otherwise.

---

## District of Columbia (DC)

**Main URL(s):**
- Listing `https://dclottery.com/dc-scratchers` (Drupal 10; 20 games per page, `?page=0..3`, 79 games). Programmatic paging: `https://dclottery.com/views/ajax?view_name=listings&view_display_id=scratchers&view_path=/node/616&page=N&_wrapper_format=drupal_ajax` (returns JSON commands whose `data` is the card HTML with `href="/dc-scratchers/{slug}"`, price, "Game No", "Top Prize").
- Per-game: `https://dclottery.com/dc-scratchers/{slug}` e.g. `/dc-scratchers/100x-4` — server-rendered.
- JSON:API (open): `https://dclottery.com/jsonapi/node/game_scratchers?page[limit]=50` (`curl -g`) → `title, path.alias, field_price (list), field_odds ("1:4.74"), field_top_prize (1000), field_top_prize_odds, field_date[{value}], field_last_date_to_claim`. Includes ended games (no `status` filter besides `status`/`moderation_state`). The tier data lives in a custom `prize--prize` entity whose collection route 500s (`Parameter "entity" ... must match`), so tiers are NOT available via JSON:API.

**Format:** HTML table per game (Drupal Views table `table.views-table` with `<th id="view-amount-table-column">` etc.). curl → 200, no bot wall.

**Fields (game page):** Top Prize, Price ("$10.00"), Game No (1652), Start Date (02/04/2026), Odds ("1:3.64"), Top Prize Odds; table `Prize Amount | Total Prizes | Prizes Paid | Prizes Remaining` for ALL tiers. Ticket image in page.

**Sample** (game page, tags stripped): `Prize Amount | Total Prizes | Prizes Paid | Prizes Remaining | $100,000 | 2 | 0 | 2 | $10,000 | 4 | 1 | 3 | $1,000 | 50 | 20 | 30 | $500 | 102 | 46 | 56 | $200 | 102 | 42 | 60 | …`
```html
<td headers="view-amount-table-column" class="views-field views-field-amount">$100,000</td>
<td headers="view-total-table-column" ...>2</td><td headers="view-paid-table-column" ...>0</td><td headers="view-remaining-table-column" ...>2</td>
```
**Effort: Medium** (4 listing pages + 1 request per game, 79 games, all tiers).

---

## Florida (FL)

**Main URL(s) (JSON API):**
- All games with all tiers: `https://apim-website-prod-eastus.azure-api.net/scratchgamesapp/getscratchinfo` — **requires header `x-partner: web`** (without it: 401 `{"statusCode":401,"message":"Missing header"}`). Single game: `?id=1497`. Returns 85 games (66 with EndDate in the future).
- Top prizes: `https://apim-website-prod-eastus.azure-api.net/scratchgamesapp/getTopPrizesRemaining` (same header) → 85 rows `{Id, GameName, TicketPrice, TopPrizes:[{TopPrize:"       $150,000.00", TopPrizesRemaining:"0 of 30*"}]}`.
- Images/how-to-play (AEM, no header): list `https://floridalottery.com/content/flalottery-web/us/en/games/scratch-offs.scratch-offs.json` → `{"data":[{id,name,price,topPrize,isFeatured,teaserImage}]}` (165 games incl. ended); per game `…/scratch-offs.scratch-offs.{id}.json` → adds `ticketFront, howToPlay, gameFamily`.
- Winning-ticket PDF: `https://files.floridalottery.com/exptkt/{Id}_WinningTicketInformation.pdf`.
(Found by unpacking the AEM Vue chunks: `cmp-top-prizes` → `/scratchgamesapp/getTopPrizesRemaining`, `cmp-scratchoffpage` → `/scratchgamesapp/getscratchinfo`, API client sets `headers:{"x-partner":"web"}`.) Old `flalottery.com/remainingPrizes` 301s to `https://floridalottery.com/games/scratch-offs/top-remaining-prizes` (JS-rendered page).

**Format:** JSON. curl → 200 (Azure API Management; no bot wall).

**Fields:** game: `Id ("1497"), GameName, HowToPlay (HTML), TicketPrice (20), LaunchDate ("2024-10-28 00:00:00"), EndDate, RedemptionDate, OverallOdds (2.79), OddsTiers[], Tpr, Gnbr`. Tier: `PrizeAmount ("$5,000,000.00"), WinningOdds ("1-in-3000000"), TotalPrizes, PrizesRemaining, PrizesPaid`. Ids match the AEM `id` (84/85 overlap) → image via AEM JSON.

**Sample** (`getscratchinfo`, one record):
```json
{"Id":"7028","GameName":"THE PERFECT GIFT","TicketPrice":20,"LaunchDate":"2024-10-28 00:00:00","EndDate":"2026-08-24 00:00:00","RedemptionDate":"2026-10-23 00:00:00","OverallOdds":2.79,
 "OddsTiers":[{"PrizeAmount":"$5,000,000.00","WinningOdds":"1-in-3000000","TotalPrizes":4,"PrizesRemaining":2,"PrizesPaid":2}, ... {"PrizeAmount":"$20.00","WinningOdds":"1-in-8","TotalPrizes":1631834,"PrizesRemaining":816813,"PrizesPaid":815021}],"Tpr":"null","Gnbr":"null"}
```
**Effort: Easy** (one JSON call for everything; one extra AEM call for images).

---

## Georgia (GA)

**Main URL(s) (JSON API, no auth):**
- `https://www.galottery.com/api/v1/instant-games/games?size=500` → 285 games (204 `ACTIVE`, 81 `DISABLED`) with all tiers. (Default page is 100 items and its `nextPageUrl` `/instant-games/api/v1/instant-games/games/page?start-item=101` is broken — 404/500 — so use `size=500`, which is what the site JS does: `this.fetch({data:{size:1000}})`.)
- Overall odds (not in the API): per-game AEM page JSON `https://www.galottery.com/en-us/games/scratchers/{gameId}.infinity.json` → `jcr:content.gameOddsAndLike.scratchersoddsandlik.odds = "1 in 3.58"` (also `gameDescription.text`, `gameTitle.text`).
- Ticket image: `https://www.galottery.com/content/dam/portal/images/scratchers-games/{gameId}/thumb.png` (301 → `https://d1gszp1bmamha.cloudfront.net/...`, 200 image/png).
- Top-prizes page `https://www.galottery.com/en-us/games/scratchers/scratchers-top-prizes-claimed.html` embeds inline JSON `{"gameId","gameName","ticketPrice":"$50","topPrize":"$10,000,000","claimed","total"}` — useful to fill in annuitized top prizes (see caveat).

**Format:** JSON. curl → 200 (Akamai-fronted, no challenge).

**Fields:** game: `gameId ("1770"), gameName, validationStatus (ACTIVE/DISABLED), ticketPrice (cents: 5000 = $50), launchDate, startDistributionDate, endDistributionDate, disableDate (epoch ms), prizeTiers[]`. Tier: `tierNumber, prizeAmount (dollars × 10,000: 5000000000 = $500,000; verified vs. top-prizes page), winningTickets (printed), paidTickets (claimed)` → remaining = winningTickets − paidTickets. **Caveat:** annuitized top prizes are encoded as `prizeAmount: 0` (e.g. 1770's $10,000,000 tier: `{"tierNumber":8,"prizeAmount":0,"winningTickets":6,"paidTickets":4}`); take the amount from the top-prizes page JSON. No overall odds or image in the API (see above).

**Sample:**
```json
{"nextPageUrl":null,"games":[{"gameId":"1759","gameName":"JUMBO JUMBO BUCKS","validationStatus":"ACTIVE","ticketPrice":1000,"launchDate":1371182400000,"startDistributionDate":...,"endDistributionDate":...,"disableDate":1796014800000,
  "prizeTiers":[{"tierNumber":1,"prizeAmount":100000,"winningTickets":...,"paidTickets":...}, ... {"tierNumber":N,"prizeAmount":5000000000,"winningTickets":24,"paidTickets":18}]}]}
```
**Effort: Easy** (one JSON call; optional per-game `.infinity.json` for odds).

---

## Summary

| State | Format | All tiers? | Price | Odds | Bot block | Effort | Main URL |
|---|---|---|---|---|---|---|---|
| AZ | JSON API | Yes (`count` remaining / `totalCount`) | Yes (`ticketValue`) | Yes (`gameOdds`, per-tier `odds`) | www: Cloudflare challenge; **api host: none** | **Easy** | `https://api.arizonalottery.com/v2/scratchers/{gameNum}` (+ `/v2/scratchers/topprizes`, `/v2/lookup/games`) |
| AR | HTML per game (Drupal) | Yes (Total / Remaining) | Yes | Yes | **Cloudflare managed challenge on all hosts (curl + urllib 403)** | **Blocked** (Medium if challenge bypassed) | `https://www.myarkansaslottery.com/games/{slug}` |
| CA | JSON list + HTML per game (Sitecore) | Yes ("X of Y") | Yes | Yes (overall + per tier) | None | **Medium** | `https://www.calottery.com/api/Sitecore/ScratchersFilteredList/GetScratchers?modelId=0dc0c687-836a-43d3-aa8b-a0491dbf4001&show=&size=200&page=1&sortBy=&gametype=&price=&nameOrNumber=` + `https://www.calottery.com/scratchers/$10/mystery-crossword-1743` |
| CO | HTML tables | No — printed counts + probability per tier, remaining only for top prize | Yes | Yes | None | **Blocked (top-prize-only)** | `https://www.coloradolottery.com/en/player-tools/scratch-insider/` + `/en/games/scratch/game/{slug}-{num}/` |
| CT | JSON embedded in SSR HTML (Next.js RSC) | Yes (`total` / `remaining`) | Yes (`ticketCostRaw`) | Yes (`overallOdds`) | None | **Medium** | `https://ctlottery.com/games/scratch-games` (list) + `https://ctlottery.com/games/scratch-games/{gameNo}` |
| DE | HTML table | No — top prize only; odds only in an image | Yes | No (image) | None | **Blocked (top-prize-only)** | `https://www.delottery.com/Instant-Games/Top-Prizes-Remaining` (+ `/Instant-Games` for images/data-attrs) |
| DC | HTML table per game (Drupal Views) + JSON:API for metadata | Yes (Total / Paid / Remaining) | Yes | Yes (`1:3.64`) | None | **Medium** | `https://dclottery.com/dc-scratchers?page=0..3` + `https://dclottery.com/dc-scratchers/{slug}` (meta: `https://dclottery.com/jsonapi/node/game_scratchers`) |
| FL | JSON API (needs `x-partner: web` header) | Yes (Total / Remaining / Paid) | Yes | Yes (overall + per tier) | None | **Easy** | `https://apim-website-prod-eastus.azure-api.net/scratchgamesapp/getscratchinfo` (+ `getTopPrizesRemaining`; images via `https://floridalottery.com/content/flalottery-web/us/en/games/scratch-offs.scratch-offs.json`) |
| GA | JSON API | Yes (`winningTickets` / `paidTickets`) | Yes (cents) | Not in API — per-game `.infinity.json` | None | **Easy** | `https://www.galottery.com/api/v1/instant-games/games?size=500` |

Notes for implementers:
- Units: GA `ticketPrice` is cents and `prizeAmount` is dollars×10,000 with `0` for annuitized top prizes; AZ amounts are dollars; FL amounts are `"$5,000,000.00"` strings and odds `"1-in-3000000"`; CT/DC/CA are display strings with commas.
- Update cadence observed: AZ daily 08:00 (`dateModified`); CA "Last Updated" timestamp on page; CT `asOf` date; DE "as of" timestamp; CO "once a day"; AR "daily".
- No open-data-portal datasets (Socrata/CKAN) were found for any of these nine; all data comes from the lottery sites' own endpoints.
