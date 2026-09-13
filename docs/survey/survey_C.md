# Survey C: MA, MI, MN, MS, MO, MT, NE, NH, NJ — scratch-off "prizes remaining" data sources

All requests made 2026-09-12 with curl, `-L`, Chrome 128 User-Agent. No browser tools used. Every URL below was actually hit; status codes and sample payloads are from real responses.

---

## Massachusetts (MA) — masslottery.com

**Stack:** React SPA (Heroku/Fastly, NeoPollard-style) backed by a public JSON API at `https://www.masslottery.com/api/v1`. No Cloudflare challenge; curl gets 200 everywhere.

**Endpoints (all GET, JSON, 200):**
1. `https://www.masslottery.com/api/v1/games` — 167 games (132 `gameType: "Scratch"`). Per game: `name`, `identifier`, `id` (Mass game #), `gameType`, `price`, `odds` ("1 in 3.47"), `topPrize`, `topPrizeDescription`, `startDate`, `expirationDate` (when set), `icon.url` / `gameCollectionIcon` (Contentful image URLs), `tags`.
2. `https://www.masslottery.com/api/v1/instant-game-prizes?gameID=559` — one game, ALL tiers:
   ```json
   {"massGameID":559,"gameName":"DECADE OF DOLLARS","gameIdentifier":"decade-of-dollars-2026","startDate":"2026-08-11","ticketCost":10,"odds":"1 in 3.47",
    "prizeTiers":[{"tierNumber":1,"prizeAmount":10,"totalPrizes":1663200,"paidPrizes":250532,"prizesRemaining":1412668,"prizeDescription":"$10","odds":"1 in 9.09","type":"REGULAR"}, ... 12 tiers, types REGULAR/TOP]}
   ```
3. `https://www.masslottery.com/api/v1/instant-game-prizes/special` — all 132 scratch games in one call, but only `TOP`/`SECONDARY` tiers (1–2 per game). Same tier keys as above minus per-tier odds.
4. `https://www.masslottery.com/api/v1/games/active-prices` — `{"instantGamePricesInDollars":[1,2,5,10,20,30,50]}`.

**Fields:** all tiers with total / paid / remaining, per-tier odds, price, overall odds, game number, start date, image URL. No end date except `expirationDate` on some records.
**Bot block:** none.
**Effort: Easy.** One list call + one call per game (132) for full tiers; or `/special` for top-tier-only in one call.

---

## Michigan (MI) — michiganlottery.com

**Stack:** React SPA (same vendor as MA) with a GraphQL endpoint at `https://www.michiganlottery.com/api/graphql` (POST, JSON). Introspection is disabled, but the queries are readable in the bundle. No bot block.

**Endpoints:**
1. Prizes remaining (ALL tiers, 119 retail instant games):
   ```
   POST https://www.michiganlottery.com/api/graphql   Content-Type: application/json
   {"query":"{ getRetailTopPrizesRemainingByGameType(gameType: \"INSTANT\"){ cms_game_igt_id game_name prizesRemainingData { prize_level prize_amount prizes_remaining starting_amount } } }"}
   ```
   Sample record:
   ```json
   {"cms_game_igt_id":480,"game_name":"DIAMONDS & GOLD $20","prizesRemainingData":[{"prize_level":1,"prize_amount":20,"prizes_remaining":281863,"starting_amount":661347}, ... 11 tiers]}
   ```
   `gameType: "PULL_TAB"` returns the 52 pull-tab games (any unrecognized value also falls through to that set).
2. Game metadata (price, odds, image) from the CMS query:
   ```
   {"query":"{ getCMSGames(removeHiddenGames: true){ name identifier igtId isInstantGame displayedTicketPrice displayedTopPrize overallOdds logoUrl dateAdded gameCategoryIdentifier canBuyInStore } }"}
   ```
   → 475 games; filter `gameCategoryIdentifier == "RETAIL_INSTANT_GAMES_CATEGORY"` (107). Sample: `{"name":"Diamonds & Gold","identifier":"0480_INSTORE_INSTANT_DIAMONDS_GOLD","igtId":480,"displayedTicketPrice":"$20.00","displayedTopPrize":"$2,000,000","overallOdds":"1 in 3.64","logoUrl":"//images.ctfassets.net/...webp","dateAdded":"2024-03-05T00:00-05:00"}`
   Join key: `igtId` == `cms_game_igt_id` (107/107 CMS games matched; 12 prize-only games are presumably ended/unlisted).

**Fields:** all tiers (starting + remaining; paid = derived), price, overall odds, game number (igtId), launch date (`dateAdded`), image. No per-tier odds, no end date.
**Bot block:** none.
**Effort: Easy.** Two POSTs total.

---

## Minnesota (MN) — mnlottery.com

**Stack:** Craft CMS site (server-rendered) plus a "GameOn" (Pollard/pblb2c) React widget for unclaimed prizes, backed by a public gateway API. No bot block.

**Endpoints:**
1. `https://gateway.gameon.mnlottery.com/services/game/api/published-games?gameTypeId.in=1&sort=gameId,desc&excludeFeatured=false&page=0&size=200` — 200 JSON, Spring page (`content`, `totalElements`, ...). 40 scratch games. Per game: `id` (internal), `gameId` ("2107" = printed game #), `name`, `playBegin`, `playEnd`, `playExpiry`, `retailPrice` (20.0), `topPrize`, `overallOdds` (3.07), `ticketPosImage`/`ticketFullImage`/`ticketScratchedImage` (URLs), `howToPlay`, `state`.
2. `https://gateway.gameon.mnlottery.com/services/game/api/published-games/{id}/prizes` (e.g. `/265/prizes`) — 200 JSON:
   ```json
   [{"prize":"500","totalPrizes":452,"remainingPrizes":425},{"prize":"1000","totalPrizes":585,"remainingPrizes":565}, ... ,{"prize":"500000","totalPrizes":3,"remainingPrizes":3}]
   ```
   **Only tiers ≥ $500 are published** (the site states "Only prizes of $500 or more are listed here"). Lower tiers are absent.
3. Full prize structure (totals + odds, no remaining) is server-rendered on each game page, e.g. `https://www.mnlottery.com/games/scratch/10000-large` — `<table class="bulletin-matrix-table">` with columns To Win / Odds / Number of Prizes (all tiers). Listing `https://www.mnlottery.com/games/scratch` is server-rendered with price per card.
   (Note: `/services/game/api/game/prizes/unclaimed?gameTypeIds=…` is the draw-game unclaimed-winner list, not scratch.)

**Fields:** price, overall odds, game #, start/end dates, images, remaining counts for ≥$500 tiers only; full totals/odds from HTML.
**Effort: Medium** — JSON is easy, but remaining counts for sub-$500 tiers do not exist anywhere on the site, so EV needs estimation for low tiers.

---

## Mississippi (MS) — mslottery.com

**Stack:** WordPress (Beaver Builder). WP REST API is open. No bot block. Note `/scratch-offs/` 404s; the listing is `https://www.mslottery.com/gamestatus/active/`.

**Endpoints:**
1. `https://www.mslottery.com/wp-json/wp/v2/instantgames?per_page=100&gamestatus=25` — 200 JSON, 76 active games. Keys: `id, slug, title.rendered, link, content.rendered, featured_media, gamevalue, gamestatus, yoast_head_json.og_image`. `acf` is empty. The prize table is HTML inside `content.rendered` (all tiers):
   ```
   Prize Value | Original Prize Count | Remaining Prize Count
   $200,000 | 3 | 3 … $10 | 100,698 | 93,990   Last updated 09/12/2026
   ```
2. Price via taxonomy: `https://www.mslottery.com/wp-json/wp/v2/gamevalue` → `{13:"$1 Ticket",14:"$2",24:"$3",15:"$5",18:"$10",32:"$20",294:"$30"}` (ids map to `gamevalue[0]`).
3. Overall odds / game number are NOT in the REST content; they are in the per-game HTML page (`link`, e.g. `https://www.mslottery.com/instantgames/ultimate-lucky-7s/`): "Ticket Price $10 Top Prize $200,000 Overall Odds 1:4.26 Game Number 264 Game Status Active".

**Fields:** all tiers (original + remaining), price, image, last-updated; odds + game # need one HTML fetch per game. No start/end dates seen.
**Effort: Easy/Medium** — one REST call covers all tiers; add 76 page fetches if odds/game# needed.

---

## Missouri (MO) — molottery.com

**Stack:** Java/JSP site behind Cloudflare (no challenge). IMPORTANT: `https://www.molottery.com/scratchers` (and `/scratchers/`) returns an Apache **403 for every UA** (path-level block), but the actual data pages are `.do` routes that return 200.

**Endpoints (server-rendered HTML, 200):**
1. `https://www.molottery.com/scratchers-list.do` — 417 KB, all 85 active games in `div.scratchers-list__item`. Per game: tile image `https://www.molottery.com/media/scratchers/tile/{game#}.png`, Start Date, End Date, Ticket Price, Top Prize, Total Won, Total Unclaimed, and a `<table class="scratchers-list__table">` with columns Top Prizes / Total / Unclaimed for the top ~4 tiers only. Link `scratchers.do?method=d&game=561`.
2. `https://www.molottery.com/scratchers.do?method=d&game=359` — per-game detail, ALL tiers: table `Prize Level | Total Prizes | Unclaimed Prizes` (e.g. `$20 | 463,709 | 89,893 … $2,000,000 | 2 | 1`), plus "Game #359", Official Start Date, End Date, Expire Date, Ticket Price, Top Prize, "Average Chances*: 1 in 3.04".

**Fields:** all tiers (total + unclaimed), price, overall odds, game #, start/end/expire dates, image.
**Effort: Medium** — HTML tables, one request per game (85).

---

## Montana (MT) — montanalottery.com

**Stack:** WordPress + Elementor (Unlimited Elements repeater tables, Ninja Tables). No bot block. `/en/view/scratch` redirects to `http://montanalottery.com/scratch-games/`.

**What exists:**
- `https://montanalottery.com/scratch-games/` (paginated `?e-page-eeedf9c=2..11`) — each game card has a `<table class="ue-repeater-table-table">` with columns WIN / PRIZE / ODDS (e.g. `C5"X" | $25,000 | 1:74,850.00`). Odds only — no prize counts, no remaining counts.
- `https://montanalottery.com/unclaimed-prizes/` — Ninja Table loaded via `https://montanalottery.com/wp-admin/admin-ajax.php?action=wp_ajax_ninja_tables_public_action&table_id=298&target_action=get-all-data&default_sorting=old_first` (200 JSON) — but it lists unclaimed **draw-game** winning tickets by retailer, not scratch tiers.
- `https://montanalottery.com/wp-content/uploads/2026/07/Scratch-End-Dates-07-28-26.pdf` — end dates only.
- Web search found no "prizes remaining" page for MT scratch games.

**Effort: Blocked** — Montana does not publish remaining-prize counts for scratch games at all (only odds tables). Price is on the card; totals are not published.

---

## Nebraska (NE) — nelottery.com

**Stack:** Server-rendered Java app under `/homeapp/`. No bot block.

**Endpoints (HTML, 200):**
1. `https://nelottery.com/homeapp/scratch/prizesremaining/web` — 25 games in `div.gameBlock`: price (`span.ballDollar`), game # and name (`div.nameBlock`: "#1396 PAC-MAN"), tile image `https://nelottery.com/homeapp/static/shared/images/scratch/tiles/1396_tile.jpg`, and `<table class="prizeRemBlock">` (Prize | Prize Count | Top Prize Flag). **Only the top 2–3 tiers per game** are listed, and only the remaining count (no starting count), e.g. `$50,000 | 4`, `$5,000 | 18`, `$1,500 | 29`.
2. `https://nelottery.com/homeapp/scratch/{game#}/0/gamedetail/web` — per-game `<table class="numbertable">` Prize | Odds | Winners (total printed winners per prize combination, all tiers) plus "Overall odds 1 in 3.87". No remaining counts.
3. `https://nelottery.com/homeapp/scratch/gamessummary` — list of games, no table.

**Fields:** price, game #, image, overall odds, full totals (per game); remaining only for top tiers.
**Effort: Blocked (top-prize-only remaining).** Everything else is Medium-difficulty HTML.

---

## New Hampshire (NH) — nhlottery.com

**Stack:** React SPA (Gambyt/NeoPollard "nh-portal") on Cloudflare (no challenge). Same-host JSON API at `https://www.nhlottery.com/api/v1/...` for game metadata; the prizes-remaining data comes from a separate Gambyt "game-data" service that needs an `X-API-Key` header — the key is hard-coded in the public bundle (`https://d1e076uakedhdo.cloudfront.net/index.js`, `GAME_DATA_API_KEY`). Without the key → 401 `{"message":"Invalid API Key"}`.

**Endpoints:**
1. `https://www.nhlottery.com/api/v1/game/all` — 200 JSON, `data.games[]` (95 `type:"scratch"`). Per game: `name`, `identifier`, `startDate` ("09/03/2026"), `topPrizeDisplay`, `price.priceInCents`, `odds` (4.08), `ticketsOrdered`, `imageUrl`, `previewImageUrl`, `configuration.dataServices.gameDataServiceId` (UUID join key).
2. `https://www.nhlottery.com/api/v1/game/prize-table?identifier=Patriots` — 200 JSON `data.prizeTable.{headers,rows}`; rows like `["$5","", " $5.00 "," 97,028 "," 9.52 "]` (Get / Bonus / Win / Prizes in Game / Odds of 1 in). Totals only, by win combination.
3. Prizes remaining (ALL games at once):
   ```
   GET https://prod.game-data.gambytservices.com/v1/instant-game/prizes-remaining
   X-API-Key: 1c4c69db-274c-4f59-95c5-3211cd74e9d8
   ```
   → 200 JSON, 176 KB: `{"lastUpdated":"2026-09-12T03:06:58.820Z","prizesRemaining":[{"id":"…","instantGameId":"00f2e872-0388-46b0-941d-d63ba161bf51","startingCount":2315,"remainingCount":885,"prizeDescription":"$1,000 Prize","prizeAmountInDollars":1000,"sortOrder":0,"ticketCostOptionsInCents":[2000]}, …]}` — 586 rows over 59 games (2–15 tiers each; appears to be all prize amounts). Filter with `?instantGameId=<uuid>`. `instantGameId` == `gameDataServiceId` from `/game/all` (59/59 joined; the other 36 scratch games have no rows — likely new/ended).
   `…/prizes-remaining/filters` → `{"ticketCostOptionsInCents":[…]}`.

**Fields:** all tiers (starting + remaining), price, overall odds, start date, image, tickets ordered, last-updated. Game number only via image filename (`NH_1708_…`).
**Effort: Easy** (two GETs) — caveat: relies on an API key scraped from the public bundle; re-scrape `GAME_DATA_API_KEY` from `index.js` if it rotates.

---

## New Jersey (NJ) — njlottery.com

**Stack:** AEM portal with a public JSON API. No bot block; curl 200.

**Endpoints (GET, JSON):**
1. `https://www.njlottery.com/api/v1/instant-games/games?size=200` and `…/games/page?size=200&start-item=201` (287 games total; `validationStatus` ACTIVE=46 / DISABLED). Top keys: `nextPageUrl, previousPageUrl, games[]`. Game record:
   ```json
   {"gameId":"1785","gameName":"Power 10X","validationStatus":"ACTIVE","ticketPrice":1000,"launchDate":1675486800000,"startDistributionDate":1672635600000,"endDistributionDate":1748404800000,"disableDate":1793768400000,"totalTicketsPrinted":…,
    "prizeTiers":[{"tierNumber":1,"prizeAmount":1000,"winningTickets":1153512,"paidTickets":874024,"claimedTickets":20,"prizeDescription":"FREE $10 TICKET","originalTierNumber":1,"tierType":2}, …]}
   ```
   Amounts are in cents; dates are epoch ms. All tiers present. Remaining = `winningTickets - paidTickets` (`claimedTickets` is a small separate "in-process claims" number — verify semantics).
2. `https://www.njlottery.com/api/v1/instant-games/games/1785` — single game, same shape.
3. Ticket image: `https://www.njlottery.com/content/dam/portal/images/instant-games/01785/ticket.png` (5-digit zero-padded gameId; `@2X.png` variant). Per-game HTML page `https://www.njlottery.com/en-us/scratch-offs/01785.html` is a JS template over the same API and contains **no overall-odds figure** — odds are not published by the API or page.

**Fields:** all tiers (winning / paid / claimed), price, game #, launch/distribution/disable dates, total tickets printed, image. **No overall odds** (derive as printed/sum(winning)).
**Effort: Easy.**

---

## Summary

| State | Format | All tiers? | Price | Odds | Bot block | Effort | Main URL |
|---|---|---|---|---|---|---|---|
| MA | JSON API | Yes (total/paid/remaining + per-tier odds) | Yes | Yes | None | Easy | `https://www.masslottery.com/api/v1/instant-game-prizes?gameID={id}` (+ `/api/v1/games`) |
| MI | GraphQL (POST) | Yes (starting/remaining) | Yes (CMS query) | Yes (CMS query) | None | Easy | `POST https://www.michiganlottery.com/api/graphql` `getRetailTopPrizesRemainingByGameType(gameType:"INSTANT")` |
| MN | JSON API (+ HTML for low tiers) | No — remaining only for tiers ≥ $500; totals for all tiers via HTML | Yes | Yes | None | Medium | `https://gateway.gameon.mnlottery.com/services/game/api/published-games?gameTypeId.in=1&size=200` + `/published-games/{id}/prizes` |
| MS | WP REST JSON with HTML table inside | Yes (original/remaining) | Yes (taxonomy) | HTML page only | None | Easy/Medium | `https://www.mslottery.com/wp-json/wp/v2/instantgames?per_page=100&gamestatus=25` |
| MO | HTML tables (server-rendered) | Yes (total/unclaimed) on detail page; top ~4 on list | Yes | Yes ("Average Chances") | `/scratchers` path 403, `.do` routes fine | Medium | `https://www.molottery.com/scratchers-list.do` + `scratchers.do?method=d&game={n}` |
| MT | HTML (odds tables only) | No remaining data at all | Yes | Per-tier odds only | None | Blocked | `https://montanalottery.com/scratch-games/` |
| NE | HTML tables | No — remaining for top 2–3 tiers only; totals all tiers per game | Yes | Yes | None | Blocked (top-prize only) | `https://nelottery.com/homeapp/scratch/prizesremaining/web` |
| NH | JSON API (needs public X-API-Key) | Yes (starting/remaining) | Yes | Yes | None (401 without key) | Easy | `https://prod.game-data.gambytservices.com/v1/instant-game/prizes-remaining` + `https://www.nhlottery.com/api/v1/game/all` |
| NJ | JSON API | Yes (winning/paid/claimed) | Yes | No | None | Easy | `https://www.njlottery.com/api/v1/instant-games/games?size=200` |

Open-data portals: no scratch remaining-prize datasets found on data.nj.gov, data.mo.gov, data.michigan.gov, data.mass.gov, or mn.gov for these states (web search returned only third-party trackers). MA and MI share the same vendor platform (Heroku/Fastly SPA + Contentful), and NH's Gambyt API pattern is likely reused by other Gambyt-run lotteries.
