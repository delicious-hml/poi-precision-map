---
name: poi-precision-map
description: Generate a standalone, file://-portable HTML map (Leaflet + Amap public tiles, no key, no proxy, no runtime geocoding) that plots every place of a given category in a region point-by-point. Use when users ask to find places of a certain category in a region and pin them one by one (e.g. "find all X in Y and pin them on a map", "某区所有的XX一家家标地图", "画出分布图"). Delivers a real runnable HTML file the user can keep, share, and open in any browser — overrides the geo-map-compliance-guard default Tencent-proxy scenario for portable-file tasks. Emphasizes precise per-place geocoding (pre-baked GCJ-02 coordinates), cross-verified sources, rigorous counting with no omissions and no redundancy. Does NOT do range/area aggregation or in-region/out-of-region splitting.
agent_created: true
---

# POI Precision Map

## Purpose
Turn a "find all places of category X in region Y and map them" request into a verified, point-by-point interactive map where every place is individually geocoded by its actual address, with category, confidence and source labels. Do the core job perfectly — no extra in-region/out-of-region splitting, no scope creep.

## When to Use
- User asks to find places of a certain category within a region and plot them **point-by-point** on a map.
- Trigger phrases / examples: find all X in Y and pin them on a map / 某区所有的XX、打点、标地图、画分布图、精确到门牌/坐标、一家家标、不要范围/气泡聚合、比例严谨、反复验证、无遗漏无冗余。
- Categories include but are not limited to: companies, schools/universities, hospitals/clinics, charging stations, parks, scenic spots, restaurants/hotels, government offices, chain stores, venues, etc.
- Do NOT use for: plain text lists, or requests that accept district-level aggregated bubble maps.

## Step 0 — UI Language
Default to the conversation language for ALL visible UI text (title, buttons, labels, popups, legend, notes). Only ask (AskUserQuestion) when the user explicitly requests a different language or the conversation language is genuinely ambiguous. Do not interrupt the flow just to confirm.

## Parameters to Confirm
- region: e.g. Shenzhen Nanshan District / 深圳市南山区
- category: e.g. consumer electronics companies / tertiary hospitals / EV charging stations / parks
- total N (optional): e.g. top 50 / all
- ranking metric (REQUIRED when N is a "top N"): 规模 / 成立时间 / 搜索热度 / 官方名录顺序. If the user did not specify, ASK before generating.
- category boundary (REQUIRED to state): the inclusion/exclusion rule for fuzzy categories (e.g. "嵌入式企业" = 含 MCU/工控/汽车电子/IoT，不含纯软件外包). State it in the deliverable.
- segment (optional): batching parameter, see Batch Strategy below
- output: point-by-point precision interactive map + numbered list

## Data Model (fixed — template and validator both depend on it)
Each place is a JSON object:
- `id` (int, required): continuous from 1, no gaps, no duplicates
- `name` (string, required)
- `cat` (string, required): category label; empty string allowed for single-category maps
- `addr` (string, required): actual street address down to door number
- `lat`, `lng` (number, required): **GCJ-02 coordinates** (see Coordinate System Rule)
- `conf` (string, required): closed set — `高` / `中` / `低` (or `High` / `Medium` / `Low` for non-Chinese UI). `低`/`Low` means uncertain and renders as a warning. An optional `⚠` prefix flags "suspect data" explicitly.
- `status` (string, optional): operating status, e.g. `营业中` / `已关闭` / `在建` (or `Open` / `Closed` / `Planned`). Fill it whenever the category has meaningful status drift (businesses, clinics, stations).
- `desc` (string, optional): one-line plain-text intro shown in the popup below the title and in the side list below the address. Keep it to one sentence (~30-60 chars) — this is a quick "who/what is this" blurb, not an essay. Examples: "深圳本土消费电子品牌，2004 年成立" / "三甲综合医院，开放床位 1500 张". Omit the field rather than leaving it empty if you have no verified blurb.
- `src` (string, optional): short source label, e.g. `卫健委名录` / `企业公示系统` / `官网`.

The dataset also carries an `asof` date (data capture date, YYYY-MM-DD) shown in the map header.

## Coordinate System Rule (hard, non-negotiable)
- The base map uses Amap tiles, which are **GCJ-02 ("Mars coordinates")**. ALL plotted coordinates MUST be GCJ-02.
- Tencent Maps and Amap geocoding results are GCJ-02 — safe to use directly. Baidu results are BD-09 — must be converted to GCJ-02 first.
- WGS-84 sources (Nominatim, raw GPS, OSM, most non-China APIs) MUST be converted to GCJ-02 before plotting. Mixing systems shifts every point by hundreds of meters and passes numeric coordinate validation silently — the map "looks fine" but everything is in the wrong place.
- Never mix coordinate systems within one dataset.

