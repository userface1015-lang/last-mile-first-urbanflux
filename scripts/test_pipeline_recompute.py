import time
from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nx
from shapely.geometry import Point

# 1. Load graphs
print("Loading road graphs...")
G_walk = ox.load_graphml("data/interim/graph_walk.graphml")
G_bike = ox.load_graphml("data/interim/graph_bike_safe.graphml")
G_drive = ox.load_graphml("data/interim/graph_drive.graphml")

for G in [G_walk, G_bike, G_drive]:
    for _, _, _, d in G.edges(keys=True, data=True):
        d["time_min"] = float(d["time_min"])
        d["length"] = float(d.get("length", 1.0))

G_rev_bike = G_bike.reverse(copy=True)
G_rev_drive = G_drive.reverse(copy=True)
G_rev_walk = G_walk.reverse(copy=True)

# 2. Load stations
st_pilot = gpd.read_file("data/interim/stations_selected.gpkg").to_crs("EPSG:32643")
st_pilot["is_context"] = False
st_all = gpd.read_file("data/interim/stations_all.gpkg").to_crs("EPSG:32643")
ctx_names = ["Singayyanapalya", "Krishnarajapura"]
ctx = st_all[st_all["name"].isin(ctx_names)].copy()
ctx["station_id"] = [f"CTX_{i+1:02d}" for i in range(len(ctx))]
ctx["is_context"] = True
stations = pd.concat([st_pilot, ctx], ignore_index=True)

print(f"Loaded {len(stations)} stations ({len(st_pilot)} pilot + {len(ctx)} context)")

# Helper for reachability-aware station snapping
def snap_station_robust(G, G_rev, sx, sy, min_reach=1000, max_dist=200.0):
    default_n, d = ox.distance.nearest_nodes(G, sx, sy, return_dist=True)
    reach = len(nx.single_source_dijkstra_path_length(G_rev, default_n, weight="time_min"))
    if reach >= min_reach:
        return default_n, d, reach
    
    # Search nearby nodes
    candidates = []
    for n, data in G.nodes(data=True):
        dist = ((float(data["x"]) - sx)**2 + (float(data["y"]) - sy)**2)**0.5
        if dist <= max_dist:
            r = len(nx.single_source_dijkstra_path_length(G_rev, n, weight="time_min"))
            candidates.append((n, dist, r))
    if not candidates:
        return default_n, d, reach
    candidates.sort(key=lambda x: (-(x[2] >= min_reach), x[1]))
    return candidates[0][0], candidates[0][1], candidates[0][2]

st_nodes_walk = []
st_nodes_bike = []
st_nodes_drive = []

print("\nStation Snapping:")
for _, r in stations.iterrows():
    sx, sy = r.geometry.x, r.geometry.y
    nw, dw, rw = snap_station_robust(G_walk, G_rev_walk, sx, sy, min_reach=1000)
    nb, db, rb = snap_station_robust(G_bike, G_rev_bike, sx, sy, min_reach=1000)
    nd, dd, rd = snap_station_robust(G_drive, G_rev_drive, sx, sy, min_reach=1000)
    st_nodes_walk.append(nw)
    st_nodes_bike.append(nb)
    st_nodes_drive.append(nd)
    print(f"  {r['name']} ({r['station_id']}): bike node={nb} (dist={db:.1f}m, reach={rb}), walk node={nw} (dist={dw:.1f}m)")

# Load cells
cells_gdf = gpd.read_file("data/output/cells.gpkg")
cell_xs = cells_gdf.geometry.centroid.x.values
cell_ys = cells_gdf.geometry.centroid.y.values

# Robust cell snapping for bike (avoid 0-out-degree)
cell_nodes_walk = ox.distance.nearest_nodes(G_walk, cell_xs, cell_ys)
cell_nodes_drive = ox.distance.nearest_nodes(G_drive, cell_xs, cell_ys)

raw_cell_nodes_bike = ox.distance.nearest_nodes(G_bike, cell_xs, cell_ys)
cell_nodes_bike = []
fixed_deadends = 0
for cx, cy, nb in zip(cell_xs, cell_ys, raw_cell_nodes_bike):
    if G_bike.out_degree(nb) == 0:
        # find nearest node with out_degree > 0
        fixed_deadends += 1
        cands = []
        for n, data in G_bike.nodes(data=True):
            dist = ((float(data["x"]) - cx)**2 + (float(data["y"]) - cy)**2)**0.5
            if dist <= 150.0 and G_bike.out_degree(n) > 0:
                cands.append((n, dist))
        if cands:
            cands.sort(key=lambda x: x[1])
            cell_nodes_bike.append(cands[0][0])
        else:
            cell_nodes_bike.append(nb)
    else:
        cell_nodes_bike.append(nb)

