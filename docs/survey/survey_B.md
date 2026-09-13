# Survey B: scratch-off "remaining prizes" data sources (ID, IL, IN, IA, KS, KY, LA, ME, MD)

Surveyed 2026-09-12 with `curl -L -A "<Chrome 128 UA>"` from this machine (no browser). Every URL below was actually fetched; sample snippets are pasted from the real responses. Saved raw pages live in `scratchpad/pages/`.

Legend for "All tiers?": **Yes** = every prize tier has both a total (printed) count and a remaining count; **Remaining only** = every tier has a remaining count but no printed total; **Partial** = only some tiers; **Top only** = only the top prize(s).

---

## Idaho (ID)

**Site tech:** Drupal 10 with JSON:API enabled (`/jsonapi` returns 200). Ticket images on CloudFront.

**1. Pages / feeds**
- Listing (server-rendered, includes prize tables): `https://www.idaholottery.com/games/scratch` (also `?view=remaining_prizes`, and `/games/scratch/{price}`). 64 `li.game[data-game-id]` cards, each with an inline `table.scratch-prizes` (Prize / Remaining) and a hidden `span.game__sold` (fraction sold).
- Per-game page: `https://www.idaholottery.com/games/scratch/mega-cash` -> `table.full-rules-and-odds.prize-chart-table` with columns **Number of Prizes | Prize Amount | Remaining Prizes | Odds**, plus text "1:2.71 overall odds", "0.71 % sold", "Tickets Printed: 543,825", "Launch Date : 09/08/2026".
- **JSON:API (best):**
  `https://www.idaholottery.com/jsonapi/node/games?filter[field_game_category.name]=Scratch&page[limit]=50&include=field_game_thumbnail`
  (use `curl -g`; 50 per page, follow `links.next`; second page exists. Includes expired games -> filter on `field_expiration_date` >= today or `field_final_claim_date`.)

**2. Format:** JSON (JSON:API) and server-rendered HTML. No bot wall.

**3. Fields (JSON:API `node--games` attributes):**
`title, field_game_id (e.g. "1874"), field_price ("20.00"), field_odds ("1:3.28"), field_percent_sold ("0.7849..."), field_top_prize_value, field_entry_date, field_expiration_date, field_final_claim_date, field_full_odds_and_prizes, field_how_to_play, field_rules_and_odds, path.alias`; relationships `field_game_thumbnail` (-> `file--file` with `attributes.uri.url` = CloudFront JPG), `field_game_category`, `field_related_games`.
Prize table `field_full_odds_and_prizes.value` is a dict of rows keyed "0".."N": row "0" is the header `["Number of Prizes","Prize Amount","Remaining Prizes","Odds","Multiplier"]`; each data row is `{"weight":"1","0":"2","1":"200000","2":1,"3":"1:134365","4":""}` i.e. **[printed, amount, remaining, tier odds]**. All tiers present with printed counts; **caveat:** on some games the lowest tiers (< $25) have remaining `""` (site note: "Prizes below $25 are not available").
Tickets printed appears only on the HTML game page ("Tickets Printed: N"), not in JSON (but sum(printed)/odds recovers it).

**4. curl:** 200 everywhere (HTML 398 KB, JSON 158 KB/page). No Cloudflare/Akamai.

**5. Sample (JSON:API, one game, trimmed):**
```json
{"title":"$200,000 Money Monster Jackpot","field_game_id":"1874","field_price":"20.00","field_odds":"1:3.28",
 "field_percent_sold":"0.78494399583225","field_top_prize_value":"200000",
 "field_entry_date":"2025-08-07T18:00:00-06:00","field_expiration_date":"2026-05-12T10:49:00-06:00",
 "field_full_odds_and_prizes":{"value":{"0":{"0":"Number of Prizes","1":"Prize Amount","2":"Remaining Prizes","3":"Odds","4":"Multiplier"},
   "1":{"weight":"1","0":"2","1":"200000","2":1,"3":"1:134365","4":""},
   "4":{"weight":"4","0":"624","1":"500","2":153,"3":"1:431","4":""},
   "9":{"weight":"9","0":"48860","1":"20","2":"","3":"1:5","4":""}}}}
```
Included file: `{"uri":{"url":"http://d2kx0heugfrx3y.cloudfront.net/2025-06/1768_thumbnail.jpg?VersionId=..."}}`

