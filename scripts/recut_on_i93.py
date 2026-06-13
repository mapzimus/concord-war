#!/usr/bin/env python
"""Recut Concord territories on I-93 instead of the Merrimack centerline.

Design refinement: the front line follows I-93 (the highway corridor) rather than
the river. The river is still drawn as geography but no longer divides territory.

Reuses the city polygon and airport landmark from concord.gpkg (still the source
of truth for geometry), fetches I-93 from OSM Overpass, cuts the city on it, and
overwrites the three Pass-A layers affected:
  * front_line.geojson         (now I-93)
  * territory_east.geojson     (now East-of-I-93)
  * territory_west.geojson     (now West-of-I-93)

Run AFTER build_geojson.py.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import geopandas as gpd
import requests
from shapely.geometry import LineString
from shapely.ops import linemerge, split, unary_union

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static" / "data"
SOURCE_GPKG = Path(r"C:\Users\Calen\concord-civil-war-map\data\processed\concord.gpkg")
BBOX = (-71.668185, 43.151772, -71.456903, 43.309419)
CRS_LOCAL = 32145  # NH State Plane, metres
OVERPASS = "https://overpass-api.de/api/interpreter"


def fetch_i93() -> gpd.GeoDataFrame:
    """Fetch I-93 ways within the Concord bbox from OSM Overpass."""
    s, w, n, e = BBOX[1], BBOX[0], BBOX[3], BBOX[2]
    query = f"""
    [out:json][timeout:60];
    (
      way["ref"="I 93"]({s},{w},{n},{e});
      way["ref"~"^I 93"]({s},{w},{n},{e});
    );
    (._;>;);
    out body;
    """
    r = requests.post(OVERPASS, data={"data": query}, timeout=120,
                      headers={"User-Agent": "concord-war/0.1 (mhowe.gis@gmail.com)"})
    r.raise_for_status()
    data = r.json()
    nodes = {n["id"]: (n["lon"], n["lat"]) for n in data["elements"] if n["type"] == "node"}
    lines = []
    for el in data["elements"]:
        if el["type"] != "way":
            continue
        coords = [nodes[nid] for nid in el["nodes"] if nid in nodes]
        if len(coords) >= 2:
            lines.append(LineString(coords))
    if not lines:
        raise RuntimeError("no I-93 ways returned by Overpass — check ref tag")
    return gpd.GeoDataFrame({"way": list(range(len(lines)))}, geometry=lines, crs=4326)


def extend_line(line: LineString, distance: float = 25000.0) -> LineString:
    """Extend a polyline past both endpoints so it fully crosses the city polygon."""
    c = list(line.coords)

    def unit(ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        return dx / L, dy / L

    ux, uy = unit(c[1][0], c[1][1], c[0][0], c[0][1])
    vx, vy = unit(c[-2][0], c[-2][1], c[-1][0], c[-1][1])
    start = (c[0][0] + ux * distance, c[0][1] + uy * distance)
    end = (c[-1][0] + vx * distance, c[-1][1] + vy * distance)
    return LineString([start] + c + [end])


def side_sign(line: LineString, pt) -> int:
    """+1 / -1 for which side of `line` point `pt` falls on (orientation-agnostic)."""
    d = line.project(pt)
    p1 = line.interpolate(max(d - 1.0, 0.0))
    p2 = line.interpolate(min(d + 1.0, line.length))
    cross = (p2.x - p1.x) * (pt.y - p1.y) - (p2.y - p1.y) * (pt.x - p1.x)
    return 1 if cross >= 0 else -1


def main() -> int:
    STATIC.mkdir(parents=True, exist_ok=True)

    print("Fetching I-93 from Overpass...")
    i93 = fetch_i93().to_crs(CRS_LOCAL)
    print(f"  {len(i93)} I-93 way segments")

    print("Loading city + airport from source GeoPackage...")
    city = gpd.read_file(SOURCE_GPKG, layer="city").to_crs(CRS_LOCAL)
    airport = gpd.read_file(SOURCE_GPKG, layer="airport").to_crs(CRS_LOCAL)

    # Merge fragmented I-93 ways into one continuous polyline; keep the longest.
    merged = linemerge(unary_union(i93.geometry.tolist()))
    main_line = max(merged.geoms, key=lambda g: g.length) if merged.geom_type == "MultiLineString" else merged
    print(f"  I-93 main line: {main_line.length / 1000:.2f} km")

    cutter = extend_line(main_line)

    # Use the largest city polygon component.
    city_poly = city.geometry.union_all()
    if city_poly.geom_type == "MultiPolygon":
        city_poly = max(city_poly.geoms, key=lambda g: g.area)

    pieces = list(split(city_poly, cutter).geoms)
    print(f"  city split into {len(pieces)} pieces by I-93")

    # Calibrate sides against airport (known East).
    ref = side_sign(cutter, airport.geometry.union_all().centroid)
    east = unary_union([g for g in pieces if side_sign(cutter, g.representative_point()) == ref])
    west = unary_union([g for g in pieces if side_sign(cutter, g.representative_point()) != ref])

    print(f"  East: {east.area / 1e6:6.2f} km^2,  West: {west.area / 1e6:6.2f} km^2")

    # Write outputs (overwriting build_geojson.py's river-cut versions).
    east_gdf = gpd.GeoDataFrame({"side": ["East"]}, geometry=[east], crs=CRS_LOCAL).to_crs(4326)
    west_gdf = gpd.GeoDataFrame({"side": ["West"]}, geometry=[west], crs=CRS_LOCAL).to_crs(4326)
    front_gdf = gpd.GeoDataFrame({"name": ["I-93 front line"]}, geometry=[main_line], crs=CRS_LOCAL).to_crs(4326)

    for name, gdf in [
        ("territory_east", east_gdf),
        ("territory_west", west_gdf),
        ("front_line", front_gdf),
    ]:
        out = STATIC / f"{name}.geojson"
        if out.exists():
            out.unlink()
        gdf.to_file(out, driver="GeoJSON")
        print(f"  wrote {out.name}")

    print("\ndone — front line is now I-93")
    return 0


if __name__ == "__main__":
    sys.exit(main())
