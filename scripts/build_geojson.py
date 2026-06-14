"""Export Pass-A GeoJSON layers + manifest + chapters from concord.gpkg.

Source: ../concord-civil-war-map/data/processed/concord.gpkg (19 layers built
by the poster pipeline). Pass A exports a subset: city, river (NHD flowlines),
front_line, territory_east, territory_west, crossings. Future passes add the
remaining ~24 layers (military, police, lifelines, viewshed, etc.).

All output is EPSG:4326 GeoJSON for web consumption.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import geopandas as gpd

DEFAULT_GPKG = Path(r"C:\Users\Calen\concord-civil-war-map\data\processed\concord.gpkg")


@dataclass
class LayerSpec:
    id: str
    group: str
    label: str
    geojson: str
    source_url: str
    style: dict[str, Any] = field(default_factory=dict)
    visible_default: bool = True
    note: str = ""


def export_layer(gpkg: Path, layer: str, out_dir: Path,
                 simplify_tolerance_deg: float | None = 0.00005) -> Path:
    """Read one GeoPackage layer, reproject to 4326, optionally simplify, write GeoJSON."""
    out_dir.mkdir(parents=True, exist_ok=True)
    gdf = gpd.read_file(gpkg, layer=layer).to_crs(4326)
    if simplify_tolerance_deg is not None and not gdf.empty:
        gdf["geometry"] = gdf.geometry.simplify(simplify_tolerance_deg, preserve_topology=True)
    out = out_dir / f"{layer}.geojson"
    if out.exists():
        out.unlink()
    gdf.to_file(out, driver="GeoJSON")
    return out


def export_split_territories(gpkg: Path, out_dir: Path) -> tuple[Path, Path]:
    """The `territories` layer holds both sides; emit territory_east + territory_west."""
    out_dir.mkdir(parents=True, exist_ok=True)
    gdf = gpd.read_file(gpkg, layer="territories").to_crs(4326)
    east = gdf[gdf["side"] == "East"]
    west = gdf[gdf["side"] == "West"]
    p_east = out_dir / "territory_east.geojson"
    p_west = out_dir / "territory_west.geojson"
    if p_east.exists():
        p_east.unlink()
    if p_west.exists():
        p_west.unlink()
    east.to_file(p_east, driver="GeoJSON")
    west.to_file(p_west, driver="GeoJSON")
    return p_east, p_west


def export_resources_by_category(gpkg: Path, out_dir: Path) -> dict[str, int]:
    """Split the poster's 18 resources by `category` into per-category GeoJSONs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    gdf = gpd.read_file(gpkg, layer="resources").to_crs(4326)
    counts: dict[str, int] = {}
    for cat in sorted(gdf["category"].unique()):
        sub = gdf[gdf["category"] == cat]
        out = out_dir / f"resources_{cat}.geojson"
        if out.exists():
            out.unlink()
        sub.to_file(out, driver="GeoJSON")
        counts[cat] = len(sub)
    return counts


def write_extra_points(out_dir: Path) -> None:
    """Author the research-only assets that don't live in the poster GeoPackage."""
    out_dir.mkdir(parents=True, exist_ok=True)
    extras = {
        "himars": {
            "label": "HIMARS launchers (3-197 FA)",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-71.5124, 43.2103]},
                "properties": {
                    "name": "HIMARS launchers (3-197 FA)",
                    "side": "E", "category": "military",
                    "note": "M142 HIMARS strategic rocket artillery at the NH Army National Guard State Military Reservation (1 Minuteman Way)."
                }
            }]
        },
        "blackhawks": {
            "label": "Black Hawks (151st Aviation / AASF)",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-71.5023, 43.2027]},
                "properties": {
                    "name": "Black Hawks (151st Aviation / AASF)",
                    "side": "E", "category": "military_air",
                    "note": "UH-60 Black Hawks at the Army Aviation Support Facility, Concord Municipal Airport. Includes 238th MEDEVAC."
                }
            }]
        },
        "garvins_falls": {
            "label": "Garvins Falls hydroelectric (12.4 MW)",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-71.515, 43.135]},
                "properties": {
                    "name": "Garvins Falls hydro (12.4 MW)",
                    "side": "Contested", "category": "power_gen",
                    "note": "Mid-river hydroelectric on the Bow/Concord line; owner Hull Street Energy. The contested generator — the river itself."
                }
            }]
        }
    }
    for key, payload in extras.items():
        out = out_dir / f"{key}.geojson"
        if out.exists():
            out.unlink()
        out.write_text(
            json.dumps({"type": "FeatureCollection", "features": payload["features"]}, indent=2),
            encoding="utf-8")


def write_manifest(layers: Iterable[LayerSpec], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"version": 1, "layers": [asdict(l) for l in layers]}, indent=2),
                   encoding="utf-8")