print(f"\nFixed {fixed_deadends} cell nodes that originally snapped to 0-out-degree dead-ends.")

# Compute Dijkstra
from src.travel_times import compute_multi_source_times, get_meters_per_minute

st_ids = stations["station_id"].tolist()
t0 = time.time()
walk_times, walk_nearest_st = compute_multi_source_times(G_walk, st_nodes_walk, st_ids)
bike_times, bike_nearest_st = compute_multi_source_times(G_bike, st_nodes_bike, st_ids)
drive_times, drive_nearest_st = compute_multi_source_times(G_drive, st_nodes_drive, st_ids)
print(f"Dijkstras computed in {time.time() - t0:.2f}s")

walk_m_per_min = 4500.0 / 60.0
ebike_overhead = 5.0
eauto_overhead = 5.0

snap_dists_m = cells_gdf["snap_dist_m"].values

w_times = []
b_times = []
d_times = []
w_st = []
b_st = []
d_st = []

for i in range(len(cells_gdf)):
    nw = cell_nodes_walk[i]
    nb = cell_nodes_bike[i]
    nd = cell_nodes_drive[i]
    snap_t = snap_dists_m[i] / walk_m_per_min
    
    tw = round(walk_times[nw] + snap_t, 2) if nw in walk_times else 999.0
    sw = walk_nearest_st.get(nw, None)
    
    tb = round(bike_times[nb] + snap_t + ebike_overhead, 2) if nb in bike_times else 999.0
    sb = bike_nearest_st.get(nb, None)
    
    td = round(drive_times[nd] + snap_t + eauto_overhead, 2) if nd in drive_times else 999.0
    sd = drive_nearest_st.get(nd, None)
    
    w_times.append(tw)
    b_times.append(tb)
    d_times.append(td)
    w_st.append(sw)
    b_st.append(sb)
    d_st.append(sd)

cells_gdf["walk_time_min"] = w_times
cells_gdf["ebike_time_min"] = b_times
cells_gdf["eauto_time_min"] = d_times
cells_gdf["nearest_station_walk"] = w_st
cells_gdf["nearest_station_ebike"] = b_st
cells_gdf["nearest_station_eauto"] = d_st
cells_gdf["is_corridor_assigned"] = ~cells_gdf["nearest_station_walk"].astype(str).str.startswith("CTX_")

# Print metrics at T=15 and T=20
for t in [15.0, 20.0]:
    print(f"\n=================== T = {t} MIN ===================")
    corr = cells_gdf[cells_gdf["is_corridor_assigned"] == True]
    c_tot = corr["population"].sum()
    
    cw = corr[corr["walk_time_min"] <= t]["population"].sum()
    ce = corr[(corr["ebike_time_min"] <= t) & (~(corr["walk_time_min"] <= t))]["population"].sum()
    ca = corr[(corr["eauto_time_min"] <= t) & (~(corr["walk_time_min"] <= t)) & (~(corr["ebike_time_min"] <= t))]["population"].sum()
    cc = corr[(corr["walk_time_min"] <= t) | (corr["ebike_time_min"] <= t) | (corr["eauto_time_min"] <= t)]["population"].sum()
    cr = c_tot - cc
    
    print(f"CORE CORRIDOR ({c_tot:,.0f} pop):")
    print(f"  1. Walk Catchment:        {cw:10,.0f} ({cw/c_tot*100:5.1f}%)")
    print(f"  2. Safe E-Bike Uplift:    {ce:10,.0f} ({ce/c_tot*100:5.1f}%)")
    print(f"     Total Walk + E-Bike:   {cw+ce:10,.0f} ({(cw+ce)/c_tot*100:5.1f}%)")
    print(f"  3. E-Auto Extra Uplift:   {ca:10,.0f} ({ca/c_tot*100:5.1f}%)")
    print(f"  Total Multi-Modal Union:  {cc:10,.0f} ({cc/c_tot*100:5.1f}%)")
    print(f"  Residual Unserved Gap:    {cr:10,.0f} ({cr/c_tot*100:5.1f}%)")

# Check 20-min walk vs ebike gap
gap_20 = corr[(corr["walk_time_min"] <= 20) & (corr["ebike_time_min"] > 20)]
print(f"\nRemaining gap in Core Corridor (walk<=20 & ebike>20): {len(gap_20)} cells, {gap_20['population'].sum():.1f} pop")
print(gap_20[["cell_id", "walk_time_min", "ebike_time_min", "nearest_station_walk", "population"]])
