#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POI Precision Map validator (v2).

Primary format: a JSON array inside
    <script id="places-data" type="application/json">[ ... ]</script>
Each entry: {id, name, cat, addr, lat, lng, conf} with optional {status, src}.
conf must be one of: 高 / 中 / 低 / High / Medium / Low (optional ⚠ prefix allowed).

Legacy fallback (auto-detected, for maps generated before v2):
  - {id, name, cat, addr, lat, lng, conf}              (object literals)
  - {id, name, cat, zone, addr, lat, lng, conf}        (zone ignored)
  - {id, name, zone, addr, lat, lng, conf}             (zone ignored, cat="")

Checks:
- total entry count, optional --expect N assertion
- ID uniqueness and continuity
- coordinate validity (numeric range only — cannot detect wrong coordinate
  SYSTEM; GCJ-02 vs WGS-84 mixups must be caught by the visual check)
- conf values against the closed set
- duplicate coordinates (overlap risk)
- duplicate name+address pairs (true redundancy); same name at different
  addresses is reported as informational only (legitimate chain branches)
- popup template still references addr/coord/conf/status/src placeholders
  (catches agents that stripped popup fields while keeping the data array intact)
- no native browser dialogs (alert/confirm/prompt) present
- no vendor map SDK (TMap/AMap/BMap/google.maps) — Leaflet only
- no runtime geocoder calls (TMap.service.Geocoder / AMap.Geocoder / .getLocation)
- no WorkBuddy proxy / runtime-secret markers (_TMapSecurityConfig, serviceHost,
  __WB_HTTP_PORT__, __WB_TMAP_SECRET__)
- optional bbox membership

Usage:
    python validate.py <map.html> [--expect N] [--bbox latmin,latmax,lngmin,lngmax] [--strict]