## Per-Category Authoritative Sources (select by category)
- Companies: business registration (national enterprise credit info system) / exchange annual reports & charters / company official sites
- Schools/universities: education authority directories / school official sites
- Hospitals/clinics: health commission directories / hospital official sites
- Charging stations: operator official sites (Teld / Star Charge / State Grid) / Amap POI
- Parks/scenic spots/venues: culture & tourism authority directories / official lists
- Restaurants/hotels/retail/chains: platform POI (Dianping / Amap / Meituan) — these need even stricter cross-verification and operating-status check
- General: WebSearch + ≥2 independent sources

## Cross-Verification Rule (mandatory, hardcoded)
When searching for information, if the source is a non-official notice or analysis (not an official bulletin / registry / government release), repeatedly cross-verify its authenticity and timeliness across multiple independent sources. Do NOT trust a single non-official source. No omissions, no redundancy. This rule overrides any convenience shortcut.

## Batch Strategy (for N > 50)
- Verifying + geocoding each point costs real search calls. When N > 50, split the work into batches of ≤ 50 points.
- `segment` = drop first M entries, keep next K (M + K = N). Use it to resume: batch 2 is `segment: M=50, K=50`, and so on.
- Accumulate batches into ONE dataset before generating the final map; run validate.py on the merged file. Never deliver per-batch partial maps unless the user explicitly asks.

## Top-N Selection & Ranking (hard rule — non-negotiable)
A "前N" / "top N" / "前30" result is ONLY meaningful when the **ranking metric** AND the **category boundary** are pinned. Two runs with different metrics or different boundaries produce different top-N lists — this is the #1 cause of "why don't the two maps match".
- **Ranking metric is mandatory for top-N.** Supported closed set: `规模` (registered capital / employees / revenue), `成立时间` (oldest first), `搜索热度` (search-result order), `官方名录顺序`. If the user did not specify one, **ASK (AskUserQuestion) before generating** — never guess. Guessing yields a non-reproducible, misleading list.
- **Category boundary must be stated.** Fuzzy categories (e.g. "嵌入式企业" spans embedded software / MCU / 工控 / 汽车电子 / IoT / firmware) need an explicit inclusion/exclusion rule written in the deliverable note.
- **Record both in the deliverable.** Set `META.rankedBy` and `META.catDef` in the HTML; they render in the header. Same query + same spec ⇒ same list. If you cannot make the selection deterministic, say so in the delivery note instead of shipping a silently different list.
- **"All X" (no N) is exempt** from the ranking requirement — list completeness matters, not order — but the category boundary still applies.

## Template Discipline (hard rules — non-negotiable)
1. **Do NOT rewrite the HTML structure.** Start from `references/map_template.html` and only replace (a) the UI strings object, (b) the `META.asof` date, (c) the contents of the `<script id="places-data" type="application/json">` block. Any feature gap (clustering, filters, custom styles) must be added as a clearly-marked extension block AFTER the existing script — never by deleting or rewriting the template's popup/list/legend logic. If you find yourself hand-writing a fresh HTML file, stop — you are doing it wrong.
2. **Popup field placeholders are frozen.** The popup template string in the template already references addr / coord / conf / status / src. Do not remove any of these references, even if a field is empty for some entries — empty fields render as blank lines, that is fine. Removing a placeholder = silently dropping a required field from the deliverable.
3. **No native browser dialogs.** The generated code MUST NOT contain `alert(`, `confirm(`, or `prompt(`. All user-facing messages (errors, "data not found", status notices) go through Leaflet popups, `bindPopup`, or in-panel DOM elements. Native dialogs break layout consistency and leak through to the host page.
4. **Standalone HTML — the deliverable must run on `file://`.** The generated HTML is opened directly in a browser, sometimes outside WorkBuddy. It MUST NOT depend on the WorkBuddy local proxy, on any `127.0.0.1` serviceHost, on `window._TMapSecurityConfig`, or on any other runtime secret injected by the host. If your code needs a key or a local port to function, it is broken by design.
5. **No browser-side geocoding.** Every `lat` / `lng` MUST be resolved at GENERATION time and written into the `places-data` JSON block. The generated HTML only renders static coordinates — it MUST NOT call `TMap.service.Geocoder`, `AMap.Geocoder`, `BMap.Geocoder`, `fetch(...geocoding api...)`, or any other runtime geocoder. Browser-side geocoding requires API keys / proxies and fails the moment the HTML leaves the host environment.
6. **Leaflet is the only map engine.** Do NOT use `new TMap.Map(`, `new AMap.Map(`, `new BMap.Map(`, `new google.maps.Map(`, or any vendor-specific map SDK. The template uses Leaflet.js + Amap raster tiles (public endpoint, no key). Sticking to Leaflet keeps the file keyless and offline-portable.

