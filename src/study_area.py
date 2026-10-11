"""
study_area.py - Step S4: Compute core and build area polygons.
Projects stations to metric CRS (EPSG:32643), creates core 3km buffers,
unions them, and adds a 500m margin for the build network area.
"""

from pathlib import Path
import json
import geopandas as gpd
from shapely.validation import make_valid
from shapely.geometry import Polygon, MultiPolygon

from src.config import load_config


def compute_study_areas(
    stations_path: str | Path = "data/interim/stations_selected.gpkg",
    config_path: str | Path = "config/params.yaml",
    output_dir: str | Path = "data/interim"
) -> dict:
    """
    Computes core study area and build area polygons for the selected stations.
    
    Returns:
        dict: Summary containing areas (sq km), station count, and bounding boxes.
    """
    cfg = load_config(config_path)
    metric_crs = cfg["study"]["metric_crs"]
    display_crs = cfg["study"]["display_crs"]
    core_buffer_m = float(cfg["study"]["core_buffer_m"])
    margin_m = float(cfg["study"]["margin_m"])
    
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load selected stations in metric CRS
    stations_gdf = gpd.read_file(stations_path).to_crs(metric_crs)
    if len(stations_gdf) == 0:
        raise ValueError(f"No selected stations found in {stations_path}")
        
    print(f"Generating study area for {len(stations_gdf)} stations...")
    print(f"  Core buffer: {core_buffer_m}m, Build margin: {margin_m}m")
    
    # 2. Buffer each station point by core_buffer_m
    station_buffers = stations_gdf.geometry.buffer(core_buffer_m)
    
    # 3. Union buffers into a single core geometry
    core_geom = station_buffers.union_all()
    core_geom = make_valid(core_geom)
    
    # 4. Buffer core geometry by margin_m for network build area
    build_geom = core_geom.buffer(margin_m)
    build_geom = make_valid(build_geom)
    
    # Create GeoDataFrames in metric CRS
    core_gdf_metric = gpd.GeoDataFrame(
        [{"id": "core", "buffer_m": core_buffer_m, "area_sqkm": core_geom.area / 1e6, "geometry": core_geom}],
        crs=metric_crs
    )
    
    build_gdf_metric = gpd.GeoDataFrame(
        [{"id": "build", "buffer_m": core_buffer_m + margin_m, "area_sqkm": build_geom.area / 1e6, "geometry": build_geom}],
        crs=metric_crs
    )
    
    # Create WGS84 representations for OSMnx queries and display
    core_gdf_wgs84 = core_gdf_metric.to_crs(display_crs)
    build_gdf_wgs84 = build_gdf_metric.to_crs(display_crs)
    
    # Save GPKG files
    core_gdf_metric.to_file(out_dir / "study_area_core.gpkg", driver="GPKG")
    build_gdf_metric.to_file(out_dir / "study_area_build.gpkg", driver="GPKG")
    
    core_gdf_wgs84.to_file(out_dir / "study_area_core_wgs84.gpkg", driver="GPKG")
    build_gdf_wgs84.to_file(out_dir / "study_area_build_wgs84.gpkg", driver="GPKG")
    
    # Bounding boxes in WGS84 (minx, miny, maxx, maxy) -> (min_lon, min_lat, max_lon, max_lat)
    core_bbox = list(core_gdf_wgs84.total_bounds)
    build_bbox = list(build_gdf_wgs84.total_bounds)
    
    summary = {
        "station_count": len(stations_gdf),
        "metric_crs": metric_crs,
        "core_area_sqkm": round(float(core_geom.area / 1e6), 2),
        "build_area_sqkm": round(float(build_geom.area / 1e6), 2),
        "core_bbox_wgs84": [round(b, 6) for b in core_bbox],
        "build_bbox_wgs84": [round(b, 6) for b in build_bbox]
    }
    
    with open(out_dir / "study_area_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print(f"Study areas computed:")
    print(f"  Core Area: {summary['core_area_sqkm']} sq km")
    print(f"  Build Area: {summary['build_area_sqkm']} sq km (includes +{margin_m}m buffer)")
    print(f"  WGS84 Build BBox: {summary['build_bbox_wgs84']}")
    
    return summary


if __name__ == "__main__":
    compute_study_areas()
