#!/usr/bin/env python
"""apply_workflow.py - turn the deep-content workflow result into app data files.

Reads the workflow's JSON result (research + verification + authored content) and
writes the SvelteKit static data: chapters.json, forces.json (dashboard),
installations.json (drawer), lifelines_power/water layers, i93_exits, blitz_arcs,
siege_overlay. Applies the verification corrections (e.g. Garvins Falls ownership).

Run AFTER build_geojson.py + build_zones.py (those produce the base layers; this
adds the authored content + a few derived layers).
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import mapping

OUT = Path(__file__).resolve().parent.parent / "static" / "data"
RESULT = Path(r"C:\Users\Calen\AppData\Local\Temp\claude\C--Users-Calen\9d334c00-ad1e-4632-a4a9-151b71bf3071\tasks\w7dlbhrgs.output")
GPKG = Path(r"C:\Users\Calen\concord-civil-war-map\data\processed\concord.gpkg")


def fc(features):
    return {"type": "FeatureCollection", "features": features}


def write(name, payload):
    p = OUT / name
    if p.exists():
        p.unlink()
    p.write_text(json.dumps(payload, indent=2 if name.endswith(".json") and "geojson" not in name else None), encoding="utf-8")
    return p


def main() -> int:
    data = json.loads(RESULT.read_text(encoding="utf-8"))
    r = data["result"]

    # 1) chapters.json (the 10-chapter story)
    chapters = r["chapters"]["chapters"]
    for ch in chapters:  # user-reported tanks belong in the East + Blitz chapters
        if ch["id"] in ("east_fist", "blitz") and "tanks" not in ch["layers"]:
            ch["layers"].append("tanks")
    write("chapters.json", {"version": 1, "chapters": chapters})
    print(f"chapters: {len(chapters)} -> {[c['id'] for c in chapters]}")

    # 2) forces.json (dashboard metrics)
    metrics = r["dashboard"]["metrics"]
    metrics.append({
        "key": "tanks", "label": "Tanks / tracked armor",
        "west": "0", "east": "present", "unit": "State Military Reservation",
        "advantage": "East",
        "source_url": "NH National Guard State Military Reservation (reported on-site)",
    })
    write("forces.json", {"version": 1, "metrics": metrics})
    print(f"forces metrics: {len(metrics)}")

    # 3) installations.json (drawer enrichment)
    inst = r["installations"]["installations"]
    inst.append({
        "name": "Tanks / tracked armor", "category": "armor", "side": "East",
        "blurb": "Tracked armor at the NH National Guard State Military Reservation (reported on-site) - the heaviest direct-fire ground assets in the city, and East's armored fist.",
        "stats": [{"label": "Side", "value": "East"}, {"label": "Type", "value": "Tracked armor"}, {"label": "Sourcing", "value": "On-site report"}],
        "source_url": "NH National Guard State Military Reservation, 1 Minuteman Way, Concord",
    })
    write("installations.json", {"installations": inst})
    print(f"installations: {len(inst)}")

    # 4) lifelines -> power / water point layers
    assets = r["lifelines"]["assets"]

    def feat(a):
        return {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [a["lon"], a["lat"]]},
            "properties": {
                "name": a["name"], "kind": a["kind"], "side": a["bank"],
                "note": a["capacity"], "source_url": a["source_url"], "confidence": a["confidence"],
            },
        }

    POWER = {"power_generation", "power_substation", "power_line", "gas", "fuel", "comms"}
    WATER = {"water_source", "water_treatment", "wastewater"}
    power = [feat(a) for a in assets if a["kind"] in POWER]
    water = [feat(a) for a in assets if a["kind"] in WATER]
    write("lifelines_power.geojson", fc(power))
    write("lifelines_water.geojson", fc(water))
    print(f"lifelines power/water: {len(power)}/{len(water)}")

    # 4b) Correct garvins_falls from research (verified coord + ownership fix)
    g = [a for a in assets if "Garvins" in a["name"]]
    if g:
        a = g[0]
        write("garvins_falls.geojson", fc([{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [a["lon"], a["lat"]]},
            "properties": {
                "name": "Garvins Falls hydro (12.4 MW)", "side": "Contested", "category": "power_gen",
                "note": "Mid-river hydroelectric on the Bow/Concord line; 12.4 MW across 4 units. "
                        "Owner LS Power / Patriot Hydro (formerly Hull Street Energy, sold 2023). "
                        "The contested generator - the river itself.",
                "source_url": a["source_url"],
            },
        }]))
        print(f"garvins corrected -> ({a['lat']},{a['lon']})")

    # 5) i93_exits from the city interstate-exit layer (Exit-12..17 = I-93)
    ex = gpd.read_file(GPKG, layer="interstate_exits").to_crs(4326)
    i93ids = {f"Exit-{n}" for n in range(12, 18)}
    e = ex[ex["ExitID"].isin(i93ids)]
    exits = [{
        "type": "Feature", "geometry": mapping(row.geometry),
        "properties": {"name": str(row["ExitID"]).replace("Exit-", "I-93 Exit "), "category": "transport"},
    } for _, row in e.iterrows()]
    write("i93_exits.geojson", fc(exits))
    print(f"i93 exits: {len(exits)}")

    # 6) blitz_arcs - authored offensive lines (bombardment / air assault / armor)
    HIMARS = (-71.5045, 43.2035)
    AASF = (-71.5022, 43.2027)
    STATEHOUSE = (-71.5381, 43.2067)
    HUTCHINS = (-71.5731, 43.2442)
    DOWNTOWN = (-71.538, 43.207)
    I393 = (-71.523, 43.220)
    arcs = [
        ("HIMARS barrage - bridges & substations", "bombardment", HIMARS, STATEHOUSE),
        ("HIMARS barrage - water works", "bombardment", HIMARS, HUTCHINS),
        ("Black Hawk air assault - State House", "air_assault", AASF, DOWNTOWN),
        ("Black Hawk air assault - water plant", "air_assault", AASF, HUTCHINS),
        ("Armor thrust - I-393 / Loudon Rd interchange", "armor", (-71.504, 43.205), I393),
    ]
    afeats = [{
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [list(a), list(b)]},
        "properties": {"name": n, "kind": k},
    } for (n, k, a, b) in arcs]
    write("blitz_arcs.geojson", fc(afeats))
    print(f"blitz arcs: {len(afeats)}")

    # 7) siege_overlay - the crossings as chokepoints West holds/blows
    cr = json.loads((OUT / "crossings.geojson").read_text(encoding="utf-8"))
    for f in cr.get("features", []):
        f.setdefault("properties", {})["siege_role"] = "chokepoint (hold or blow)"
    write("siege_overlay.geojson", cr)
    print(f"siege_overlay: {len(cr.get('features', []))} chokepoints")

    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