Exit code 0 = passed, 1 = failed. --strict treats warnings as failures.
"""
import re
import sys
import json
import argparse
from collections import Counter

PATTERN_NEW = r'\{id:(\d+), name:"([^"]+)", cat:"([^"]*)", addr:"([^"]+)", lat:([\d.\-]+), lng:([\d.\-]+), conf:"([^"]+)"\}'
PATTERN_LEGACY_CAT_ZONE = r'\{id:(\d+), name:"([^"]+)", cat:"([^"]*)", zone:"(\w+)", addr:"([^"]+)", lat:([\d.\-]+), lng:([\d.\-]+), conf:"([^"]+)"\}'
PATTERN_LEGACY_ZONE = r'\{id:(\d+), name:"([^"]+)", zone:"(\w+)", addr:"([^"]+)", lat:([\d.\-]+), lng:([\d.\-]+), conf:"([^"]+)"\}'
PATTERN_JSON_BLOCK = r'<script[^>]*id="places-data"[^>]*>(.*?)</script>'

CONF_OK = {"高", "中", "低", "high", "medium", "low"}


def parse(html):
    """Return list of dicts with keys: id, name, cat, addr, lat, lng, conf."""
    m = re.search(PATTERN_JSON_BLOCK, html, re.S)
    if m:
        try:
            data = json.loads(m.group(1))
            out = []
            for d in data:
                out.append({
                    "id": int(d["id"]), "name": str(d["name"]),
                    "cat": str(d.get("cat", "")), "addr": str(d["addr"]),
                    "lat": float(d["lat"]), "lng": float(d["lng"]),
                    "conf": str(d["conf"]),
                })
            if out:
                print("Format: JSON block (v2)")
                return out
        except (ValueError, KeyError, TypeError) as e:
            print("WARNING: places-data JSON block found but failed to parse:", e)
            print("Falling back to legacy object-literal parsing.")

    m = re.findall(PATTERN_NEW, html)
    if m:
        print("Format: legacy object literals")
        return [{"id": int(x[0]), "name": x[1], "cat": x[2], "addr": x[3],
                 "lat": float(x[4]), "lng": float(x[5]), "conf": x[6]} for x in m]
    m = re.findall(PATTERN_LEGACY_CAT_ZONE, html)
    if m:
        print("Format: legacy cat+zone")
        return [{"id": int(x[0]), "name": x[1], "cat": x[2], "addr": x[4],
                 "lat": float(x[5]), "lng": float(x[6]), "conf": x[7]} for x in m]
    m = re.findall(PATTERN_LEGACY_ZONE, html)
    if m:
        print("Format: legacy zone-only")
        return [{"id": int(x[0]), "name": x[1], "cat": "", "addr": x[3],
                 "lat": float(x[4]), "lng": float(x[5]), "conf": x[6]} for x in m]
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="Path to the generated map HTML")
    ap.add_argument("--expect", type=int, default=None,
                    help="Assert the total entry count equals N")
    ap.add_argument("--bbox", default=None,
                    help="Optional bbox latmin,latmax,lngmin,lngmax for informational check")
    ap.add_argument("--strict", action="store_true",
                    help="Treat warnings (dup coords/names/bad conf) as failures")
    args = ap.parse_args()

    with open(args.path, encoding="utf-8") as f:
        html = f.read()

    places = parse(html)
    total = len(places)
    ids = [p["id"] for p in places]
    warnings = []
    hard_errors = []

    print("Total entries:", total)
    if args.expect is not None:
        if total == args.expect:
            print("Expected count: %d -- OK" % args.expect)
        else:
            print("Expected count: %d -- MISMATCH (got %d)" % (args.expect, total))
            hard_errors.append("count mismatch")

    if ids:
        print("ID range:", min(ids), "-", max(ids), "| Unique IDs:", len(set(ids)))
        missing = [i for i in range(min(ids), max(ids) + 1) if i not in set(ids)]
        print("Missing IDs:", missing if missing else "None")
        if missing:
            hard_errors.append("missing IDs")
        dups = sorted(i for i in set(ids) if ids.count(i) > 1)
        print("Duplicate IDs:", dups if dups else "None")
        if dups:
            hard_errors.append("duplicate IDs")
    else:
        print("ID range: N/A")

    cats = Counter(p["cat"] for p in places)
    print("Category distribution:", dict(cats))

    bad = [(p["id"], p["lat"], p["lng"]) for p in places
           if not (-90 <= p["lat"] <= 90 and -180 <= p["lng"] <= 180)]
    if places:
        lats = [p["lat"] for p in places]
        lngs = [p["lng"] for p in places]
        print("Coordinate range lat:[%.4f, %.4f] lng:[%.4f, %.4f]"
              % (min(lats), max(lats), min(lngs), max(lngs)))
    print("Invalid coordinates:", bad if bad else "None")
    if bad:
        hard_errors.append("invalid coordinates")

    # conf value set
    bad_conf = sorted({p["conf"] for p in places
                       if p["conf"].lstrip("⚠").strip().lower() not in CONF_OK})
    if bad_conf:
        print("conf values outside closed set:", bad_conf)
        warnings.append("bad conf values")
    else:
        print("conf values: OK")

    # Duplicate coordinates (overlap risk)
    coord_counter = Counter((round(p["lat"], 6), round(p["lng"], 6)) for p in places)
    dup_coords = [(p["id"], p["name"]) for p in places
                  if coord_counter[(round(p["lat"], 6), round(p["lng"], 6))] > 1]
    if dup_coords:
        print("Duplicate coordinates (overlap risk):", dup_coords)
        warnings.append("duplicate coordinates")
    else:
        print("Duplicate coordinates: None")

    # Chain-aware duplicate detection:
    # same name + same address = true redundancy (warning)
    # same name, different address = informational (legitimate branches)
    pair_counter = Counter((p["name"], p["addr"]) for p in places)
    dup_pairs = sorted(k for k, v in pair_counter.items() if v > 1)
    if dup_pairs:
        print("Duplicate name+address (true redundancy):", dup_pairs)
        warnings.append("duplicate name+address")
    else:
        print("Duplicate name+address: None")

    name_counter = Counter(p["name"] for p in places)
    shared_names = sorted(n for n, v in name_counter.items() if v > 1
                          and all(pair_counter[(n, p["addr"])] == 1 for p in places if p["name"] == n))
    if shared_names:
        print("Shared names at different addresses (chain branches, informational):", shared_names)

    # Template discipline checks (independent of data parsing):
    # (a) popup template must still reference addr / coord / conf / status / src placeholders;
    # (b) native browser dialogs (alert/confirm/prompt) are banned.
    # These catch agents that started from the template but silently stripped popup fields or
    # dropped in a quick alert() for error handling.
    print("\n-- Template discipline --")
    # Placeholders actually used by map_template.html:
    #   UI.addr, UI.coord, UI.status, UI.src  (i18n labels) + c.conf (direct field)
    # c.addr / c.lat / c.lng are used implicitly via UI.addr/UI.coord bindings, so checking
    # the UI.* labels + c.conf is sufficient to confirm the popup wasn't stripped.
    popup_ok = True
    for ph in ["UI.addr", "UI.coord", "c.conf", "UI.status", "UI.src"]:
        if ph not in html:
            print("Popup placeholder missing: %s" % ph)
            popup_ok = False
            hard_errors.append("missing popup placeholder: %s" % ph)
    if popup_ok:
        print("Popup placeholders: OK (addr/coord/conf/status/src all referenced)")

    native_hits = []
    for fn in ("alert(", "confirm(", "prompt("):
        # word-boundary tolerant search; catches window.alert( and bare alert(
        if re.search(r'\b' + re.escape(fn[:-1]) + r'\s*\(', html):
            native_hits.append(fn)
    if native_hits:
        print("Native dialogs banned but found:", native_hits)
        hard_errors.append("native dialogs present")
    else:
        print("Native dialogs (alert/confirm/prompt): None -- OK")

    # Selection-basis check (reproducibility): every deliverable must declare its
    # ranking metric (META.rankedBy) and category boundary (META.catDef) so two runs
    # of the same query stay comparable. The empty template ships these blank on
    # purpose; a real deliverable MUST fill them (for "all X" set rankedBy to e.g.
    # "全量收录，无排序").
    meta_m = re.search(r'const\s+META\s*=\s*\{([^}]*)\}', html)
    if not meta_m:
        print("META block not found -- cannot verify selection basis")
        hard_errors.append("META block missing")
    else:
        meta_body = meta_m.group(1)
        def _meta_val(key):
            m = re.search(r'%s\s*:\s*"([^"]*)"' % re.escape(key), meta_body)
            return m.group(1) if m else None
        rb = _meta_val("rankedBy")
        cd = _meta_val("catDef")
        if not rb:
            print("META.rankedBy empty -- top-N reproducibility needs a stated ranking metric")
            hard_errors.append("META.rankedBy not declared")
        else:
            print("META.rankedBy: %s" % rb)
        if not cd:
            print("META.catDef empty -- category boundary must be stated")
            hard_errors.append("META.catDef not declared")
        else:
            print("META.catDef: %s" % cd)

    # Standalone-HTML discipline (catches the WorkBuddy-proxy / runtime-geocoder failure mode):
    # (c) no vendor map SDK constructors (must be Leaflet only);
    # (d) no runtime geocoder calls (all coords must be pre-baked into places-data);
    # (e) no WorkBuddy proxy / serviceHost / _TMapSecurityConfig markers.
    sdk_hits = []
    for pat in [r'new\s+TMap\.Map\s*\(', r'new\s+AMap\.Map\s*\(',
                r'new\s+BMap(?:_)?Map\s*\(', r'new\s+BMap\.Map\s*\(',
                r'new\s+google\.maps\.Map\s*\(']:
        if re.search(pat, html):
            sdk_hits.append(pat)
    if sdk_hits:
        print("Vendor map SDK banned (must use Leaflet):", sdk_hits)
        hard_errors.append("vendor map SDK present")
    else:
        print("Map engine: Leaflet only -- OK")

    geocode_hits = []
    for pat in [r'TMap\.service\.Geocoder', r'new\s+AMap\.Geocoder\s*\(',
                r'new\s+BMap\.Geocoder\s*\(', r'new\s+google\.maps\.Geocoder\s*\(',
                r'\.getLocation\s*\(\s*\{', r'geocoder\.getLocation']:
        if re.search(pat, html):
            geocode_hits.append(pat)
    if geocode_hits:
        print("Runtime geocoding banned (coords must be pre-baked):", geocode_hits)
        hard_errors.append("runtime geocoding present")
    else:
        print("Runtime geocoding: None -- OK (coords pre-baked)")

    proxy_hits = []
    for pat in [r'_TMapSecurityConfig', r'serviceHost', r'__WB_HTTP_PORT__',
                r'__WB_TMAP_SECRET__', r'127\.0\.0\.1:\s*__WB', r'_wbt/__WB']:
        if re.search(pat, html):
            proxy_hits.append(pat)
    if proxy_hits:
        print("WorkBuddy proxy / runtime secret markers banned:", proxy_hits)
        hard_errors.append("proxy/runtime-secret dependency present")
    else:
        print("Standalone (no proxy/runtime-secret): OK")

    if args.bbox:
        la0, la1, lo0, lo1 = [float(x) for x in args.bbox.split(",")]
        outside = [(p["id"], p["name"]) for p in places
                   if not (la0 <= p["lat"] <= la1 and lo0 <= p["lng"] <= lo1)]
        print("Outside bbox (informational):", outside if outside else "None")

    if total == 0:
        hard_errors.append("no entries parsed")

    soft_fail = bool(args.strict and warnings)
    ok = not hard_errors and not soft_fail
    if ok:
        status = "PASSED"
    elif hard_errors:
        status = "FAILED (%s)" % ", ".join(hard_errors)
    else:
        status = "FAILED (strict mode: %s)" % ", ".join(warnings)
    print("Validation:", status)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
