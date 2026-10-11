import geopandas as gpd
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
from pathlib import Path

# Load graphs
G_walk = ox.load_graphml("data/interim/graph_walk.graphml")
G_bike = ox.load_graphml("data/interim/graph_bike_safe.graphml")

for G in [G_walk, G_bike]:
    for _, _, _, d in G.edges(keys=True, data=True):
        d["time_min"] = float(d["time_min"])
        d["length"] = float(d.get("length", 1.0))

from src.optimizer import generate_candidate_sites, compute_coverage_pairs, run_greedy_max_coverage, rank_stations

# Load updated cells from test run
cells_gdf = gpd.read_file("data/output/cells.gpkg")
# Note: we need to use the newly computed cells from our test
from scripts.test_pipeline_recompute import *

print("\n--- Running Optimizer on Recomputed Snapped Cells ---")
stations_pilot = gpd.read_file("data/interim/stations_selected.gpkg").to_crs("EPSG:32643")

# S12: Candidate Sites
sites_gdf, bike_ride_time, _ = generate_candidate_sites(
    G_bike, G_walk, stations_pilot, spacing_m=120.0, metric_crs="EPSG:32643"
)
print(f"Total candidate sites: {len(sites_gdf)}")

# Filter target cells to strictly unserved cells in the Core Corridor!
target_cells = cells_gdf[(cells_gdf["walk_covered"] == False) & (cells_gdf["is_corridor_assigned"] == True)].copy()
print(f"Core corridor unserved cells: {len(target_cells)} with population {target_cells['population'].sum():,.0f}")

# Compute coverage pairs
pairs_df_15 = compute_coverage_pairs(
    G_walk, sites_gdf, cells_gdf[cells_gdf["is_corridor_assigned"] == True],
    threshold_T=15.0, overhead_min=5.0, max_walk_to_site_min=5.0, walk_speed_kmh=4.5
)
print(f"T=15 sparse coverage pairs: {len(pairs_df_15)}")

walk_baseline_pop = cells_gdf[(cells_gdf["walk_covered"] == True) & (cells_gdf["is_corridor_assigned"] == True)]["population"].sum()
selected_15 = run_greedy_max_coverage(sites_gdf, pairs_df_15, cells_gdf, k_max=15, baseline_walk_covered_pop=walk_baseline_pop)

print("\nTop 5 Hub Sites at T = 15 min:")
print(selected_15.head(5)[["k", "site_id", "marginal_gain", "cumulative_feeder_pop", "coverage_after"]])

# At T = 20 min
pairs_df_20 = compute_coverage_pairs(
    G_walk, sites_gdf, cells_gdf[cells_gdf["is_corridor_assigned"] == True],
    threshold_T=20.0, overhead_min=5.0, max_walk_to_site_min=5.0, walk_speed_kmh=4.5
)
print(f"T=20 sparse coverage pairs: {len(pairs_df_20)}")
walk_baseline_pop_20 = cells_gdf[(cells_gdf["walk_time_min"] <= 20.0) & (cells_gdf["is_corridor_assigned"] == True)]["population"].sum()
selected_20 = run_greedy_max_coverage(sites_gdf, pairs_df_20, cells_gdf, k_max=15, baseline_walk_covered_pop=walk_baseline_pop_20)

print("\nTop 5 Hub Sites at T = 20 min:")
print(selected_20.head(5)[["k", "site_id", "marginal_gain", "cumulative_feeder_pop", "coverage_after"]])
