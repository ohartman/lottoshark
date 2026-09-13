# Survey D: NM, NC, ND, OH, OK, OR, PA, RI, SC — scratch-off "prizes remaining" data sources

Surveyed 2026-09-12 with curl (Chrome UA, `-L`) and stdlib Python parsing. No browser tools used.
All raw responses are saved under the scratchpad (`nm/`, `nc/`, `oh/`, `ok/`, `or/`, `pa/`, `ri/`, `sc/`, `nd/`).

---

## New Mexico (NM)

- **Main URL:** `https://www.nmlottery.com/games/scratchers/` (WordPress 7.1 + Divi + Search & Filter Pro; fully server-rendered)
- **Format:** HTML, one page, all 56 active games with an embedded `<table class="data">` per game. No pagination (`Found 56 Results`; 56 `filter-block`s, 56 tables). WP REST (`/wp-json/wp/v2/`) is enabled but scratchers are not exposed as a CPT (`project` type returns `[]`), so HTML is the source.
- **Fields per game:** name (`<h3>`), top prize (`p.top-prize`), price (`p.price`), start date (`p.start-date`), how-to-play, overall odds text ("Approximate overall odds of winning (includes breakeven prizes): 1 in 3.89"), game number (`p.game-number`), ticket image (`div.scratcher-image img`, e.g. `https://www.nmlottery.com/wp-content/uploads/2026/09/692.jpg`), and a prize table with **all tiers**: `Prize | Approx. Odds 1 in | Approx. # of Prizes | Approx. Prizes Remaining`.
- **Secondary:** `/games/scratchers/games-ending/` (end-of-game schedule), `/games/scratchers/top-prizes-not-yet-claimed/` (content is not in HTML — appears to be loaded another way; not needed since the main page has everything).
- **curl:** 200, 448 KB, real content. No bot wall.
- **Sample (game 692 "Frogger"):**
  ```html
  <p class="top-prize"><em>Top Prize: &#36;5,000</em></p>
  <p class="price">&#36;3</p>
  <p class="start-date"><strong>Start Date:</strong> September 1, 2026</p>
  ... Approximate overall odds of winning (includes breakeven prizes): 1 in 3.89 ...
  <p class="game-number"><strong>Game Number:</strong> 692</p>
  <table class="data"> <thead><tr><th>Prize:</th><th>Approx. Odds 1 in:</th><th>Approx. # of Prizes:</th><th>Approx. Prizes Remaining:</th></tr></thead>
  <tr><td>$5,000.00</td><td>166,000</td><td>3</td><td>3</td></tr>
  <tr><td>$1,000.00</td><td>83,000</td><td>6</td><td>5</td></tr>
  ...
  <tr><td>$3.00</td><td>8.33</td><td>59,760</td><td>57,381</td></tr>
  ```
  Note the malformed `</ th >` / `</ tr >` tags in `<thead>` — parse with a regex or a lenient HTMLParser, not strict XML.
- **Effort: Easy** (single HTML page, all tiers, price, odds, game number, start date, image).

---

## North Carolina (NC)

