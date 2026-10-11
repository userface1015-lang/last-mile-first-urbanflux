"""
export_T20_hub_results.py - Computes and exports coverage pairs and greedy hub selection for T = 20 min.
Matches the WRI STAMP 20-minute threshold benchmark.
Outputs:
- data/output/coverage_pairs_T20.csv
- data/output/selected_sites_T20.csv
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import pandas as pd
import networkx as nx
import osmnx as ox

from src.optimizer import compute_coverage_pairs, run_greedy_max_coverage

def export_T20_results():
    out_dir = Path("data/output")
    
    # 1. Load graphs and data
    G_walk = ox.load_graphml("data/interim/graph_walk.graphml")
    for _, _, _, d in G_walk.edges(keys=True, data=True):
        d["time_min"] = float(d["time_min"])
        
    sites = gpd.read_file(out_dir / "candidate_sites.gpkg")
    cells = gpd.read_file(out_dir / "cells.gpkg")
    
    corr_cells = cells[cells["is_corridor_assigned"] == True]
    w_base_20 = corr_cells[corr_cells["walk_time_min"] <= 20.0]["population"].sum()
    
    print("================================================================================")
    print("COMPUTING T = 20 MIN HUB COVERAGE PAIRS AND GREEDY SELECTION")
    print(f"Walk baseline at T = 20 min: {w_base_20:,.1f} residents")
    print("================================================================================")
    
    # 2. Compute coverage pairs at T = 20 min
    pairs_T20 = compute_coverage_pairs(
        G_walk, sites, cells,
        threshold_T=20.0,
        overhead_min=5.0,
        max_walk_to_site_min=5.0,
        walk_speed_kmh=4.5
    )
    pairs_path = out_dir / "coverage_pairs_T20.csv"
    pairs_T20.to_csv(pairs_path, index=False)
    print(f"Generated {len(pairs_T20)} coverage pairs at T = 20 min -> saved to {pairs_path}")
    
    # 3. Run greedy max-coverage for k = 1 to 15
    selected_T20 = run_greedy_max_coverage(
        sites, pairs_T20, cells,
        k_max=15,
        baseline_walk_covered_pop=w_base_20
    )
    sel_path = out_dir / "selected_sites_T20.csv"
    selected_T20.to_csv(sel_path, index=False)
    print(f"Greedy selection completed -> saved to {sel_path}")
    
    print("\nTop 5 Feeder Hubs at T = 20 min:")
    print(selected_T20.head(5)[["k", "site_id", "marginal_gain", "cumulative_feeder_pop", "coverage_after"]].to_string(index=False))
    print(f"\nTotal 5-Hub Marginal Uplift at T = 20 min: +{selected_T20.head(5)['marginal_gain'].sum():,.1f} residents")

if __name__ == "__main__":
    export_T20_results()
