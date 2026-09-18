# Reusable Prompt Template · POI Precision Map

Fill the placeholders, then run. Full rules & pitfalls are in SKILL.md — this file is just the launch template to avoid duplicating them.

## Step 0 — UI Language
Default to the conversation language. Only ask if the user explicitly wants a different one.

## Template

```
【Task】 Retrieve "{category}" in "{region}" + point-by-point precision map

【Parameters】
- region: {e.g. Shenzhen Nanshan District}
- category: {e.g. consumer electronics companies / tertiary hospitals / EV charging stations}
- total: top {N} / all
- ranking metric (REQUIRED if top N): 规模 / 成立时间 / 搜索热度 / 官方名录顺序 — if the user didn't say, ASK before generating
- category boundary (REQUIRED to state): inclusion/exclusion rule for fuzzy categories (e.g. "嵌入式企业 = 含 MCU/工控/汽车电子/IoT，不含纯软件外包")
- segment (optional): batching for N > 50 — drop first {M}, keep next {K} (M+K=N), resume from where the last batch stopped
- UI language: {conversation language by default}

【Hard rules — see SKILL.md for full detail】
- Cross-verify every non-official source across ≥2 independent sources; no omissions, no redundancy.
- Pin each place by its actual address; ALL coordinates must be GCJ-02 (base map is Amap) — convert WGS-84 / BD-09 first.
- Data model: id / name / cat / addr / lat / lng / conf (closed set 高/中/低 or High/Medium/Low) + optional desc (one-line intro shown in popup) / status / src. Injected as a JSON block in the HTML; set META.asof to the capture date. For top-N set META.rankedBy (the metric) and META.catDef (the boundary) too — both render in the header so two runs stay comparable.
- Points that cannot be precisely geocoded: exclude from markers, list in delivery note — never invent coordinates.
- Template discipline: start from references/map_template.html, replace only UI strings + META.asof + the places-data JSON block. Do NOT rewrite the HTML structure. Do NOT remove popup placeholders (addr/coord/conf/status/src). Do NOT use alert()/confirm()/prompt() — all messages go through Leaflet popups or in-panel DOM.
- Standalone HTML: the deliverable must run on file:// — no WorkBuddy proxy, no _TMapSecurityConfig, no serviceHost. ALL coordinates pre-baked at generation time (no TMap.service.Geocoder / AMap.Geocoder / .getLocation at runtime). Leaflet is the only map engine — no TMap.Map / AMap.Map / BMap.Map / google.maps.Map.
- IDs continuous, no gaps/duplicates; validate with validate.py --expect {N} before delivering (--strict to catch dup coords / bad conf). Validator also checks popup placeholders, no native dialogs, no vendor SDK, no runtime geocoding, no proxy markers, and META.rankedBy / META.catDef declared.
- Final visual check: open the HTML, confirm tiles load, points land on the right streets, popups show all required fields.
- Output = real runnable HTML file in the workspace, UI in the chosen language, no placeholders/demos.
```