- **Main URL:** `https://nclottery.com/scratch-off-prizes-remaining` (ASP.NET WebForms, server-rendered; 786 KB)
- **Format:** HTML, one page, **79 games**, one `<table class="datatable">` per game inside `<div class="box cloudfx databox price_N">` (price is in the class name: `price_1 … price_50`). Columns: `Value | Odds 1 in | Total | Remaining`, cells carry classes `PrizeValue`, `OriginalOdds`, `PrizeCount`, `PrizeCountRemaining`. Header row has thumbnail (`/Content/Images/Instant/nc996_sqr.png`), name, link to per-game page, and `Game Number`. Footer text gives the as-of date ("prizes not yet claimed through **9/11/2026**"; "Reordered" flag possible).
- **Per-game pages:** `https://nclottery.com/scratch-off/{gameNumber}/{slug}` (e.g. `/scratch-off/1/5-times-lucky`) — same tier table plus `span.price.value` ("$5"), `span.odds.value` ("1 in 4.28"), `span.topprize.value`, status, sample-ticket image `/Content/Images/Instant/nc001.jpg`. Listing of all games with links: `https://nclottery.com/scratch-off` (79 links).
- **Missing from the all-games page:** overall odds and start date (need the per-game page for overall odds; start date not seen — check `/scratch-off-games-ending` for end dates).
- **API:** page defines `NcelServicesUrl = "https://services.nclottery.com/"` but it is only used for draw/ticket features; root returns 404. No JSON needed.
- **curl:** 200 real content. No bot wall (Exponea analytics only).
- **Sample:**
  ```html
  <div class="box cloudfx databox price_10">
   <table class="datatable"><thead><tr><th colspan="4" class="ticketdetails">
     <span class="gamethumb"><a href="/Content/Images/Instant/nc996_sqr.png" ...>
     <span class="gamename"><a href="/scratch-off/996/1000000-triple-play">$1,000,000 Triple Play</a></span>
     <span class="gamestats"><span class="gamenumber"><b>Game Number:</b> 996</span></span>
   <tr><th>Value</th><th>Odds 1&nbsp;in</th><th>Total</th><th>Remaining</th></tr></thead>
   <tbody><tr>
     <td><span class="PrizeValue">$1,000,000</span></td>
     <td><span class="OriginalOdds">1,469,394</span></td>
     <td><span class="PrizeCount">5</span></td>
     <td><span class="PrizeCountRemaining">4</span></td></tr> ...
  ```
- **Effort: Easy** (one HTML page with all tiers + price + game number; add per-game fetch only if overall odds are needed — or compute odds from `Total` counts and tier odds).

---

## North Dakota (ND)

- **No scratch-off games.** ND Lottery sells draw games only (Powerball, Mega Millions, Lucky for Life, Lotto America, 2by2, Millionaire for Life). `https://www.lottery.nd.gov/` → `/public`, 200; game links are `/games/2-by-2`, `/games/lotto-america`, `/games/lucky-for-life`, `/games/mega-millions`, `/games/millionaire-for-life`, `/games/powerball` only. Home page has zero "scratch"/"instant" mentions.
- **Effort: N/A** — skip this jurisdiction.

---

## Ohio (OH)

- **Main URL:** `https://www.ohiolottery.com/games/scratch-offs/prizes-remaining` (Kentico CMS; page shell is server-rendered but the data is a Vue component `<prizes-remaining>` mounted by `/dist/js/app.js`).
- **Format:** **JSON API, JS-rendered page.** The Vue bundle calls:
  - `https://api-solutions.ohiolottery.com/1.0/Games/ScratchOffs/ScratchOffGame/GetFullPrizesRemainingList`
  - `.../ScratchOffGame/GetAllGames`, `.../GetAllGamesWithLastDayToRedeemSet`
  - `.../ScratchOffGame/GetPrizeRemainingListByGameID/{id}`
  - `.../ScratchOffGame/GetGameInformation?gameCode={n}&getAllGameInfo=true`
  All require `Authorization: Bearer <token>`; without it they return **401** (verified). The token comes from `POST https://authapi-solutions.ohiolottery.com/1.0/Authentication/Login` (`Content-type: application/json-patch+json`, body `{"userName":..., "password":...}`), and `/global.js` (`mtllc_getAPItoken`) contains a hard-coded public "mobilepublic" account used for every anonymous visitor; the token is cached in a `TokenInfo` cookie.
  **I did not perform the login** (it is a password-authenticated request); the endpoints above are documented from the bundle. From the Vue template, the response shape is `data[]` of games with `gameId` and `prizeRemainingValues[]` of `{description, prizesLeft, ...}` (tier rows, so all tiers) and a game object with `oddsOfWinning`, `gameGraphicURL`, `gameRulesPDFURL`. Per-game HTML pages expose `name`, `price`, `number`, `odds` as hidden inputs (Vue reads `document.getElementById("price").value`), but the listing is also Vue-rendered (`<scratchoffs-list>`), so there is no server-rendered list of game URLs; `sitemap.xml`/`robots.txt` are 404.
- **Fields (from template):** all prize tiers (`description`, `prizesLeft`), game id/number, price, overall odds, graphic URL, rules PDF, last-day-to-redeem.
- **curl:** HTML 200 (108 KB, no data); API 401 without token. No bot wall on the site itself.
- **Effort: Hard/Blocked** — JSON with all tiers exists, but every call needs a Bearer token obtained by logging in with the credentials embedded in the site's `global.js`. Whether to use that public embedded account is a policy decision for the project; if acceptable it becomes Easy (2 requests).

