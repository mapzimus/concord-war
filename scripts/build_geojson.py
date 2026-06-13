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
                "body": "Interstate 93 cuts north-south through Concord, separating West (downtown, State House, hospital, prisons) from East (airport, NH National Guard, State Office Park, the Heights). In an alternate-history civil war the highway becomes the front line - both sides fight to seize and hold the exits and interchanges along it.",
                "stats": [],
                "camera": {"center": CONCORD_CENTROID, "zoom": 11, "pitch": 0, "bearing": 0},
                "layers": ["city", "river", "front_line"]
            },
            {
                "id": "explorer",
                "title": "Explore",
                "subtitle": "Toggle layers freely.",
                "body": "",
                "stats": [],
                "camera": {"center": CONCORD_CENTROID, "zoom": 11.3, "pitch": 0, "bearing": 0},
                "layers": ["city", "river", "front_line", "territory_east", "territory_west", "crossings"]
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
    LayerSpec(id="crossings", group="Transport", label="Merrimack River crossings",
              geojson="crossings.geojson",
              source_url="https://gis.concordnh.gov/arc1061/rest/services/CityGeneral/WaterSystemGIS/MapServer/44",
              style={"point": "#b22222", "pointRadius": 6}, visible_default=False),
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

    write_manifest(PASS_A_MANIFEST, out_dir / "manifest.json")
    write_chapters(out_dir / "chapters.json")

    print(f"wrote {len(PASS_A_MANIFEST)} layers + manifest + chapters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
