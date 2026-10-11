"""
test_stations.py - Unit tests for Step S3 station cleaning and network/pilot selection.
Asserts 83 operational stations across Bengaluru (63 GPKG + 20 OSM), no duplicates,
valid coordinates, and ridership matched for all stations.
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
from src.stations import clean_stations, export_station_tables


def test_clean_stations():
    all_gdf, pilot_gdf = clean_stations()
    
    # 1. Total counts: assert 83 operational stations, no duplicates
    assert len(all_gdf) == 83
    assert all_gdf["name"].nunique() == 83
    assert all_gdf["station_id"].nunique() == 83
    assert len(pilot_gdf) == 10
    
    # 2. CRS check
    assert str(all_gdf.crs) == "EPSG:32643"
    assert str(pilot_gdf.crs) == "EPSG:32643"
    
    # 3. Contract columns
    expected_cols = [
        "station_id", "name", "source", "lon", "lat", "node_walk", "node_bike",
        "snap_dist_walk_m", "snap_dist_bike_m", "days_of_data", "total_boardings",
        "ridership", "include_flag", "geometry"
    ]
    for col in expected_cols:
        assert col in all_gdf.columns
        
    # 4. Valid coordinates and ridership matched for all 83 stations
    for _, st in all_gdf.iterrows():
        assert 77.0 <= st["lon"] <= 78.5, f"Invalid lon for {st['name']}: {st['lon']}"
        assert 12.0 <= st["lat"] <= 13.5, f"Invalid lat for {st['name']}: {st['lat']}"
        assert pd.notna(st["ridership"]), f"Missing ridership for {st['name']}"
        assert st["ridership"] > 0, f"Non-positive ridership for {st['name']}: {st['ridership']}"
        assert pd.notna(st["days_of_data"])
        assert st["days_of_data"] > 0


def test_export_station_tables(tmp_path):
    export_station_tables(output_dir=tmp_path, network_dir=tmp_path / "network")
    assert (tmp_path / "stations_all.csv").exists()
    assert (tmp_path / "stations_pilot.csv").exists()
    assert (tmp_path / "stations_all.gpkg").exists()
    assert (tmp_path / "stations_pilot.gpkg").exists()
    assert (tmp_path / "network" / "stations_83_network.csv").exists()
    assert (tmp_path / "network" / "stations_83_network.gpkg").exists()
    
    df_all = pd.read_csv(tmp_path / "stations_all.csv")
    assert len(df_all) == 83
    assert df_all["ridership"].notna().sum() == 83
    
    df_pilot = pd.read_csv(tmp_path / "stations_pilot.csv")
    assert len(df_pilot) == 10
    assert df_pilot["ridership"].notna().sum() == 10