CONCORD_CENTROID = [-71.538, 43.207]


def write_chapters(out: Path) -> None:
    """Pass A ships chapter 1 (intro) + a stub explorer chapter so the panel can mount."""
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "chapters": [
            {
                "id": "intro",
                "title": "The Two Banks",
                "subtitle": "An alternate history of Concord, New Hampshire.",
                "body": "The Merrimack River and Interstate 93 run roughly parallel through Concord. West of BOTH lies the body of the city - downtown, the State House, hospital, prisons. East of BOTH lies the fist - airport, NH National Guard, State Office Park, the Heights. The strip between the river and the highway is no-man's-land: Fort Eddy Rd, Everett Arena, NHTI, the airport approach. In an alternate-history civil war this strip becomes the battleground - both sides bleed into it, neither holds it for long.",
                "stats": [],
                "camera": {"center": CONCORD_CENTROID, "zoom": 11, "pitch": 0, "bearing": 0},
                "layers": [
                    "city", "river", "front_line",
                    "territory_contested", "territory_contested_stripes",
                    "crossings", "flashpoints"
                ]
            },
            {
                "id": "explorer",
                "title": "Explore",
                "subtitle": "Toggle layers freely.",
                "body": "",
                "stats": [],
                "camera": {"center": CONCORD_CENTROID, "zoom": 11.3, "pitch": 0, "bearing": 0},
                "layers": [
                    "city", "river", "front_line",
                    "territory_east", "territory_west",
                    "territory_contested", "territory_contested_stripes",
                    "crossings", "flashpoints",
                    "viewshed_east", "exposed_west",
                    "himars", "blackhawks",
                    "resources_military", "resources_police", "resources_manpower",
                    "resources_medical", "resources_govt", "resources_command",
                    "resources_water", "garvins_falls", "resources_energy",
                    "resources_logistics", "resources_fortress", "resources_transport"
                ]
            }
        ]
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")