**6. Effort: Easy** (JSON with all tiers, printed + remaining + per-tier odds, price, overall odds, game number, dates, image).

---

## Illinois (IL)

**1. Pages:** The official remaining-prizes page is `https://www.illinoislottery.com/about-the-games/unpaid-instant-games-prizes` (per web search: "unclaimed scratch off ticket prizes and the number of remaining prizes by the prize value of each game"). Instant games list: `https://www.illinoislottery.com/instant-games`.

**2. Format:** Unknown/unverifiable from this machine — see 4.

**3. Fields:** Could not inspect. (Third-party sites that mirror it show per-tier remaining, which suggests all tiers, but unverified.)

**4. curl:** **403 on every path**, including `/`, `/robots.txt`, `/sitemap.xml`, `/api/*`. Headers: `server: cloudflare`, `cf-mitigated: challenge`, `critical-ch: Sec-CH-UA...` -> Cloudflare Managed Challenge (JS/browser fingerprint). WebFetch also returns 403. `api.illinoislottery.com` does not resolve.
Open data: `data.illinois.gov` is Socrata; catalog search restricted to that domain (`/api/catalog/v1?domains=data.illinois.gov&q=lottery|instant|scratch`) returns 0 relevant datasets (only two IDVA grant datasets match "lottery"). No CKAN API (`/api/3/action/*` -> "No service found").

**5. Sample:** none obtainable (403 challenge page, 172 KB HTML).

**6. Effort: Blocked** (Cloudflare challenge; would need a real headless browser session, and this project is stdlib-only). No open-data alternative found.

---

## Indiana (IN)

**Site tech:** Kentico (`/getmedia/...` images), server-rendered.

**1. Pages**
- Stats table: `https://hoosierlottery.com/games/scratch-off/scratch-off-stats/` -> `table.grid-table`, 64 rows, **top prize only**. Columns: Game Name | Game Number | Top Prize | Unclaimed | Prize Total | Price | On Sale Date | Estimated Odds. (`?grid-page=` / `?grid-pagesize=` change nothing; all rows are in one page.)
- Listing: `https://hoosierlottery.com/games/scratch-off/` (521 KB) -> `div.cardContainer[data-count="63"]` with `a.game` cards: `data-id="2634" data-name="WILD CHERRY" data-price="5" data-prize="100000" data-play-type="Number Match" data-second-chance="false"`, text "Est. Overall Odds: 1 in 3.85", image `/getmedia/<guid>/2634-Wild-Cherry_cropped.png`, href `/games/scratch-off/wild-cherry`.
- Per-game (all tiers): `https://hoosierlottery.com/games/scratch-off/wild-cherry/` -> `table.prize-table` **Prize Amount | Unclaimed | Total Winning Tickets** for every tier, plus "Game #2634", "Top Prize: $100,000", "Estimated Overall Odds: 1 in 3.85", "Ticket Price: $5", "Sale Date: 9/1/2026", "Reorder Date: None".

**2. Format:** Server-rendered HTML; one request per game for full tiers. No JSON endpoint found (only Braze/recaptcha keys in page config).

**3. Fields:** All tiers with total + unclaimed (per-game page); price, overall odds, game number, on-sale date, image URL (listing). No per-tier odds, no tickets-printed (derivable: sum(total winners) x overall odds).

**4. curl:** 200 (no bot wall). Note `/games/scratch-offs/` (plural) 301s to nowhere useful; use `/games/scratch-off/`.

**5. Sample (per-game page):**
```html
<table class="table table-sm-responsive table-striped prize-table"><thead><tr class="prize-headers">
<th>Prize Amount</th><th>Unclaimed</th><th>Total Winning Tickets</th></tr></thead><tbody>
<tr><td><span class="font-weight-bold">$100,000</span></td><td>3</td><td>3</td></tr>
<tr><td><span class="font-weight-bold">$5,000</span></td><td>32</td><td>35</td></tr>
<tr><td><span class="font-weight-bold">$100</span></td><td>14,333</td><td>15,884</td></tr>
```
Stats row: `<td data-name="Name">PREMIUM PLAY</td><td data-name="InstantGameId">2441</td><td data-name="TopPrize">$250,000</td><td data-name="Unclaimed">1</td><td data-name="PrizeTotal">3</td><td data-name="PricePoint">$10</td><td data-name="ConsumerSalesStartDate">01/04/2022</td><td data-name="Odds">1 in 3.81</td>`

