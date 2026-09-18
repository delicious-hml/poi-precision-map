# 🗺️ POI Precision Map

> Turn *"find every X in region Y and pin them on a map, one by one"* into a **verified, point-by-point interactive HTML map** — no API keys, no proxy, no runtime geocoding. One standalone file you can keep, share, and open in any browser.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Map engine](https://img.shields.io/badge/map%20engine-Leaflet%201.9-199900.svg)](https://leafletjs.com/)
[![API key](https://img.shields.io/badge/API%20keys-none%20required-success.svg)](#why-no-keys)
[![Coordinates](https://img.shields.io/badge/coordinates-GCJ--02%20discipline-red.svg)](#coordinate-system-rule)

**[中文说明](README.zh-CN.md)** · [Live example map](examples/shenzhen-universities.html) · [Skill spec (SKILL.md)](SKILL.md)

---

## What it is

An **Agent Skill** (drop-in `SKILL.md` + templates, compatible with Claude Code, TRAE, WorkBuddy and any agent that supports the Agent Skills convention) that turns a natural-language mapping request into a real deliverable:

> *"标出深圳所有的大学，一家家精确到地址"* → a single self-contained HTML file with every university individually geocoded, numbered, labeled with confidence and source, cross-verified, and validated by script before delivery.

The demo map below was generated with this skill — download and open it locally, it just works:

| | |
|---|---|
| **Input** | "map all universities in Shenzhen, one by one" |
| **Output** | [`examples/shenzhen-universities.html`](examples/shenzhen-universities.html) — 13 numbered pins across 4 categories, each with address, GCJ-02 coordinates, status, confidence and source; searchable side list, CSV export, `file://`-portable. Two more universities exist in Shenzhen but were **excluded and reported in the delivery note** (one under construction with no fixed campus site, one no longer enrolling) — that's the skill's no-invented-data rule in action. |

## Why it exists (the failure mode)

Most AI-generated maps die outside the chat window. A typical run hand-writes a Tencent Maps SDK page with `serviceHost: 'http://127.0.0.1:…'` and calls `geocoder.getLocation()` **at runtime**. Inside the host app, a local proxy makes it work. Open the file anywhere else → every geocode is rejected → **zero markers, blank map**.

This skill makes that failure mode structurally impossible:

1. **All coordinates are resolved at generation time** and baked into the HTML as a static JSON block.
2. **Leaflet + public Amap raster tiles** — no SDK, no key, no proxy, no account.
3. The deliverable must run on `file://`, and the bundled [validator](references/validate.py) mechanically enforces it.

## Features

- **Point-by-point precision** — every place geocoded from its actual street address, never district-center approximations or aggregated bubbles
- **Keyless & portable** — a single HTML file; double-click and it opens, forever, in any browser
- **Data you can trust**
  - per-place `conf` (高/中/低) confidence and `src` source labels
  - cross-verification rules baked into the skill (official registries preferred; non-official sources verified across ≥2 independent channels)
  - `asof` capture date in the header, so you know how fresh the data is
- **Reproducible Top-N** — "top 30" requires a stated ranking metric (`META.rankedBy`) and category boundary (`META.catDef`); both render in the header, so two runs with the same spec produce the same list
- **Coordinate-system discipline (GCJ-02)** — Amap/Tencent coords used directly; WGS-84 and BD-09 sources converted first; never mixed
- **No invented data** — places that can't be precisely located are excluded from markers and listed in the delivery note, never guessed
- **Script-validated output** — entry count, ID continuity, duplicate detection (chain-aware), popup completeness, banned patterns (native dialogs, vendor SDKs, runtime geocoders, proxy markers)
- **Practical UI** — numbered pins, rich popups, searchable side list with click-to-fly, fit-all, one-click CSV export, multi-category legend, responsive mobile layout, UI in your conversation language

## Install

Copy this folder into your agent's skills directory:

```bash
# Claude Code
git clone https://github.com/delicious-hml/poi-precision-map.git \
  ~/.claude/skills/poi-precision-map

# TRAE / WorkBuddy — place under your agent skills dir, e.g.
# C:\Users\<you>\.workbuddy\skills\poi-precision-map
```

The skill is picked up automatically. No build step, no dependencies — just `SKILL.md`, the HTML template, the prompt template, and a Python validator.

## Usage

Ask your agent for any *"places of category X in region Y, pinned one by one"* task:

- 「标出深圳南山区所有的三甲医院，一家家精确到地址」
- "Map every EV charging station in Pudong, New Area — point by point"
- 「深圳市前 30 大消费电子企业分布图」（the skill will ask for the ranking metric before generating)
- "画出广东省所有 5A 景区的分布图"

Or use the fill-in-the-blank [prompt template](references/prompt_template.md) to launch a batch.

## How it works

```
you: "map all X in Y, one by one"
      │
      ▼
[1] confirm region / category / N / ranking metric / category boundary
      │
      ▼
[2] research — authoritative sources per category
    (registries, official sites), cross-verified
      │
      ▼
[3] per-place geocoding to GCJ-02, actual address → lat/lng
    (unlocatable points: excluded & reported, never guessed)
      │
      ▼
[4] inject dataset into the frozen HTML template
    (JSON block only — structure never rewritten)
      │
      ▼
[5] validate.py — count / IDs / coords / duplicates /
    popup placeholders / banned patterns / META completeness
      │
      ▼
[6] visual check → deliver a single standalone HTML file
```

## Data model

Each place is a JSON object injected into the template's `<script id="places-data">` block:

```json
{
  "id": 1,
  "name": "南方科技大学",
  "cat": "本地高校",
  "addr": "广东省深圳市南山区学苑大道1088号",
  "lat": 22.595xxx,
  "lng": 113.974xxx,
  "conf": "高",
  "status": "办学中",
  "desc": "2011年创办的新型研究型大学",
  "src": "官网"
}
```

`id`/`name`/`cat`/`addr`/`lat`/`lng`/`conf` are required; `desc`/`status`/`src` optional. `META.asof` (capture date), `META.rankedBy` (ranking metric) and `META.catDef` (inclusion rule) render in the map header.

## Coordinate system rule (hard)

The base map uses Amap tiles → **everything plotted must be GCJ-02** ("Mars coordinates"):

| Source | System | Action |
|---|---|---|
| Amap / Tencent geocoding | GCJ-02 | use directly |
| Baidu | BD-09 | convert → GCJ-02 |
| Nominatim / OSM / raw GPS | WGS-84 | convert → GCJ-02 |

Mixing systems shifts every pin by **hundreds of meters** while still passing naive numeric validation — the map "looks fine" but everything is in the wrong place. This is the #1 silent killer of AI-generated China maps, and the skill treats it as non-negotiable.

## Repository structure

```
poi-precision-map/
├── SKILL.md                      # the skill: rules, workflow, pitfalls
├── README.md                     # you are here
├── README.zh-CN.md               # 中文说明
├── LICENSE                       # MIT
├── references/
│   ├── map_template.html         # frozen HTML template (Leaflet + Amap tiles)
│   ├── prompt_template.md        # fill-in-the-blank launch prompt
│   └── validate.py               # post-generation validator
└── examples/
    └── shenzhen-universities.html  # demo: all universities in Shenzhen
```

## Limitations & caveats

- Tile endpoint is Amap's public raster service and Leaflet loads from unpkg CDN — the map needs internet for tiles, though no keys or accounts
- Verification quality is bounded by search; the skill compensates with mandatory cross-verification and visible confidence labels rather than false certainty
- Not for district-level aggregate/bubble maps — it is deliberately a point-by-point tool

## License

[MIT](LICENSE) © 2026 delicious-hml