---

## Oklahoma (OK)

- **Main URL:** `https://oklottery.com/games/scratchers` (Next.js App Router, Contentful-backed; **server-rendered RSC payload** in `self.__next_f.push(...)` script tags — no headless browser needed)
- **Format:** JSON embedded in HTML (React Flight). Listing page contains `"scratchOffs":[...]` with **96** games. Each per-game page `https://oklottery.com/games/scratchers/{gameNumber}-{slug}` (e.g. `/games/scratchers/834-jaws`) embeds the full game record. Sending header `RSC: 1` returns just the flight payload (`text/x-component`, ~50 KB vs 235 KB HTML). Decode: join the `self.__next_f.push([1,"..."])` string segments, unescape, then locate the JSON object starting at `{"howToPlay"`.
- **List record keys:** `ribbonColor, gameId, gameNumber, topPrize, slug, title, imageAltText, order, ticketPrice, pullTab, startDate, endDate, ribbonType, image{url}, appImage{url}`.
- **Game record keys:** `howToPlay, rulesPdf, gameId, gameNumber, topPrize, slug, prizeDetails, title, imageAltText, startDate, endDate, claimEndDate, order, ticketPrice, totalTickets, odds, pullTab, oddsDetails, image, appImage, gameConfig`.
- **Tier records:** `prizeDetails[0].matches[] = {"prize":"$$10","remainingPrizes":47880,"totalPrizes":104150}` (all tiers); `oddsDetails[0].matches[] = {"odds":6,"prize":"$$10"}`. Note the doubled `$$` in prize strings (Contentful escaping) — strip it.
- **Sample:**
  ```json
  {"gameId":70,"gameNumber":"834","topPrize":100000,"slug":"834-jaws","title":"JAWS",
   "startDate":"2026-04-09T00:00:00.000-05:00","endDate":null,"claimEndDate":null,
   "ticketPrice":10,"totalTickets":624720,"odds":"1 in 3.00",
   "prizeDetails":[{"matches":[{"prize":"$$10","remainingPrizes":47880,"totalPrizes":104150},
                                {"prize":"$$20","remainingPrizes":32191,"totalPrizes":72869}, ...]}],
   "oddsDetails":[{"matches":[{"odds":6,"prize":"$$10"},{"odds":8.57,"prize":"$$20"}, ...]}],
   "image":{"url":"https://images.ctfassets.net/gziyj7mnq57m/.../834_JAWS_web_tile.jpg"}}
  ```
- **curl:** 200 with full data (listing 298 KB; game page 235 KB; RSC 50 KB). No bot wall.
- **Effort: Medium** (1 listing + 1 request per game, ~97 requests; all tiers, price, odds, dates, total tickets, image — very complete).

---

## Oregon (OR)

- **Main URL:** `https://www.oregonlottery.org/scratch-its/list/` (WordPress; the list and per-game pages are **placeholders filled by JS** — `data-lottery="scratchGame.TicketPrice"`, `scratchGame.OverallOdds`, `scratchGame.DateAvailable`, `scratchGame.GameEndDate`, `scratchGame.SellThroughRate`, `scratchGame.ValidationEndDate`, `.ol-table-scratchits__loader`). WP REST is disabled (`/wp-json/` returns the HTML home page).
- **Underlying API (from `/wp-content/plugins/pollinate-ol-api/js/min/main.min.js`):**
  - `GET https://api.oregonlottery.org/gameinfo/v1/instant/games` (all games)
  - `GET https://api.oregonlottery.org/gameinfo/v1/instant/games?gameNumber={n}&includePrizeTiers=true` (per game with tiers)
  Response shape: `{ "InstantGames": [ { TicketPrice, DateAvailable, TopPrize, OverallOdds, GameEndDate, SellThroughRate, ValidationEndDate, PlayStyle, ... , prize tiers when includePrizeTiers=true } ] }`.
  Auth: headers `client_id` and `client_secret`, computed at runtime by `unscramble()` in `/wp-content/plugins/pollinate-ol-api/js/helpers.js` (Caesar shift + chunk rearrangement) from the page's inline `var olapi = {"newClient": "...", "newSecret": "..."}` values. Without them the API returns **401 `{"error":"Authentication denied."}`** (verified; the older `Ocp-Apim-Subscription-Key` = `olapi.apikey` also gets 401). **I did not decode or use the client secret.** A scraper would have to port `unscramble()` and send the derived headers — i.e. use the site's obfuscated app credentials; policy call for the project.