**6. Effort: Medium** (1 listing + ~63 per-game HTML pages; all tiers with totals).

---

## Iowa (IA)

**Site tech:** ASP.NET WebForms (`__doPostBack` nav, but the real pages are plain GET-able .aspx).

**1. Pages**
- Remaining prizes (all games, one page): `https://ialottery.com/Pages/Games/RemainingPrizes.aspx` (409 KB) -> `table#RemainPrizes_JS_DATATABLE`, 518 rows / 104 games (72 Scratch, 24 InstaPlay, 8 PullTab). Columns: **Game Name (Game Number) | Game Type | Cost | Prize | Claimed | Unclaimed**. Total per tier = Claimed + Unclaimed. **Only tiers >= $50 are listed** (min listed prize is $50 for 75 of 104 games, $60-$100 for the rest).
- Listing: `https://ialottery.com/Pages/Games-Scratch/ScratchGamesListing.aspx` -> links `ScratchGamesDetail.aspx?g=819`.
- Per-game: `https://ialottery.com/Pages/Games-Scratch/ScratchGamesDetail.aspx?g=819` -> `table#Prizes` (Prize | Odds, e.g. "$30 | 1 in 5.00", every tier) + "Overall Odds 1 in 2.28" + `table#Dates` (Game Start, End Distribution, Official Game End, Last Day To Redeem Prizes) + game image.
- Open data: `data.iowa.gov` Socrata catalog search for "lottery" returns nothing relevant.

**2. Format:** Server-rendered HTML tables. No JSON.

**3. Fields:** Price, game number, game type; claimed/unclaimed for tiers >= $50 only; per-tier odds + overall odds + dates on the per-game page. No tickets-printed figure (so low-tier counts cannot be reconstructed exactly; you can estimate total tickets from a >= $50 tier: total_tier / (1/odds_tier)).

**4. curl:** 200, no bot wall. (`/Games/ScratchGames` guessed path is a 404 — use the `/Pages/...aspx` URLs.)

**5. Sample (RemainingPrizes.aspx):**
```html
<tr><td class="col2" style="text-align: left;">$100,000 CASH BONUS (797)</td><td class="col2">Scratch </td>
<td class="col2" style="text-align: center;">10</td><td class="col2" style="text-align: right;">$100000</td>
<td class="col2" style="text-align: right;">1</td><td class="col2" style="text-align: right;">8</td></tr>
```
Per-game odds row: `<tr class=""><td ...>$30</td><td ...> 1 in 5.00</td></tr>` ... `Overall Odds 1 in 2.28`.

**6. Effort: Medium** (one HTML table for claimed/unclaimed, but **partial tiers** (>= $50); plus one page per game for odds/dates).

---

## Kansas (KS)

**Site tech:** kslottery.com now redirects to `playonkansas.com` (Next.js App Router, MUI, Contentful images). kslottery.gov is a small regulatory site that links to playonkansas.

**1. Pages**
- Listing: `https://playonkansas.com/games/scratch-and-pull-tabs` (258 KB). Game list is embedded in the RSC payload (`self.__next_f.push([1,"..."])` strings) as `"scratchOffs":[...]` — 109 records (6 are `pullTab:true`), prices 1-50.
- Per-game (server-rendered, includes prize table): `https://playonkansas.com/games/scratch-and-pull-tabs/rivalry-riches-490` -> text "Top Prize $25,000 | Price $5 | Overall Odds 1 in 3.35 | Game Number 490 | Launch Date Aug 23, 2026 | Expiration Date TBD" and a "Prizes Remaining" MUI table (**Prize | Remaining**) for every tier incl. "FREE TICKET" ("The remaining prize quantity updates once every hour").
- `/games/instants` is e-Instants (online) only — ignore.
- APIs: bundle config `NEXT_PUBLIC_KSL_API_URL=https://kslapi.kslottery.com/api` (server-side only; every guessed path 404s) and `NEXT_PUBLIC_PLAYON_BASE_URL=https://gateway-web.loyalty.playonkansas.com/services` (the JS `GamesService` calls `game/api/game/{id}/prizes/unclaimed`, `game/api/published-games?gameTypeId.in=...` there, but those serve e-instant/draw games: 401 for v1/v2, "Game not found" for id 490, empty content for published-games). No public scratch JSON found.