PASS_A_MANIFEST: list[LayerSpec] = [
    LayerSpec(id="city", group="Territory", label="City of Concord boundary",
              geojson="city.geojson",
              source_url="https://gis.concordnh.gov/arc1061/rest/services/CityGeneral/WaterSystemGIS/MapServer/63",
              style={"line": "#3a2f1d", "lineWidth": 2}, visible_default=True),
    LayerSpec(id="river", group="Territory", label="Merrimack River (NHD flowlines)",
              geojson="river.geojson",
              source_url="https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6",
              style={"line": "#26527a", "lineWidth": 2}, visible_default=True),
    LayerSpec(id="front_line", group="Territory", label="I-93 corridor (front line)",
              geojson="front_line.geojson",
              source_url="OpenStreetMap: way[ref=\"I 93\"] within Concord bbox (recut_on_i93.py)",
              style={"line": "#463722", "lineWidth": 3}, visible_default=True),
    LayerSpec(id="territory_east", group="Territory", label="East Concord",
              geojson="territory_east.geojson",
              source_url="derived: city polygon cut on the I-93 corridor",
              style={"fill": "#bcc6a8", "fillOpacity": 0.55}, visible_default=False),
    LayerSpec(id="territory_west", group="Territory", label="West Concord",
              geojson="territory_west.geojson",
              source_url="derived: city polygon cut on the I-93 corridor",
              style={"fill": "#d7c597", "fillOpacity": 0.55}, visible_default=False),
    LayerSpec(id="territory_contested", group="Territory", label="Contested zone (river ↔ I-93)",
              geojson="territory_contested.geojson",
              source_url="derived: city pieces between the Merrimack and I-93",
              style={"fill": "#c4825a", "fillOpacity": 0.55, "line": "#6e2c00", "lineWidth": 1.5}, visible_default=True),
    LayerSpec(id="territory_contested_stripes", group="Territory", label="Contested zone (hatch)",
              geojson="territory_contested_stripes.geojson",
              source_url="derived: 150 m / 45° diagonal hatch over the contested zone",
              style={"line": "#9e3b2e", "lineWidth": 1.2}, visible_default=True,
              note="visual hatching for the contested zone — 1860s campaign-map look"),
    LayerSpec(id="crossings", group="Transport", label="Merrimack River crossings",
              geojson="crossings.geojson",
              source_url="https://gis.concordnh.gov/arc1061/rest/services/CityGeneral/WaterSystemGIS/MapServer/44",
              style={"point": "#b22222", "pointRadius": 6}, visible_default=False),

    # === Tactical overlays (poster data) ===
    LayerSpec(id="viewshed_east", group="Tactical", label="East viewshed (3DEP DEM)",
              geojson="viewshed_east.geojson",
              source_url="USGS 3DEP DEM + gdal.ViewshedGenerate from airport / armory / Oak Hill",
              style={"fill": "#7d6608", "fillOpacity": 0.20, "line": "#7d6608", "lineWidth": 0.5},
              visible_default=False,
              note="Everything East's batteries can SEE — i.e. can shell"),
    LayerSpec(id="exposed_west", group="Tactical", label="Beaten zone (West under fire)",
              geojson="exposed_west.geojson",
              source_url="viewshed_east ∩ territory_west — 36.4% of the west bank",
              style={"fill": "#9e3b2e", "fillOpacity": 0.35, "line": "#9e3b2e", "lineWidth": 0.5},
              visible_default=False,
              note="The west-bank ground actually exposed to East fire"),
    LayerSpec(id="flashpoints", group="Tactical", label="Contested flashpoints",
              geojson="flashpoints.geojson",
              source_url="curated points: Hannah Dustin, Exit 17, Sewalls Falls, Exit 16, Fort Eddy plaza, NHTI, Bow Jct",
              style={"point": "#7b241c", "pointRadius": 9, "line": "#3a2f1d", "lineWidth": 1.5},
              visible_default=False),

    # === Military (named installations + research-only assets) ===
    LayerSpec(id="himars", group="Military", label="HIMARS launchers (3-197 FA)",
              geojson="himars.geojson",
              source_url="NH Army National Guard, 3rd Battalion 197th Field Artillery (M142 HIMARS)",
              style={"point": "#c0392b", "pointRadius": 11, "line": "#3a2f1d", "lineWidth": 1.5},
              visible_default=False,
              note="Strategic rocket artillery — East's range advantage"),
    LayerSpec(id="blackhawks", group="Military", label="Black Hawks (AASF / 151st Aviation)",
              geojson="blackhawks.geojson",
              source_url="Army Aviation Support Facility, Concord Municipal Airport",
              style={"point": "#1a5276", "pointRadius": 11, "line": "#3a2f1d", "lineWidth": 1.5},
              visible_default=False,
              note="UH-60 air mobility — East can bypass the bridges"),
    LayerSpec(id="resources_military", group="Military", label="NHARNG sites",
              geojson="resources_military.geojson",
              source_url="poster: 07_resources.py (Census geocoded + bank-validated)",
              style={"point": "#7b241c", "pointRadius": 8, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),

    # === Police / corrections ===
    LayerSpec(id="resources_police", group="Forces", label="Police HQ + BearCat (West)",
              geojson="resources_police.geojson",
              source_url="poster: 07_resources.py",
              style={"point": "#1a5276", "pointRadius": 8, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),
    LayerSpec(id="resources_manpower", group="Forces", label="State prisons (1,408+ inmates)",
              geojson="resources_manpower.geojson",
              source_url="poster: 07_resources.py",
              style={"point": "#4a3520", "pointRadius": 8, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),

    # === Medical ===
    LayerSpec(id="resources_medical", group="Medical", label="Hospitals (Level II + psych)",
              geojson="resources_medical.geojson",
              source_url="poster: 07_resources.py",
              style={"point": "#922b21", "pointRadius": 9, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),

    # === Government & command ===
    LayerSpec(id="resources_govt", group="Government", label="State House",
              geojson="resources_govt.geojson",
              source_url="poster: 07_resources.py",
              style={"point": "#5b3a1a", "pointRadius": 10, "line": "#3a2f1d", "lineWidth": 1.5},
              visible_default=False),
    LayerSpec(id="resources_command", group="Government", label="Supreme Court / DOS HQ / data ctr",
              geojson="resources_command.geojson",
              source_url="poster: 07_resources.py",
              style={"point": "#7d6608", "pointRadius": 8, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),

    # === Lifelines: water ===
    LayerSpec(id="resources_water", group="Water", label="Drinking water + WWTPs",
              geojson="resources_water.geojson",
              source_url="poster: 07_resources.py (Hutchins WTP, Hall St WWTP, Penacook Lake)",
              style={"point": "#1f618d", "pointRadius": 9, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),

    # === Lifelines: power + fuel ===
    LayerSpec(id="garvins_falls", group="Power", label="Garvins Falls hydro (12.4 MW)",
              geojson="garvins_falls.geojson",
              source_url="Hull Street Energy / FERC; mid-river on the Bow line",
              style={"point": "#f1c40f", "pointRadius": 11, "line": "#3a2f1d", "lineWidth": 1.5},
              visible_default=False,
              note="The contested generator — neither bank can claim it"),
    LayerSpec(id="resources_energy", group="Power", label="Solar + propane + transfer station",
              geojson="resources_energy.geojson",
              source_url="poster: 07_resources.py (Rymes Propane, Old Turnpike solar 6.7 MW)",
              style={"point": "#9c640c", "pointRadius": 8, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),

    # === Logistics & fortress ===
    LayerSpec(id="resources_logistics", group="Logistics", label="Loudon Rd big-box belt",
              geojson="resources_logistics.geojson",
              source_url="poster: 07_resources.py (Walmart/Sam's/Target/Market Basket)",
              style={"point": "#7d6608", "pointRadius": 8, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),
    LayerSpec(id="resources_fortress", group="Logistics", label="Steeplegate Mall (staging)",
              geojson="resources_fortress.geojson",
              source_url="poster: 07_resources.py",
              style={"point": "#6e2c00", "pointRadius": 9, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),
    LayerSpec(id="resources_transport", group="Logistics", label="Concord Municipal Airport",
              geojson="resources_transport.geojson",
              source_url="poster: 07_resources.py",
              style={"point": "#196f3d", "pointRadius": 9, "line": "#3a2f1d", "lineWidth": 1.2},
              visible_default=False),

    # === Lifeline networks (workflow-sourced) ===
    LayerSpec(id="lifelines_power", group="Power", label="Power & utility network",
              geojson="lifelines_power.geojson",
              source_url="workflow research: substations, Garvins Falls, solar, gas, comms (cited per point)",
              style={"point": "#9c640c", "pointRadius": 7, "line": "#3a2f1d", "lineWidth": 1.0},
              visible_default=False),
    LayerSpec(id="lifelines_water", group="Water", label="Water & wastewater network",
              geojson="lifelines_water.geojson",
              source_url="workflow research: Penacook Lake, Hutchins WTP, Hall St + Penacook WWTP (cited per point)",
              style={"point": "#1f618d", "pointRadius": 7, "line": "#3a2f1d", "lineWidth": 1.0},
              visible_default=False),

    # === Transport / scenario layers ===
    LayerSpec(id="i93_exits", group="Transport", label="I-93 interchanges",
              geojson="i93_exits.geojson",
              source_url="City of Concord interstate-exit layer (Exits 12-17 = I-93)",
              style={"point": "#6e2c00", "pointRadius": 6, "line": "#3a2f1d", "lineWidth": 1.0},
              visible_default=False),
    LayerSpec(id="blitz_arcs", group="Tactical", label="Blitz — offensive arcs",
              geojson="blitz_arcs.geojson",
              source_url="authored from the blitz scenario (HIMARS / air assault / armor)",
              style={"arc": True, "line": "#c0392b", "lineWidth": 3}, visible_default=False,
              note="East's week-one offensive: bombardment, air assault, armor thrusts"),
    LayerSpec(id="terrain_3d", group="Terrain", label="3D terrain (the Heights)",
              geojson="",
              source_url="Mapzen / AWS Terrain Tiles (terrarium raster-DEM)",
              style={"terrain": True}, visible_default=False,
              note="Toggles real 3D relief + hillshade; best with a tilted camera"),
    LayerSpec(id="siege_overlay", group="Tactical", label="Siege — held/blown crossings",
              geojson="siege_overlay.geojson",
              source_url="derived: the crossings as chokepoints West holds or blows",
              style={"point": "#7b241c", "pointRadius": 8, "line": "#3a2f1d", "lineWidth": 1.5},
              visible_default=False),
]


def main(gpkg: Path = DEFAULT_GPKG, out_dir: Path | None = None) -> int:
    out_dir = out_dir or (Path(__file__).resolve().parent.parent / "static" / "data")
    print(f"reading {gpkg}")
    print(f"writing to {out_dir}")

    export_layer(gpkg, "city", out_dir)
    export_layer(gpkg, "river", out_dir)
    export_layer(gpkg, "front_line", out_dir)
    export_split_territories(gpkg, out_dir)
    p_cross = export_layer(gpkg, "merrimack_crossings", out_dir)
    # Rename merrimack_crossings.geojson -> crossings.geojson to match the manifest id
    target = out_dir / "crossings.geojson"
    if target.exists():
        target.unlink()
    p_cross.rename(target)

    # Pass A+ additions: tactical overlays and the resource catalog. Viewshed
    # polygons are raster-derived with thousands of jagged vertices; a 25 m
    # tolerance drops them from ~7 MB to ~200 KB without changing what the eye
    # sees at city-scale zoom.
    export_layer(gpkg, "viewshed_east", out_dir, simplify_tolerance_deg=0.00025)
    export_layer(gpkg, "exposed_west", out_dir, simplify_tolerance_deg=0.00025)
    export_layer(gpkg, "flashpoints", out_dir)
    res_counts = export_resources_by_category(gpkg, out_dir)
    print(f"  resources split by category: {res_counts}")
    write_extra_points(out_dir)

    write_manifest(PASS_A_MANIFEST, out_dir / "manifest.json")
    # chapters.json is now authored by the deep-content workflow (apply_workflow.py),
    # not generated here — don't clobber it.

    print(f"wrote {len(PASS_A_MANIFEST)} layers + manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