- **Fields (from JS):** price, top prize, overall odds, on-sale date, end date, validation end date, sell-through %, play style; per-tier data via `includePrizeTiers=true` (field names not verified because the call is gated).
- **curl:** site 200; API 401 without derived headers. No bot wall.
- **Effort: Hard** (JSON API likely with all tiers, but behind obfuscated client credentials that must be reverse-engineered from the page; no server-rendered fallback).

---

## Pennsylvania (PA)

- **Main URL:** `https://www.palottery.pa.gov/Scratch-Offs/Prizes-Remaining.aspx` (redirects from `palottery.state.pa.us`; Kentico/WebForms, server-rendered, 316 KB)
- **Format:** HTML, one `<table>` for all active games (~71 games; `Active-Games.aspx` lists 71 `View-Scratch-Off.aspx?id=` links). Columns: `Game # | Game Name | Price | Top Six Prizes | Wins Remaining` — each row has the six highest prize values and the corresponding remaining counts; flags like "NEW", "Second-Chance Eligible", "Available on iLottery". A price filter `<select>` exists (postback), default shows all.
- **Per-game page:** `https://www.palottery.pa.gov/Scratch-Offs/View-Scratch-Off.aspx?id={id}` — same top-six table, plus "Overall chances of winning a prize: 1:4.66", price in prose ("Quick Cash is a $1 game…"), game number "(PA-1280)", claim deadline text. **No total-printed counts and no tiers below the top six** anywhere.
- **curl:** 200 real content. No bot wall.
- **Sample (row):**
  `NEW | 1806 | Cash Grab | $1 | $1,000 $150 $100 $50 $30 $15 | 50 143 1,559 6,391 4,262 72,308`
- **Effort: Blocked** for EV (top-six remaining only, no printed totals; low tiers omitted). Usable only for a "top prizes remaining" view (Easy HTML).

---

## Rhode Island (RI)