**2. Format:** JS-app but **server-rendered** — the listing JSON is in the HTML and the per-game prize table is in the HTML, so plain curl + regex/HTMLParser works. No bot wall.

**3. Fields:** Listing JSON: `gameId, gameNumber, topPrize, slug, title, imageAltText, order, ticketPrice, pullTab, startDate, endDate, claimEndDate, image.url, appImage.url`. Per-game: price, overall odds, game number, launch/expiration date, all-tier **remaining** counts. **No printed totals and no per-tier odds** (only overall odds).

**4. curl:** 200 (listing 258 KB, game page 184 KB).

**5. Sample:**
Listing record (after unescaping `\"`): 
```json
{"gameId":490,"gameNumber":"490","topPrize":25000,"slug":"rivalry-riches-490","title":"Rivalry Riches","ticketPrice":5,"pullTab":false,
 "startDate":"2026-08-24T00:00:00.000-05:00","endDate":null,"claimEndDate":null,
 "image":{"url":"https://images.ctfassets.net/9rr74jcm47fc/.../RivalryRichesC_490__1_.jpg"}}
```
Per-game table cells (each value duplicated in a visually-hidden span + aria-hidden span):
`<td ...><span style="position:absolute;clip:rect(0 0 0 0)">FREE TICKET</span><span aria-hidden="true">FREE TICKET</span></td><td ...><span ...>35,852</span><span aria-hidden="true">35,852</span></td>`
Text form: `Prize Remaining $25,000 4 $500 73 $100 513 $50 6,345 $25 5,764 $15 14,386 $10 28,841 $5 41,900 FREE TICKET 35,852`

**6. Effort: Medium** (1 listing + ~109 per-game pages; remaining-only counts, no printed totals).

---

## Kentucky (KY)

**Site tech:** OpenCms (`/apps/...`, `/export/kylmod/...`), jQuery. Draw-game data comes from an IGT API (`https://kys-v2.p1.awc.lotteryservices.net/api/v2/draw-games/draws` with an `X-Esa-Api-Key` header embedded in the page) but scratch data is **server-rendered** HTML.

