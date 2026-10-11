import geopandas as gpd
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
from pathlib import Path

# 1. Load fresh outputs
cells = gpd.read_file("data/output/cells.gpkg")
stations_selected = gpd.read_file("data/interim/stations_selected.gpkg").to_crs("EPSG:32643")
stations_all = gpd.read_file("data/interim/stations_all.gpkg").to_crs("EPSG:32643")
G_bike = ox.load_graphml("data/interim/graph_bike_safe.graphml")
G_walk = ox.load_graphml("data/interim/graph_walk.graphml")

print("================================================================================")
print("DIAGNOSTIC AUDIT 1: SNAP DISTANCE DISTRIBUTION & BARRIER CROSSING")
print("================================================================================")
# Calculate snap distance from cell centroid to its snapped bike node
snap_dists_bike = []
for idx, r in cells.iterrows():
    cx, cy = r.geometry.centroid.x, r.geometry.centroid.y
    nb = int(r["node_bike"])
    nd = G_bike.nodes[nb]
    d = ((cx - float(nd["x"]))**2 + (cy - float(nd["y"]))**2)**0.5
    snap_dists_bike.append(d)

cells["snap_dist_bike_m"] = snap_dists_bike

print("Bike Snap Distance (m) Distribution across all 680 cells:")
print(f"  Min:    {cells['snap_dist_bike_m'].min():.1f} m")
print(f"  25%:    {cells['snap_dist_bike_m'].quantile(0.25):.1f} m")
print(f"  Median: {cells['snap_dist_bike_m'].median():.1f} m")
print(f"  Mean:   {cells['snap_dist_bike_m'].mean():.1f} m")
print(f"  75%:    {cells['snap_dist_bike_m'].quantile(0.75):.1f} m")
print(f"  90%:    {cells['snap_dist_bike_m'].quantile(0.90):.1f} m")
print(f"  95%:    {cells['snap_dist_bike_m'].quantile(0.95):.1f} m")
print(f"  Max:    {cells['snap_dist_bike_m'].max():.1f} m")

# Walk Snap Distance
print("\nWalk Snap Distance (m) Distribution:")
print(f"  Mean:   {cells['snap_dist_m'].mean():.1f} m")
print(f"  Median: {cells['snap_dist_m'].median():.1f} m")
print(f"  90%:    {cells['snap_dist_m'].quantile(0.90):.1f} m")
print(f"  Max:    {cells['snap_dist_m'].max():.1f} m")

# Check if any cell has bike snap distance > 200m
over_200 = cells[cells["snap_dist_bike_m"] > 200]
print(f"\nCells with bike snap distance > 200m: {len(over_200)}")

# Check what drove the +5,812 increase in T=15 e-bike uplift
# Compare with old outputs
old_cells = pd.read_csv("scratch/old_outputs/cells.csv")
merged_cells = cells[["cell_id", "is_corridor_assigned", "walk_time_min", "ebike_time_min", "nearest_station_walk", "population"]].merge(
    old_cells[["cell_id", "ebike_time_min"]].rename(columns={"ebike_time_min": "old_ebike_time_min"}),
    on="cell_id"
)
corr_merged = merged_cells[merged_cells["is_corridor_assigned"] == True]

newly_reached = corr_merged[(corr_merged["ebike_time_min"] <= 15.0) & (corr_merged["old_ebike_time_min"] > 15.0) & (corr_merged["walk_time_min"] > 15.0)]
print(f"\nNewly reached cells at T=15 due to station/cell snapping fix: {len(newly_reached)} cells, {newly_reached['population'].sum():.1f} pop")
print("Breakdown by nearest walk station:")
print(newly_reached["nearest_station_walk"].value_counts())

print("\n================================================================================")
print("DIAGNOSTIC AUDIT 2: FOOTBRIDGE CELL-BY-CELL DISMOUNT AUDIT")
print("================================================================================")
# Audit the 12 cells in the 20-min gap
gap12 = corr_merged[(corr_merged["walk_time_min"] <= 20.0) & (corr_merged["ebike_time_min"] > 20.0)]
print(f"Fresh 20-min gap cells: {len(gap12)} cells, {gap12['population'].sum():.1f} pop")
print("Individual cell details:")
for _, r in gap12.iterrows():
    # If walking bike: walk_time_min is cell-to-station walk time.
    # At 4.0 km/h: walk_t_40 = walk_time_min * (4.5 / 4.0)
    # Plus stairs penalty (2.0 min) + vehicle overhead (5.0 min)
    wt_45 = r["walk_time_min"]
    dismount_t_40 = wt_45 * (4.5 / 4.0) + 2.0 + 5.0
    dismount_t_45 = wt_45 + 2.0 + 5.0
    print(f"  Cell {r['cell_id']} (st={r['nearest_station_walk']}): Pop={r['population']:5.1f} | Walk={wt_45:4.1f}m | Bike_Drive={r['ebike_time_min']:4.1f}m | Dismount@4.0={dismount_t_40:4.1f}m (<=20? {dismount_t_40 <= 20.0}) | Dismount@4.5={dismount_t_45:4.1f}m (<=20? {dismount_t_45 <= 20.0})")