## Why these rules exist (real failure mode)
A previous run ignored the template and hand-wrote a TMap-based HTML with `window._TMapSecurityConfig = { serviceHost: 'http://127.0.0.1:__WB_HTTP_PORT__/...' }` plus `geocoder.getLocation()` calls at runtime. Inside WorkBuddy the proxy translated those calls; opened in an external browser, the proxy was unreachable → every geocode rejected → zero markers rendered. The user saw a blank map. The rules above exist to make this failure mode impossible: coordinates are baked in at generation time, no key, no proxy, no SDK lock-in.

## Workflow
1. **UI language** (Step 0 — default to conversation language). Resolve category + region; if ambiguous, ask. Determine the right authoritative source mix above. If N > 50, plan batches (Batch Strategy).
2. Search & compile a candidate list. Prefer official / open directories; supplement with web search. For "all of X" requests, verify each candidate's **current status** (fill the `status` field).
3. For each place, obtain the **actual address** down to street / door number, then geocode to GCJ-02 latitude / longitude.
   - If Nominatim / sandbox has no outbound network, use the "Tencent Maps reference" method: WebSearch the exact address; Tencent Maps returns `经纬度:(lat,lon)` — capture per point. Tencent output is GCJ-02, matching the base map.
4. **Geocoding failure rule**: if a point cannot be located precisely, do NOT guess coordinates. Default: exclude it from markers, but list it in the delivery note as "未能精确定位" with the reason. If the user wants such points kept, annotate them in the side panel only, never with invented coordinates.
5. Cross-verify non-official info per the Cross-Verification Rule; record the capture date as `asof`. Treat non-official notices as suspect by default.
6. Prevent same-building overlap: nudge coordinates of co-located places by a few meters and note the shared site in the popup.
7. Generate the interactive map (see `references/map_template.html`): Leaflet.js + Amap street tiles, data injected as a JSON block (`<script id="places-data" type="application/json">`), numbered markers, popup with id / name / category / **desc (one-line intro, if provided)** / address / coordinates / confidence / status / source, side panel list with click-to-fly, button to fit all. All UI strings in the user's language; header shows the `asof` date. **Follow Template Discipline above — do not rewrite the HTML.**
8. Validate with `references/validate.py` (`--expect N` to assert the total): entry count, ID continuity / uniqueness, coordinate validity, conf value set, duplicate coordinates, chain-aware duplicate detection, **popup placeholder presence** (addr / coord / conf / status / src all referenced), **native-dialog ban** (no `alert(` / `confirm(` / `prompt(`). Iterate until clean.
9. **Final visual check (mandatory)**: open the generated HTML in a browser and confirm with your own eyes — base tiles actually load, points land on the right streets, popups show all required fields. This is the last line of defense against coordinate-system mixups, dead tile endpoints, data-format bugs, and silent popup-field drops, none of which the validator can fully catch.

## Known Pitfalls (verified from real runs)
- **Address relocation/rename**: addresses from legacy lists may be stale. Always check the latest authoritative record, not legacy summaries.
- **HQ vs branch**: a place's HQ may sit elsewhere while a branch operates in the target region. Plot by the place's actual listed location.
- **Geocoding offline**: Nominatim fails in sandbox; use the Tencent Maps WebSearch method instead. (And remember: Nominatim output is WGS-84 — if it ever works, convert before plotting.)
- **Status drift**: for "all X" requests verify current operating status; exclude closed / unbuilt ones unless the user wants them annotated in `status`.
- **Category ambiguity**: "all X" can include franchises / sub-brands; confirm the inclusion rule with the user when ambiguous.
- **Top-N non-reproducibility**: "前30" with no stated ranking metric / category boundary produces a different list every run. Always pin both and record them in `META` — this is what makes two maps comparable.
- **Chain stores share names**: multiple branches of one brand are legitimate duplicates by name. Dedup by name+address, not name alone.
- **Tile/CDN fragility**: the Amap tile endpoint is an unofficial public endpoint and may throttle or die; Leaflet loads from the unpkg CDN and needs network. If the delivered map shows a blank background, check these two first — this is exactly what the final visual check is for.

## Self-Check Before Delivering
- [ ] N entries complete, matches the requested total (validate with `--expect N`), IDs continuous with no gaps, no duplicates
- [ ] for top-N tasks: `META.rankedBy` (ranking metric) and `META.catDef` (category boundary) are both set and render in the header; for "all X" the category boundary is still stated
- [ ] every entry has conf from the closed set + (where relevant) status + src
- [ ] all coordinates are GCJ-02; no WGS-84/BD-09 mixed in
- [ ] geocoding failures are excluded or annotated per the rule — zero invented coordinates
- [ ] script validation passes (count / uniqueness / coordinate validity / conf values / chain-aware dups)
- [ ] map opened in a browser: tiles load, points sit in the right places, popups complete, header shows asof, UI in the user's language
- [ ] no placeholder / demo entries — every entry is real verified data
- [ ] final deliverable is a real runnable HTML file written to the workspace, not a description or code block

## Reusable Prompt Template
See `references/prompt_template.md` for a fill-in-the-blank prompt to launch similar tasks.
