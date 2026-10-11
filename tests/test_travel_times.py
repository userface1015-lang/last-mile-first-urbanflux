"""
test_travel_times.py - Unit tests for catchments, travel times, and uplift calculations.
"""

from pathlib import Path
import json
import pandas as pd
import geopandas as gpd


def test_catchment_outputs_exist():
    out_dir = Path("data/output")
    assert (out_dir / "cells.csv").exists()
    assert (out_dir / "cells.gpkg").exists()
    assert (out_dir / "catchment_metrics.json").exists()


def test_catchment_logic_and_uplift():
    df = pd.read_csv("data/output/cells.csv")
    assert len(df) == 680
    
    # Check that contract columns exist
    expected_cols = [
        "cell_id", "population", "walk_time_min", "ebike_time_min", "eauto_time_min",
        "walk_covered", "ebike_covered", "eauto_covered",
        "ebike_uplift", "eauto_uplift", "combined_covered", "combined_time_min", "residual"
    ]
    for col in expected_cols:
        assert col in df.columns
        
    # Check uplift mutually exclusive logic
    # ebike_uplift must be ebike_covered AND NOT walk_covered
    assert (df[df["ebike_uplift"]]["walk_covered"] == False).all()
    
    # eauto_uplift must be eauto_covered AND NOT walk_covered AND NOT ebike_covered
    assert (df[df["eauto_uplift"]]["walk_covered"] == False).all()
    assert (df[df["eauto_uplift"]]["ebike_covered"] == False).all()
    
    # Combined covered must equal sum of walk, ebike_uplift, and eauto_uplift
    combined_check = df["walk_covered"] | df["ebike_uplift"] | df["eauto_uplift"]
    assert (df["combined_covered"] == combined_check).all()
    
    # Residual must be opposite of combined_covered
    assert (df["residual"] == ~df["combined_covered"]).all()


def test_metrics_json():
    with open("data/output/catchment_metrics.json", "r") as f:
        metrics = json.load(f)
        
    assert metrics["total_population"] > 500000
    assert metrics["walk_covered_pop"] > 0
    assert metrics["ebike_uplift_pop"] > 0
    assert metrics["combined_covered_pop"] == metrics["walk_covered_pop"] + metrics["ebike_uplift_pop"] + metrics["eauto_uplift_pop"]


def test_population_conservation():
    """Verify total population conservation across corridor and boundary absorptions."""
    df = pd.read_csv("data/output/cells.csv")
    total_pop = df["population"].sum()
    assert round(total_pop, 0) == 562035.0
    
    # Check corridor + context partition
    corridor_cells = df[df["is_corridor_assigned"] == True]
    context_cells = df[df["is_corridor_assigned"] == False]
    assert len(corridor_cells) + len(context_cells) == len(df)
    assert round(corridor_cells["population"].sum() + context_cells["population"].sum(), 0) == 562035.0
    assert round(corridor_cells["population"].sum(), 0) == 453687.0
    assert round(context_cells["population"].sum(), 0) == 108348.0
    
    # Check mutually exclusive partition sums to total
    partition_sum = (
        corridor_cells[corridor_cells["walk_covered"]]["population"].sum()
        + corridor_cells[corridor_cells["ebike_uplift"]]["population"].sum()
        + corridor_cells[corridor_cells["eauto_uplift"]]["population"].sum()
        + corridor_cells[corridor_cells["residual"]]["population"].sum()
    )
    assert round(partition_sum, 0) == 453687.0


def test_reachability_snapping_integrity():
    """Verify that stations and cells avoid 0-degree disconnected stubs."""
    import osmnx as ox
    import networkx as nx
    G_bike = ox.load_graphml("data/interim/graph_bike_safe.graphml")
    for _, _, _, d in G_bike.edges(keys=True, data=True):
        d["time_min"] = float(d["time_min"])
    G_rev = G_bike.reverse(copy=True)
    
    # Verify pilot stations on G_bike have high incoming reach (>1000 nodes)
    st = gpd.read_file("data/interim/stations_selected.gpkg")
    from src.travel_times import snap_nodes_reachability_aware
    st_nodes = snap_nodes_reachability_aware(G_bike, st.geometry.x.values, st.geometry.y.values)
    for n, sname in zip(st_nodes, st["name"]):
        reach = len(nx.single_source_dijkstra_path_length(G_rev, n, weight="time_min"))
        assert reach >= 1000, f"Station {sname} snapped to disconnected stub (reach={reach})"
        
    # Verify no cell in cells.csv snapped to an out-degree 0 dead-end
    cells = pd.read_csv("data/output/cells.csv")
    for nb in cells["node_bike"].unique():
        assert G_bike.out_degree(nb) > 0, f"Cell node {nb} has out_degree 0 (cannot leave by bike)"


def test_snap_distance_integrity():
    """Verify that cell snapping distances are within physical limits and well within 500m."""
    cells = pd.read_csv("data/output/cells.csv")
    if "snap_dist_bike_m" in cells.columns:
        mean_bike_snap = cells["snap_dist_bike_m"].mean()
        max_bike_snap = cells["snap_dist_bike_m"].max()
        assert 70.0 <= mean_bike_snap <= 100.0, f"Mean bike snap distance unexpected: {mean_bike_snap}"
        assert max_bike_snap < 500.0, f"Max bike snap distance exceeded physical cap (500m): {max_bike_snap}"