print("\n================================================================================")
print("DIAGNOSTIC AUDIT 3: OVERHEAD SENSITIVITY GRID (3, 5, 7 MIN)")
print("================================================================================")
corr_cells = cells[cells["is_corridor_assigned"] == True]
c_pop = corr_cells["population"].sum()

for ov in [3.0, 5.0, 7.0]:
    # ebike_time with varied overhead: (default_ebike_time - 5.0) + ov
    e_time_ov = np.maximum(0.0, corr_cells["ebike_time_min"] - 5.0) + ov
    a_time_ov = np.maximum(0.0, corr_cells["eauto_time_min"] - 5.0) + ov
    w_time = corr_cells["walk_time_min"]
    
    for t in [15.0, 20.0]:
        w_cov = w_time <= t
        e_cov = e_time_ov <= t
        a_cov = a_time_ov <= t
        
        e_up = e_cov & (~w_cov)
        a_up = a_cov & (~w_cov) & (~e_cov)
        comb = w_cov | e_cov | a_cov
        res = ~comb
        
        w_pop = corr_cells[w_cov]["population"].sum()
        e_pop = corr_cells[e_up]["population"].sum()
        a_pop = corr_cells[a_up]["population"].sum()
        comb_pop = corr_cells[comb]["population"].sum()
        res_pop = corr_cells[res]["population"].sum()
        
        print(f"Overhead={ov:.0f}min | T={t:.0f}min: Walk={w_pop:6,.0f} ({w_pop/c_pop*100:4.1f}%) | E-Bike Up=+{e_pop:6,.0f} (+{e_pop/c_pop*100:4.1f}%) | Walk+Bike={w_pop+e_pop:6,.0f} ({(w_pop+e_pop)/c_pop*100:4.1f}%) | E-Auto Up=+{a_pop:6,.0f} (+{a_pop/c_pop*100:4.1f}%) | Union={comb_pop:6,.0f} ({comb_pop/c_pop*100:4.1f}%)")

print("\n================================================================================")
print("DIAGNOSTIC AUDIT 4: TOP 5 HUBS COORDINATES COMPARISON (OLD VS NEW)")
print("================================================================================")
old_selected = pd.read_csv("scratch/old_outputs/selected_sites.csv")
old_sites = pd.read_csv("scratch/old_outputs/candidate_sites.csv")
new_selected = pd.read_csv("data/output/selected_sites.csv")
new_sites = pd.read_csv("data/output/candidate_sites.csv")

old_top5 = old_selected.head(5).merge(old_sites, on="site_id")
new_top5 = new_selected.head(5).merge(new_sites, on="site_id")

print("Old Top 5 Hubs (k=1..5):")
for _, r in old_top5.iterrows():
    print(f"  k={r['k']}: {r['site_id']} | gain={r['marginal_gain']:6.1f} | st={r['nearest_station']} | lat={r['lat']:.5f}, lon={r['lon']:.5f}")

print("\nNew Top 5 Hubs (k=1..5):")
for _, r in new_top5.iterrows():
    print(f"  k={r['k']}: {r['site_id']} | gain={r['marginal_gain']:6.1f} | st={r['nearest_station']} | lat={r['lat']:.5f}, lon={r['lon']:.5f}")

print("\nDistance from each new hub to closest old hub:")
for _, nr in new_top5.iterrows():
    dists = []
    for _, orow in old_top5.iterrows():
        # approx distance in meters
        d = ((float(nr['lat']) - float(orow['lat']))**2 + (float(nr['lon']) - float(orow['lon']))**2)**0.5 * 111000.0
        dists.append((orow['site_id'], orow['k'], d))
    dists.sort(key=lambda x: x[2])
    print(f"  New k={nr['k']} ({nr['site_id']}) -> closest Old hub is k={dists[0][1]} ({dists[0][0]}) at {dists[0][2]:.1f} m")
