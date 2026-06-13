"""Tests for build_geojson.export_layer and the manifest builder."""
from __future__ import annotations
import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Polygon, LineString, Point

import build_geojson as bg


@pytest.fixture
def tmp_gpkg(tmp_path: Path) -> Path:
    """A minimal GeoPackage with the layers Pass A needs."""
    gpkg = tmp_path / "concord.gpkg"
    polys = gpd.GeoDataFrame(
        {"side": ["East", "West"]},
        geometry=[
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
        ],
        crs=32145,  # NH State Plane (m), like the real data
    )
    polys.to_file(gpkg, layer="territories", driver="GPKG")

    front = gpd.GeoDataFrame(
        {"name": ["Merrimack front line"]},
        geometry=[LineString([(1, 0), (1, 1)])],
        crs=32145,
    )
    front.to_file(gpkg, layer="front_line", driver="GPKG")

    river = gpd.GeoDataFrame(
        {"OBJECTID": [1, 2]},
        geometry=[LineString([(0.9, 0), (1, 0.5)]), LineString([(1, 0.5), (1.1, 1)])],
        crs=32145,
    )
    river.to_file(gpkg, layer="river", driver="GPKG")

    city = gpd.GeoDataFrame(
        {"name": ["Concord"]},
        geometry=[Polygon([(0, 0), (2, 0), (2, 1), (0, 1)])],
        crs=32145,
    )
    city.to_file(gpkg, layer="city", driver="GPKG")

    crossings = gpd.GeoDataFrame(
        {"FacilityCarried": ["I-93, US 4 NB", "Loudon Rd, NH 9"],
         "StructureName": ["", "WW II Veterans Memorial"]},
        geometry=[Point(1, 0.3), Point(1, 0.5)],
        crs=32145,
    )
    crossings.to_file(gpkg, layer="merrimack_crossings", driver="GPKG")
    return gpkg


def test_export_layer_writes_geojson_in_4326(tmp_gpkg: Path, tmp_path: Path):
    out = tmp_path / "out"
    bg.export_layer(tmp_gpkg, "territories", out, simplify_tolerance_deg=None)
    f = out / "territories.geojson"
    assert f.exists()
    fc = json.loads(f.read_text(encoding="utf-8"))
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 2
    geom = fc["features"][0]["geometry"]
    assert geom["type"] == "Polygon"


def test_export_layer_simplification_reduces_vertices(tmp_path: Path, tmp_gpkg: Path):
    out = tmp_path / "out"
    bg.export_layer(tmp_gpkg, "river", out, simplify_tolerance_deg=0.001)
    fc = json.loads((out / "river.geojson").read_text(encoding="utf-8"))
    assert fc["features"], "simplification should not erase all features"


def test_export_split_territories_writes_separate_files(tmp_gpkg: Path, tmp_path: Path):
    out = tmp_path / "out"
    bg.export_split_territories(tmp_gpkg, out)
    assert (out / "territory_east.geojson").exists()
    assert (out / "territory_west.geojson").exists()
    east = json.loads((out / "territory_east.geojson").read_text(encoding="utf-8"))
    west = json.loads((out / "territory_west.geojson").read_text(encoding="utf-8"))
    assert len(east["features"]) == 1
    assert len(west["features"]) == 1
    assert east["features"][0]["properties"]["side"] == "East"
    assert west["features"][0]["properties"]["side"] == "West"


def test_build_manifest_lists_pass_a_layers(tmp_path: Path):
    layers = [
        bg.LayerSpec(id="territory_east", group="Territory", label="East Concord",
                     geojson="territory_east.geojson", source_url="https://gis.concordnh.gov",
                     style={"fill": "#bcc6a8"}, visible_default=True),
        bg.LayerSpec(id="territory_west", group="Territory", label="West Concord",
                     geojson="territory_west.geojson", source_url="https://gis.concordnh.gov",
                     style={"fill": "#d7c597"}, visible_default=True),
    ]
    bg.write_manifest(layers, tmp_path / "manifest.json")
    m = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert m["version"] == 1
    assert len(m["layers"]) == 2
    assert m["layers"][0]["id"] == "territory_east"
    assert m["layers"][0]["source_url"].startswith("https://")


def test_build_chapters_includes_intro(tmp_path: Path):
    bg.write_chapters(tmp_path / "chapters.json")
    c = json.loads((tmp_path / "chapters.json").read_text(encoding="utf-8"))
    assert c["chapters"][0]["id"] == "intro"
    assert "camera" in c["chapters"][0]
    assert "center" in c["chapters"][0]["camera"]