- **Main URL:** `https://www.rilot.com/en-us/instantgames.html` (Adobe AEM / IGT iLottery portal; 665 KB but the game list and prize tables are **Backbone templates filled from an API**)
- **Format:** JS-rendered. The client model `InstantGame` fetches `{convenienceCloudApi}/api/v1/instant-games/games/` with `convenienceCloudApi = https://ris.p1.awc.lotteryservices.net` (IGT "ESA"); listing uses `?size=1000`, detail `…/games/{gameId}`. Both return **401 `{"code":"NOT_AUTHORIZED"}`** without a player-session OAuth token (`Authorization: OAuth <token>` injected by `authServiceProvider` in the portal's `home.js`; tokens come from the IGT player gateway `/gk/controller/AuthenticationServlet`). Not attempted.
  The template shows the tier fields: `game.prizeTiers[] = {tierNumber, prizeAmount, winningTickets, paidTickets}` (remaining = winningTickets − paidTickets), i.e. **all tiers** exist behind the wall. Per-game AEM content is public at `https://www.rilot.com/en-us/instantgames/{gameId}.infinity.json` (200; `jcr:title`, `subtitle`, top-prize text, images) but contains no counts.
- **Server-rendered fallback:** `https://www.rilot.com/en-us/instantgames/validation-end-dates.html` — HTML table `Game # | Game Name | Game Start Date | Game End Date | Last Day To Redeem Winning Tickets` (no prizes).
- **curl:** site 200; ESA API 401. No bot wall on the portal.
- **Effort: Blocked** (tier data only via an authenticated IGT player-session API).

---

## South Carolina (SC)

- **Main URL (summary):** `https://www.sceducationlottery.com/Games/PrizesRemaining` (ASP.NET MVC, server-rendered, 147 KB) — one table, **58 games**: `Game Name (#gameNumber) | Ticket Price | Start of Game | Value of Top Prize | Number of Estimated Remaining Or Unclaimed Top Prizes | Estimated Value of Remaining Or Unclaimed Total Prizes | Last Day to Sell | Last Day to Claim`, with "No longer available to purchase." markers.
- **Per-game (all tiers):** `https://www.sceducationlottery.com/Games/InstantGame?gameId={gameNumber}` (e.g. `?gameId=1578`; 58 links on `/Games/InstantGames`). Server-rendered table: `Prize Amount By Prize Level | Estimated Number of Unclaimed Prizes | Estimated Value of Unclaimed Prizes | Number of Prizes at Start of Game | Value of Prizes at Start of Game`, plus info blocks `Last Updated`, `Price`, `Start of Game`, `Last Day to Sell`, `Last Day to Claim`, ticket image, and the game number in the `<title>` ("Giant Jumbo Bucks (Game #1578)").
- **Missing:** overall odds and total tickets printed — not on the game page, the listing, or `/Games/Odds` (that page has draw-game odds only and a dead "FOR INDIVIDUAL SCRATCH-OFF ODDS CLICK HERE" span). Expected value per ticket therefore cannot be computed from the site alone unless total tickets are obtained elsewhere (e.g., game rules PDFs).
- **curl:** 200 real content. No bot wall.
- **Sample (game 1578):**
  ```
  Price: $5 | Start of Game: 08/18/2025 | Last Day to Sell: 08/10/2026 | Last Day to Claim: 01/26/2027
  $250,000 | 0 | $0 | 6 | $1,500,000
  $1,000   | 7 | $7,000 | 50 | $50,000
  ...
  $5 | 131,569 | $657,845 | 713,247 | $3,566,235
  ```
- **Effort: Medium** (1 listing + 1 request per game; all tiers with start/remaining counts, price, dates, image; no odds/total tickets).

---

## Summary

| State | Format | All tiers? | Price | Odds | Bot block | Effort | Main URL |
|---|---|---|---|---|---|---|---|
| NM | HTML, single server-rendered page (WordPress) | Yes (printed + remaining + tier odds) | Yes | Yes (overall) | None | **Easy** | `https://www.nmlottery.com/games/scratchers/` |
| NC | HTML, single server-rendered page (WebForms) | Yes (total + remaining + tier odds) | Yes (CSS class `price_N`) | Per-game page only | None | **Easy** | `https://nclottery.com/scratch-off-prizes-remaining` |
| ND | — no scratch-off games sold | — | — | — | — | N/A | `https://www.lottery.nd.gov/` |
| OH | JSON API (Bearer token) behind Vue page | Yes (per bundle template) | Yes | Yes | None, but API needs login token (embedded public creds in `global.js`) | **Hard/Blocked** (policy) | `https://api-solutions.ohiolottery.com/1.0/Games/ScratchOffs/ScratchOffGame/GetFullPrizesRemainingList` |
| OK | JSON embedded in Next.js RSC payload (server-rendered) | Yes (total + remaining + tier odds) | Yes | Yes (+ totalTickets) | None | **Medium** (1 + 96 requests) | `https://oklottery.com/games/scratchers` + `/games/scratchers/{n}-{slug}` |
| OR | JSON API (`api.oregonlottery.org/gameinfo/v1/instant/games`) | Likely (`includePrizeTiers=true`), unverified | Yes | Yes | 401 without obfuscated `client_id`/`client_secret` | **Hard** | `https://api.oregonlottery.org/gameinfo/v1/instant/games` |
| PA | HTML table (server-rendered) | No — top six prizes, remaining only, no totals | Yes | Per-game page | None | **Blocked** (top-prize-only) | `https://www.palottery.pa.gov/Scratch-Offs/Prizes-Remaining.aspx` |
| RI | JS (AEM/IGT) over authenticated ESA API | Yes, but behind OAuth player session | Yes | Unknown | API 401 | **Blocked** | `https://www.rilot.com/en-us/instantgames.html` |
| SC | HTML (server-rendered) listing + per-game pages | Yes (start + unclaimed counts) | Yes | No (no odds / total tickets) | None | **Medium** (1 + 58 requests) | `https://www.sceducationlottery.com/Games/PrizesRemaining` + `/Games/InstantGame?gameId={n}` |

Recommended first targets: **NM** and **NC** (single-page HTML with everything), then **OK** (rich JSON, one request per game), then **SC** (all tiers but no odds).
