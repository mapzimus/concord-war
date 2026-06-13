#!/usr/bin/env python
"""Cut Concord into THREE zones: pure West, pure East, and the contested strip.

Two cutters:
  * Merrimack centerline (NHD flowlines from concord.gpkg, merged)
  * I-93 corridor (OSM Overpass, ref="I 93")

Pieces are classified by which side of each line they lie on, with the airport
used as a known-East landmark for direction:
  west of BOTH lines        -> West Concord
  east of BOTH lines        -> East Concord
  between (mixed sides)     -> Contested

Run AFTER build_geojson.py. Overwrites:
  static/data/front_line.geojson       (now I-93)
  static/data/territory_west.geojson   (pure West)
  static/data/territory_east.geojson   (pure East)
  static/data/territory_contested.geojson (NEW — the strip between river and I-93)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import requests
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge, split, unary_union

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static" / "data"
CACHE = ROOT / "data" / "raw"  # I-93 cache lives here, NOT in static/data (which is rebuilt)
SOURCE_GPKG = Path(r"C:\Users\Calen\concord-civil-war-map\data\processed\concord.gpkg")
BBOX = (-71.668185, 43.151772, -71.456903, 43.309419)
CRS_LOCAL = 32145
OVERPASS = "https://overpass-api.de/api/interpreter"


def fetch_i93() -> gpd.GeoDataFrame:
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
        raise RuntimeError("no I-93 ways returned by Overpass")
    return gpd.GeoDataFrame({"way": list(range(len(lines)))}, geometry=lines, crs=4326)


def extend_line(line: LineString, distance: float = 25000.0) -> LineString:
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
    d = line.project(pt)
    p1 = line.interpolate(max(d - 1.0, 0.0))
    p2 = line.interpolate(min(d + 1.0, line.length))
    cross = (p2.x - p1.x) * (pt.y - p1.y) - (p2.y - p1.y) * (pt.x - p1.x)
    return 1 if cross >= 0 else -1


def hatch_polygon(poly, spacing: float = 150.0, angle_deg: float = 45.0) -> list[LineString]:
    """Generate parallel diagonal stripes across a polygon (clipped to it)."""
    if poly is None or poly.is_empty:
        return []
    minx, miny, maxx, maxy = poly.bounds
    pad = 1000.0
    minx -= pad; miny -= pad; maxx += pad; maxy += pad
    diag = float(np.hypot(maxx - minx, maxy - miny))
    theta = np.radians(angle_deg)
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    n = int(diag / spacing) + 1
    out: list[LineString] = []
    for i in range(-n, n + 1):
        off = i * spacing
        ox, oy = cx + off * (-sin_t), cy + off * cos_t
        p1 = (ox - diag * cos_t, oy - diag * sin_t)
        p2 = (ox + diag * cos_t, oy + diag * sin_t)
        seg = LineString([p1, p2]).intersection(poly)
        if seg.is_empty:
            continue
        if seg.geom_type == "LineString":
            out.append(seg)
        elif seg.geom_type == "MultiLineString":
            out.extend(list(seg.geoms))
    return out


def main() -> int:
    STATIC.mkdir(parents=True, exist_ok=True)

    print("Loading city + airport + river from source GeoPackage...")
    city = gpd.read_file(SOURCE_GPKG, layer="city").to_crs(CRS_LOCAL)
    airport = gpd.read_file(SOURCE_GPKG, layer="airport").to_crs(CRS_LOCAL)
    river = gpd.read_file(SOURCE_GPKG, layer="river").to_crs(CRS_LOCAL)

    # I-93 cache (data/raw/i93.geojson) — separate from the static/data outputs that
    # build_geojson.py rebuilds, so a second run can't confuse Merrimack for I-93.
    CACHE.mkdir(parents=True, exist_ok=True)
    cached_i93 = CACHE / "i93.geojson"
    if cached_i93.exists():
        print(f"Loading I-93 from cache: {cached_i93}")
        i93 = gpd.read_file(cached_i93).to_crs(CRS_LOCAL)
    else:
        print("Fetching I-93 from Overpass (with up to 3 retries)...")
        import time as _t
        last_err = None
        for attempt in range(3):
            try:
                i93_raw = fetch_i93()
                break
            except Exception as e:
                last_err = e
                print(f"  attempt {attempt + 1} failed: {e}; waiting before retry")
                _t.sleep(10)
        else:
            raise RuntimeError(f"could not fetch I-93 after 3 attempts: {last_err}")
        i93_raw.to_file(cached_i93, driver="GeoJSON")
        print(f"  cached to {cached_i93}")
        i93 = i93_raw.to_crs(CRS_LOCAL)

    # Build the two cutters as single, extended polylines.
    river_merged = linemerge(unary_union(river.geometry.tolist()))
    river_main = max(river_merged.geoms, key=lambda g: g.length) if river_merged.geom_type == "MultiLineString" else river_merged
    river_cut = extend_line(river_main)
    print(f"  river cutter: {river_main.length / 1000:.2f} km")

    i93_geoms = i93.geometry.tolist()
    if len(i93_geoms) == 1 and i93_geoms[0].geom_type == "LineString":
        i93_main = i93_geoms[0]  # already merged (cached on disk)
    else:
        i93_merged = linemerge(unary_union(i93_geoms))
        i93_main = max(i93_merged.geoms, key=lambda g: g.length) if i93_merged.geom_type == "MultiLineString" else i93_merged
    i93_cut = extend_line(i93_main)
    print(f"  I-93 cutter:  {i93_main.length / 1000:.2f} km")

    # Use largest city component.
    city_poly = city.geometry.union_all()
    if city_poly.geom_type == "MultiPolygon":
        city_poly = max(city_poly.geoms, key=lambda g: g.area)

    # Cut city by BOTH lines sequentially.
    after_river = list(split(city_poly, river_cut).geoms)
    pieces = []
    for p in after_river:
        if p.intersects(i93_cut):
            pieces.extend(list(split(p, i93_cut).geoms))
        else:
            pieces.append(p)
    print(f"  city split into {len(pieces)} pieces by river + I-93")

    # Calibrate "east" using the airport.
    airport_pt = airport.geometry.union_all().centroid
    ref_river = side_sign(river_cut, airport_pt)
    ref_i93 = side_sign(i93_cut, airport_pt)

    # Classify pieces.
    west_pieces, east_pieces, contested_pieces = [], [], []
    for p in pieces:
        rep = p.representative_point()
        rs = side_sign(river_cut, rep)
        i9s = side_sign(i93_cut, rep)
        if rs == ref_river and i9s == ref_i93:
            east_pieces.append(p)
        elif rs != ref_river and i9s != ref_i93:
            west_pieces.append(p)
        else:
            contested_pieces.append(p)

    east = unary_union(east_pieces) if east_pieces else None
    west = unary_union(west_pieces) if west_pieces else None
    contested = unary_union(contested_pieces) if contested_pieces else None

    def area_km2(g):
        return (g.area / 1e6) if g else 0.0

    print(f"\n  East:      {area_km2(east):6.2f} km^2  ({len(east_pieces)} pieces)")
    print(f"  West:      {area_km2(west):6.2f} km^2  ({len(west_pieces)} pieces)")
    print(f"  Contested: {area_km2(contested):6.2f} km^2  ({len(contested_pieces)} pieces)")

    # Write outputs in EPSG:4326.
    def write(name: str, geom, props: dict):
        if geom is None or geom.is_empty:
            print(f"  skipping {name} — no geometry")
            return
        gdf = gpd.GeoDataFrame([props], geometry=[geom], crs=CRS_LOCAL).to_crs(4326)
        out = STATIC / f"{name}.geojson"
        if out.exists():
            out.unlink()
        gdf.to_file(out, driver="GeoJSON")
        print(f"  wrote {out.name}")

    write("territory_east", east, {"side": "East"})
    write("territory_west", west, {"side": "West"})
    write("territory_contested", contested, {"side": "Contested"})
    write("front_line", i93_main, {"name": "I-93 front line"})

    # Pre-compute diagonal hatching for the contested zone — campaign-map look.
    if contested is not None and not contested.is_empty:
        stripes = hatch_polygon(contested, spacing=150.0, angle_deg=45.0)
        print(f"\n  hatch: {len(stripes)} stripe segments at 150 m / 45 deg")
        if stripes:
            stripes_gdf = gpd.GeoDataFrame(
                {"id": list(range(len(stripes)))},
                geometry=stripes, crs=CRS_LOCAL,
            ).to_crs(4326)
            out = STATIC / "territory_contested_stripes.geojson"
            if out.exists():
                out.unlink()
            stripes_gdf.to_file(out, driver="GeoJSON")
            print(f"  wrote {out.name}")

    print("\ndone — three zones (West / East / Contested + hatch) live on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
