#!/usr/bin/env python
"""render_chapters.py - render one static sepia map per story chapter.

Reads static/data/chapters.json + manifest.json + the layer GeoJSONs and draws a
poster-style (1860s sepia) map image for each chapter, framed to the relevant
area, with that chapter's layers styled. Output: static/story/<id>.png.

These power the STATIC-IMAGE scrollytelling story (reliable, no live-map jank);
the live MapLibre/deck viewer lives separately at /explore.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, Rectangle
from pyproj import Transformer

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from adjustText import adjust_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "static" / "data"
OUT = ROOT / "static" / "story"
CRS = 32145

PARCH = "#e7dcc0"; INK = "#3a2f1d"; WEST = "#d7c597"; EAST = "#bcc6a8"
CONTESTED = "#c4825a"; WATER = "#9fb4c2"; FRONT = "#463722"
ARC = {"bombardment": "#9e3b2e", "air_assault": "#1a5276", "armor": "#6e2c00"}

# lon/lat focus boxes for the close-up chapters; others use the city extent.
FOCUS_LL = {
    "downtown": (-71.566, 43.186, -71.512, 43.230),
    "east": (-71.523, 43.192, -71.468, 43.240),
    "highground": (-71.527, 43.197, -71.465, 43.270),
}
CHAPTER_FOCUS = {"west_body": "downtown", "east_fist": "east", "high_ground": "highground"}

TF = Transformer.from_crs(4326, CRS, always_xy=True)


def halo(size, weight="normal", color=INK, lw=2.4):
    return dict(fontsize=size, fontweight=weight, color=color,
                family="serif", path_effects=[pe.withStroke(linewidth=lw, foreground=PARCH)])


def proj_bbox(ll):
    xs, ys = [], []
    for lon, lat in [(ll[0], ll[1]), (ll[2], ll[1]), (ll[2], ll[3]), (ll[0], ll[3])]:
        x, y = TF.transform(lon, lat)
        xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def load_layers(manifest):
    layers = {}
    for spec in manifest["layers"]:
        if not spec.get("geojson"):
            continue
        p = DATA / spec["geojson"]
        if not p.exists():
            continue
        try:
            gdf = gpd.read_file(p)
            if len(gdf):
                layers[spec["id"]] = gdf.to_crs(CRS)
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] load {spec['id']}: {e}")
    return layers


def draw_layer(ax, lid, gdf, style, labels=None):
    gtype = gdf.geom_type.iloc[0]
    if "Polygon" in gtype:
        fill = style.get("fill")
        if lid == "territory_west":
            fill = WEST
        elif lid == "territory_east":
            fill = EAST
        elif lid == "territory_contested":
            fill = CONTESTED
        if fill:
            gdf.plot(ax=ax, color=fill, alpha=style.get("fillOpacity", 0.5),
                     edgecolor=style.get("line", INK), linewidth=style.get("lineWidth", 0.5), zorder=3)
        else:
            gdf.plot(ax=ax, color="none", edgecolor=style.get("line", INK),
                     linewidth=style.get("lineWidth", 1.0), zorder=3)
    elif "Line" in gtype:
        if style.get("arc"):
            for _, row in gdf.iterrows():
                coords = list(row.geometry.coords)
                if len(coords) < 2:
                    continue
                kind = row.get("kind", "bombardment")
                ax.add_patch(FancyArrowPatch(coords[0], coords[-1], arrowstyle="-|>", mutation_scale=26,
                                             linewidth=3.2, color=ARC.get(kind, "#9e3b2e"), alpha=0.9,
                                             connectionstyle="arc3,rad=0.18", zorder=9))
        else:
            col = WATER if lid == "river" else style.get("line", INK)
            gdf.plot(ax=ax, color=col, linewidth=style.get("lineWidth", 1.0),
                     linestyle="--" if lid == "front_line" else "-", zorder=5)
    else:  # points
        col = style.get("point", "#7b241c")
        gdf.plot(ax=ax, color=col, markersize=style.get("pointRadius", 7) * 6,
                 edgecolor=PARCH, linewidth=0.6, zorder=11)
        namecol = next((c for c in ("name", "Name", "NAME") if c in gdf.columns), None)
        if namecol and labels is not None:
            for _, row in gdf.iterrows():
                nm = str(row[namecol])
                if not nm or nm == "None":
                    continue
                labels.append({"x": row.geometry.x, "y": row.geometry.y, "text": nm[:44], "color": col})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    style_by_id = {s["id"]: s.get("style", {}) for s in manifest["layers"]}
    chapters = json.loads((DATA / "chapters.json").read_text(encoding="utf-8"))["chapters"]
    layers = load_layers(manifest)
    print(f"loaded {len(layers)} layers")

    city_bounds = layers["city"].total_bounds if "city" in layers else (570000, 70000, 590000, 92000)

    for i, ch in enumerate(chapters, 1):
        cid = ch["id"]
        focus = CHAPTER_FOCUS.get(cid)
        if focus:
            minx, miny, maxx, maxy = proj_bbox(FOCUS_LL[focus])
        else:
            minx, miny, maxx, maxy = city_bounds
        mx, my = (maxx - minx) * 0.04, (maxy - miny) * 0.04

        fig, ax = plt.subplots(figsize=(11, 8))
        fig.patch.set_facecolor(PARCH)
        ax.set_facecolor(PARCH)
        ax.set_aspect("equal")
        ax.set_axis_off()
        labels = []

        # always-on geographic context
        for ctx, st in [("surrounding_towns", {"line": "#cdbf9c", "lineWidth": 0.5}),
                        ("city", {"line": INK, "lineWidth": 1.4}),
                        ("river", {"line": WATER, "lineWidth": 1.6}),
                        ("front_line", {"line": FRONT, "lineWidth": 2.4})]:
            if ctx in layers:
                try:
                    draw_layer(ax, ctx, layers[ctx], st, labels)
                except Exception as e:  # noqa: BLE001
                    print(f"  [warn] ctx {ctx}: {e}")

        # chapter layers on top (skip context already drawn + special terrain flag)
        for lid in ch.get("layers", []):
            if lid in ("city", "river", "front_line", "surrounding_towns"):
                continue
            if lid not in layers:
                continue
            try:
                draw_layer(ax, lid, layers[lid], style_by_id.get(lid, {}), labels)
            except Exception as e:  # noqa: BLE001
                print(f"  [warn] {cid}/{lid}: {e}")

        ax.set_xlim(minx - mx, maxx + mx)
        ax.set_ylim(miny - my, maxy + my)

        # place point labels and de-conflict overlaps (with leader lines)
        if labels:
            texts = [ax.text(p["x"], p["y"], p["text"],
                             **halo(8.5, "bold", p["color"], 2.2), zorder=13) for p in labels]
            try:
                adjust_text(texts, x=[p["x"] for p in labels], y=[p["y"] for p in labels], ax=ax,
                            arrowprops=dict(arrowstyle="-", color="#6b5a2a", lw=0.6, alpha=0.7))
            except Exception as e:  # noqa: BLE001
                print(f"  [warn] adjust_text {cid}: {e}")

        # title cartouche (top-left)
        ax.text(0.025, 0.965, f"{i:02d}  {ch['title']}", transform=ax.transAxes, va="top",
                **halo(20, "bold", INK, 3))
        if ch.get("subtitle"):
            ax.text(0.025, 0.915, ch["subtitle"], transform=ax.transAxes, va="top",
                    **halo(12, "normal", "#6b5a2a", 2.2))

        out = OUT / f"{cid}.png"
        fig.savefig(out, dpi=150, facecolor=PARCH, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        print(f"[{i:02d}] {cid} -> {out.name}")

    print(f"\nrendered {len(chapters)} chapter maps -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