**1. Pages**
- All prizes remaining, one page: `https://www.kylottery.com/apps/scratch_offs/prizes_remaining.html` (834 KB, 107 games incl. ended-but-claimable). Each game is a Bootstrap accordion: heading `"$1,000,000 Luck - 848"` (name - game number), body: "Game End Date / Last Date to Purchase: TBD", "Last Claim Date: TBD", "Prizes Remaining as of 09/11/2026", and `table.il24-table-custom` **Prize Amount | Prizes Remaining** for every tier (down to the lowest, e.g. $15).
- Current games with metadata: `https://www.kylottery.com/apps/scratch_offs/available_games.html` (786 KB, 81 games): same accordion plus image `/export/kylmod/galleries/images/KYLottery_ScratchOffs/KY848CV-V7.jpg`, "Start Date: March 30, 2023", "Value: $20", "Top Prize: $1,000,000", "Overall Odds: 1:3.57", "Game #: 848", and the same prizes-remaining table. This one page has everything a scraper needs.
- Per-game: `https://www.kylottery.com/apps/scratch_offs/games/$200000WildCherries_158` (URLs are listed in the page's `availableGamesDtl.push("/apps/scratch_offs/games/...")` script array) — same fields.
- `/apps/scratch_off_games/` (guessed) is a 404 -> use `scratch_offs`.

**2. Format:** Server-rendered HTML (large single pages). No JSON.

**3. Fields:** Price, top prize, overall odds, game number, start/end/claim dates, image, and **remaining counts for all tiers**. **No printed totals, no per-tier odds.**

**4. curl:** 200, no bot wall.

**5. Sample (available_games.html):**
```html
<h4 class="panel-title">... $1,000,000 Luck - 848</h4> ...
<span>Start Date:&nbsp;</span><b>March 30, 2023</b><br /> <span>Value:&nbsp;</span><b>$20</b><br />
<span>Top Prize:&nbsp;</span><b>$1,000,000**</b><br /> <span>Overall Odds:&nbsp;</span><b>1:3.57</b><br /> <span>Game #:&nbsp;</span><b>848</b><br />
<span>Prizes Remaining as of <b>09/11/2026</b>...
<tr><td style="text-align: center;" title="Prize Amount">$862,000</td><td style="text-align:center;" title="Prizes Remaining"> 1</td></tr>
<tr><td ... title="Prize Amount">$10,000</td><td ... title="Prizes Remaining"> 8</td></tr>
```

**6. Effort: Medium** (single HTML page, all tiers, but remaining-only; no printed totals).

---

## Louisiana (LA)

**Site tech:** WordPress (custom theme `la-lotto`, web components), behind Cloudflare but **no challenge** for curl (one 30 s fetch timed out once; use `--max-time 60`).

**1. Pages**
- Summary JSON embedded in HTML: `https://louisianalottery.com/top-prizes-remaining/` -> `<prize-table><script type="application/json">{"columns":[...],"data":[...]}</script>` with **37 current scratch-off games**: `image, game{name,link}, number, remaining ("1 of 6"), top_prize, price, percent_claimed, start_date`.
- Per-game (all tiers): `https://louisianalottery.com/game/1605-louisiana-seasons/` -> `table.table` **Tier Prize | Odds of Winning | Total | Claimed | Remaining** for every tier (including free "TICKET"), plus "Game No. 1605", "$10 Ticket Price", "$200,000 Top Prize", "1 in 3.24 Overall Odds", "Launch Date", "Top Prizes remaining: 0 of 4", "Approximate Percent Claimed: 79%", "Close Date", "Final Redemption Date", front/back/scratched images, "Last Updated: 09/12/2026 10:06:23 PM CDT".
- Listing `https://louisianalottery.com/scratch-offs/` has 38 `/game/<num>-<slug>/` links (server-rendered, client-side `game-filter`).
- WP REST (metadata only, no prizes): `https://louisianalottery.com/wp-json/wp/v2/instant-game?per_page=100&game-type=133` (217 total posts; taxonomy `game-type` 133 = "Scratch Offs" (176 incl. expired), 132 = Fast Play; `price-point` taxonomy). `acf` is empty. Theme JS only exposes `/wp-json/la-lotto/v1/retailers` and `/playslip-stats`.

**2. Format:** JSON blob in HTML (summary) + server-rendered HTML tables (per game).

**3. Fields:** All tiers with total, claimed, remaining and per-tier odds; price; overall odds; game number; launch/close/redemption dates; percent claimed; image URLs. (Fast Play games use the same template with "Total Winners / Total Won" instead — filter by URL from the top-prizes JSON.)

**4. curl:** 200.

**5. Sample:**
```json
{"image":"https://louisianalottery.com/wp-content/uploads/2025/08/1640C.png","game":{"name":"100x The Cash","link":"https://louisianalottery.com/game/1640-100x-the-cash/"},
 "number":"1640","remaining":"1 of 6","top_prize":"500000","price":"20","percent_claimed":"97","start_date":"09/22/2025"}
```
```html
<thead><tr><th>Tier Prize</th><th>Odds of Winning</th><th>Total</th><th>Claimed</th><th>Remaining</th></tr></thead>
<tr><td>$200,000</td><td>1 in 420,631.25</td><td>4</td><td>4</td><td>0</td></tr>
<tr><td>$10,000</td><td>1 in 112,168.33</td><td>15</td><td>12</td><td>3</td></tr>
```

**6. Effort: Easy/Medium** (1 embedded-JSON listing + ~37 per-game HTML tables; all tiers with totals and odds).

---

## Maine (ME)

**Site tech:** Static HTML (Maine.gov InforME template).

**1. Pages**
- `https://www.mainelottery.com/players_info/unclaimed_prizes.html` -> `table.tbstriped` **Price Point | Game No. | Game Name | Percent Unsold | Total Unclaimed ($) | Top Prize Level(s) | Top Prize(s) Unclaimed** — "list of top unclaimed prizes ... as of September 12, 2026 5:00 AM". **Top 1-2 tiers only**; extra tiers appear as continuation rows with blank first five cells.
- `https://www.mainelottery.com/instant/scratchdates.html` -> Game Number | Game Name | Game End | Last Cash Date.
- Price-point pages `https://www.mainelottery.com/instant/scratch1dollar.html` ... `scratch30dollar.html` link each game to a maine.gov article: `https://www.maine.gov/tools/whatsnew/index.php?topic=Lottery_Scratch&id=13350811&v=article` -> "GRAB A GRAND, Maximum Award: $1,000, Game #730, HIGHEST INSTANT PRIZE ODDS 1:80,000, OVERALL ODDS 1:4.43, On Sale - June 4, 2026, Tickets Printed 960,000" + image `attach.php?id=...&an=1`. **No prize-tier table anywhere.**

**2. Format:** Server-rendered HTML tables. No JSON/CSV/PDF.

**3. Fields:** Price, game number, percent unsold, total unclaimed dollars, top-prize level(s) and unclaimed count; overall odds + tickets printed on the article page. No per-tier structure.

**4. curl:** 200, no bot wall.

**5. Sample:**
```html
<tr><th>Price Point</th><th>Game No.</th><th>Game Name</th><th>Percent Unsold</th><th>Total Unclaimed</th><th>Top Prize Level(s)</th><th>Top Prize(s) Unclaimed</th></tr>
<tr><td>$2.00</td><td>624</td><td>CASH BLAST</td><td>0.3</td><td>$79,953.00</td><td>$10000</td><td>2 </td></tr>
<tr><td> </td><td> </td><td> </td><td> </td><td> </td><td>$1000</td><td>1 </td></tr>
```

**6. Effort: Blocked** (top-prize-only data; easy to parse but insufficient for full-tier EV). "Total Unclaimed $" + percent unsold could support a crude EV if desired.

---

## Maryland (MD)

**Site tech:** WordPress (theme `mdlottery`), custom post type `scratch-off`; the game list is loaded by `scratch-offs.js` via admin-ajax.

**1. Pages**
- **Single request with everything:** `POST https://www.mdlottery.com/wp-admin/admin-ajax.php` with form fields `action=jquery_shortcode`, `shortcode=scratch_offs`, `atts={"null":"null"}` -> 313 KB HTML fragment with 91 `li.ticket#ticket_<n>` blocks. Each has `.price`, `.name`, `strong.topprize`, `strong.topremaining`, `strong.chancestowin`, `strong.launchdate`, `span.probability` ("1 in 3.05"), `strong.gamenumber` ("Game #815"), front/back/scratched image links, and `div.prize-details#prize_details_<n>` with a table **Prize Amount | Start | Remaining*** for every tier, "Records Last Updated: 09/11/2026", hidden `div.allremaining`.
- Per-game page (same table): `https://www.mdlottery.com/scratch-off/100000-crossword-815/` (game number is the slug suffix).
- Public page `https://www.mdlottery.com/games/scratch-offs/` only has a 4-slide carousel server-side; the finder list is AJAX.
- WP REST (metadata only): `https://www.mdlottery.com/wp-json/wp/v2/scratch-off?per_page=100` -> 91 items (`id, slug, link, title, scratch-category` [Holiday/Bingo/Crossword/Second Chance/Featured]); `acf` empty, no prize data.

**2. Format:** HTML fragment via admin-ajax (one POST) or per-game HTML. No JSON with prizes.

**3. Fields:** All tiers with **Start (printed) and Remaining**; price; overall odds ("Probability of Winning 1 in X"); game number; launch date; top prize + top prizes remaining; image URLs. No per-tier odds, no tickets printed (derivable: sum(Start) x probability).

**4. curl:** 200 for the page, the admin-ajax POST, REST, and per-game pages. No bot wall.

**5. Sample (admin-ajax response):**
```html
<li class="ticket" id="ticket_815"><div class="header"><div class="price">$10</div><div class="name">$100,000 Crossword</div>...
<ul class="primary"><li>Top Prize: <strong class="topprize">$100,000</strong></li><li>Top Prizes Remaining: <strong class="topremaining">9</strong></li>
<li>Game Start: <strong class="launchdate">08/21/2026</strong></li><li>Probability of Winning: <strong>1 in <span class="probability">3.05</span></strong></li></ul>
<ul class="secondary"><li><strong class="gamenumber">Game #815</strong></li>...
<div class="mfp-hide white-popup prize-details" id="prize_details_815"><table><thead><tr><th>Prize Amount</th><th>Start</th><th>Remaining*</th></tr></thead>
<tbody><tr><td>$100,000</td><td>9</td><td>9</td></tr><tr><td>$1,000</td><td>22</td><td>20</td></tr><tr><td>$10</td><td>508517</td><td>466168</td></tr></tbody></table>
<p><strong>Records Last Updated:</strong> 09/11/2026</p>
```

**6. Effort: Easy/Medium** (one HTML POST returns all 91 games with all tiers, printed + remaining).

---

## Summary

| State | Format | All tiers? | Price | Odds | Bot block | Effort | Main URL |
|---|---|---|---|---|---|---|---|
| ID | JSON:API (Drupal) + SSR HTML | Yes (printed + remaining + tier odds; <$25 tiers sometimes blank remaining) | Yes | Overall + per-tier | None | **Easy** | `https://www.idaholottery.com/jsonapi/node/games?filter[field_game_category.name]=Scratch&page[limit]=50&include=field_game_thumbnail` |
| IL | Unknown (Cloudflare challenge) | Unknown | - | - | **Cloudflare managed challenge (403 on all paths, WebFetch too)** | **Blocked** | `https://www.illinoislottery.com/about-the-games/unpaid-instant-games-prizes` |
| IN | SSR HTML (Kentico) | Yes on per-game pages (Unclaimed + Total Winning Tickets); stats table = top prize only | Yes | Overall only | None | **Medium** (~63 game pages) | `https://hoosierlottery.com/games/scratch-off/` + `/games/scratch-off/<slug>/` (+ `/games/scratch-off/scratch-off-stats/`) |
| IA | SSR HTML (ASP.NET) | Partial: tiers >= $50 (Claimed + Unclaimed); per-tier odds on game pages | Yes | Overall + per-tier | None | **Medium** (partial tiers) | `https://ialottery.com/Pages/Games/RemainingPrizes.aspx` + `.../Games-Scratch/ScratchGamesDetail.aspx?g=N` |
| KS | Next.js SSR: JSON blob in HTML + HTML table | Remaining only (all tiers incl. free ticket; no printed totals) | Yes | Overall only | None | **Medium** (~109 game pages) | `https://playonkansas.com/games/scratch-and-pull-tabs` + `/games/scratch-and-pull-tabs/<slug>` |
| KY | SSR HTML (OpenCms), one big page | Remaining only (all tiers; no printed totals) | Yes | Overall only | None | **Medium** (single 786 KB page) | `https://www.kylottery.com/apps/scratch_offs/available_games.html` (+ `prizes_remaining.html`) |
| LA | JSON blob in HTML + SSR HTML tables (WordPress) | Yes (Total + Claimed + Remaining + tier odds) | Yes | Overall + per-tier | Cloudflare present, no challenge | **Easy/Medium** (~37 game pages) | `https://louisianalottery.com/top-prizes-remaining/` + `https://louisianalottery.com/game/<num>-<slug>/` |
| ME | Static HTML | Top prize(s) only | Yes | Overall (article page) | None | **Blocked** (top-prize-only data) | `https://www.mainelottery.com/players_info/unclaimed_prizes.html` |
| MD | HTML fragment via admin-ajax POST (WordPress) | Yes (Start + Remaining for all tiers) | Yes | Overall only | None | **Easy/Medium** (one POST) | `POST https://www.mdlottery.com/wp-admin/admin-ajax.php` (`action=jquery_shortcode&shortcode=scratch_offs&atts={"null":"null"}`) |

Notes for implementation:
- Idaho JSON:API needs `curl -g` / no URL globbing; the site returns expired games too, so filter by `field_expiration_date`.
- Kansas, Kentucky: no printed totals anywhere, so EV needs an external assumption (e.g. tickets printed from overall odds is not enough without per-tier odds). Only "remaining prizes per tier" is available.
- Iowa: printed totals for >= $50 tiers are `Claimed + Unclaimed`; low tiers only have odds.
- Louisiana per-game pages take ~1-2 s each; use a 60 s timeout.
- Illinois: no workaround found without a real browser; the sites data.illinois.gov (Socrata) has no lottery instant-game dataset.
