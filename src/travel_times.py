"""
travel_times.py - Steps S6, S7, S8, S9:
Generates H3 grid, calculates zonal population, snaps cells/stations to road networks,
computes multi-source shortest travel times to nearest station for Walk, E-Bike, and E-Auto,
and produces distinct per-mode catchments, the combined union catchment, and the micromobility uplift.
"""

from pathlib import Path
from typing import Dict, Tuple, List
import json
import time

import h3
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, Point
from rasterstats import zonal_stats
import osmnx as ox
import networkx as nx

from src.config import load_config, get_meters_per_minute


def generate_h3_grid_with_population(
    core_poly_path: str | Path = "data/interim/study_area_core_wgs84.gpkg",
    raster_path: str | Path = "data/interim/worldpop_study_area.tif",
    h3_res: int = 9,
    metric_crs: str = "EPSG:32643"
) -> gpd.GeoDataFrame:
    """
    Generates H3 resolution 9 hexagons covering the core area and computes
    zonal population sums from the clipped WorldPop raster.
    """
    core_gdf = gpd.read_file(core_poly_path)
    core_geom = core_gdf.geometry.iloc[0]
    
    # 1. Fill polygon with H3 cells
    cell_ids = list(h3.geo_to_cells(core_geom, h3_res))
    print(f"Generated {len(cell_ids)} H3 cells at resolution {h3_res}...")
    
    # 2. Convert H3 cells to Shapely polygons in WGS84 (lon, lat)
    polys_wgs84 = []
    centroids_wgs84 = []
    
    for cid in cell_ids:
        # h3.cell_to_boundary returns (lat, lng)
        coords = h3.cell_to_boundary(cid)
        # Shapely expects (lng, lat)
        poly = Polygon([(pt[1], pt[0]) for pt in coords])
        polys_wgs84.append(poly)
        
        c_lat, c_lng = h3.cell_to_latlng(cid)
        centroids_wgs84.append(Point(c_lng, c_lat))
        
    gdf_wgs84 = gpd.GeoDataFrame(
        {"cell_id": cell_ids, "geometry": polys_wgs84, "centroid_wgs84": centroids_wgs84},
        crs="EPSG:4326"
    )
    
    # 3. Zonal stats population calculation
    print(f"Calculating zonal population from {raster_path}...")
    stats = zonal_stats(gdf_wgs84.geometry, raster_path, stats=["sum"], nodata=-99999.0)
    gdf_wgs84["population"] = [round(float(s["sum"]), 1) if s["sum"] is not None and s["sum"] > 0 else 0.0 for s in stats]
    
    # 4. Project centroids to metric CRS for accurate snapping
    centroids_gdf = gpd.GeoDataFrame(
        {"cell_id": cell_ids, "geometry": centroids_wgs84},
        crs="EPSG:4326"
    ).to_crs(metric_crs)
    
    gdf_wgs84["centroid_x"] = centroids_gdf.geometry.x.values
    gdf_wgs84["centroid_y"] = centroids_gdf.geometry.y.values
    
    print(f"H3 grid complete: {len(gdf_wgs84)} cells, Total Population = {gdf_wgs84['population'].sum():,.0f}")
    return gdf_wgs84


def compute_multi_source_times(
    G: nx.MultiDiGraph,
    station_nodes: list,
    station_ids: list,
    weight_attr: str = "time_min"
) -> Tuple[Dict[int, float], Dict[int, str]]:
    """
    Computes shortest time from every reachable node to its nearest station
    along the reversed graph, recording both shortest time and nearest station ID.
    """
    # Ensure weight is float
    for _, _, _, data in G.edges(keys=True, data=True):
        data[weight_attr] = float(data[weight_attr])
        
    G_rev = G.reverse(copy=True)
    
    node_min_time: Dict[int, float] = {}
    node_nearest_st: Dict[int, str] = {}
    
    for st_id, st_node in zip(station_ids, station_nodes):
        # Dijkstra outward from station on reversed graph gives time TO station
        dists = nx.single_source_dijkstra_path_length(G_rev, st_node, weight=weight_attr)
        for node, t in dists.items():
            if node not in node_min_time or t < node_min_time[node]:
                node_min_time[node] = t
                node_nearest_st[node] = st_id
                
    return node_min_time, node_nearest_st


def snap_nodes_reachability_aware(
    G: nx.MultiDiGraph,
    xs: np.ndarray,
    ys: np.ndarray,
    min_reach: int = 1000,
    max_search_m: float = 250.0
) -> List[int]:
    """
    Snaps coordinates to nearest nodes on a directed road network, ensuring
    the snapped node has sufficient incoming reachability (in G.reverse())
    to avoid dead-end stubs, one-way traps, or disconnected spurs.
    """
    G_rev = G.reverse(copy=True)
    for _, _, _, d in G_rev.edges(keys=True, data=True):
        d["time_min"] = float(d["time_min"])
    nearest = ox.distance.nearest_nodes(G, xs, ys)
    snapped = []
    for x, y, n in zip(xs, ys, nearest):
        reach = len(nx.single_source_dijkstra_path_length(G_rev, n, weight="time_min"))
        if reach >= min_reach:
            snapped.append(int(n))
        else:
            candidates = []
            for cand_n, data in G.nodes(data=True):
                dist = ((float(data["x"]) - x)**2 + (float(data["y"]) - y)**2)**0.5
                if dist <= max_search_m:
                    r = len(nx.single_source_dijkstra_path_length(G_rev, cand_n, weight="time_min"))
                    candidates.append((cand_n, dist, r))
            if candidates:
                candidates.sort(key=lambda item: (-(item[2] >= min_reach), item[1]))
                snapped.append(int(candidates[0][0]))
            else:
                snapped.append(int(n))
    return snapped


def build_catchments_and_uplift(
    config_path: str | Path = "config/params.yaml",
    stations_path: str | Path = "data/interim/stations_selected.gpkg",
    output_dir: str | Path = "data/output"
) -> gpd.GeoDataFrame:
    """
    Executes full multi-modal travel time calculations and generates separate
    and combined catchments and micromobility uplift metrics.
    """
    cfg = load_config(config_path)
    metric_crs = cfg["study"]["metric_crs"]
    speeds = cfg["speeds_kmh"]
    overheads = cfg["overhead_min"]
    threshold_T = float(cfg["thresholds"]["T_min"])
    
    walk_m_per_min = get_meters_per_minute(speeds["walk"])
    ebike_overhead = float(overheads.get("ebike", 5.0))
    eauto_overhead = float(overheads.get("eauto", 5.0))
    
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    interim_dir = Path("data/interim")
    
    # 1. Generate H3 grid with population
    cells_gdf = generate_h3_grid_with_population(
        core_poly_path="data/interim/study_area_core_wgs84.gpkg",
        raster_path="data/interim/worldpop_study_area.tif",
        h3_res=cfg["grid"]["h3_resolution"],
        metric_crs=metric_crs
    )
    
    # 2. Load stations
    stations_gdf = gpd.read_file(stations_path).to_crs(metric_crs)
    stations_gdf["is_context"] = False

    # Load context boundary stations to absorb boundary loads if configured
    context_station_names = cfg.get("study", {}).get("stations_context", [])
    if context_station_names:
        stations_all = gpd.read_file(interim_dir / "stations_all.gpkg").to_crs(metric_crs)
        ctx_gdf = stations_all[stations_all["name"].isin(context_station_names)].copy()
        ctx_gdf["station_id"] = [f"CTX_{i+1:02d}" for i in range(len(ctx_gdf))]
        ctx_gdf["is_context"] = True
        all_routing_stations = pd.concat([stations_gdf, ctx_gdf], ignore_index=True)
        print(f"Added {len(ctx_gdf)} context boundary stations to absorb edge effects: {context_station_names}")
    else:
        all_routing_stations = stations_gdf

    st_xs = all_routing_stations.geometry.x.values
    st_ys = all_routing_stations.geometry.y.values
    st_ids = all_routing_stations["station_id"].tolist()
    
    # 3. Load graphs
    print("\n--- Loading Road Graphs ---")
    G_walk = ox.load_graphml(interim_dir / "graph_walk.graphml")
    G_bike = ox.load_graphml(interim_dir / "graph_bike_safe.graphml")
    G_drive = ox.load_graphml(interim_dir / "graph_drive.graphml")
    for G in [G_walk, G_bike, G_drive]:
        for _, _, _, d in G.edges(keys=True, data=True):
            d["time_min"] = float(d["time_min"])
            d["length"] = float(d.get("length", 1.0))
    
    # 4. Snap stations to graphs (reachability-aware)
    print("\n--- Snapping Stations to Road Networks ---")
    st_nodes_walk = ox.distance.nearest_nodes(G_walk, st_xs, st_ys)
    st_nodes_bike = snap_nodes_reachability_aware(G_bike, st_xs, st_ys, min_reach=1000)
    st_nodes_drive = snap_nodes_reachability_aware(G_drive, st_xs, st_ys, min_reach=1000)
    
    # Calculate station snap distances (in meters) and snap travel times (in minutes)
    st_snap_dists_walk_m = [
        ((sx - float(G_walk.nodes[n]["x"]))**2 + (sy - float(G_walk.nodes[n]["y"]))**2)**0.5
        for sx, sy, n in zip(st_xs, st_ys, st_nodes_walk)
    ]
    st_snap_dists_bike_m = [
        ((sx - float(G_bike.nodes[n]["x"]))**2 + (sy - float(G_bike.nodes[n]["y"]))**2)**0.5
        for sx, sy, n in zip(st_xs, st_ys, st_nodes_bike)
    ]
    st_snap_dists_drive_m = [
        ((sx - float(G_drive.nodes[n]["x"]))**2 + (sy - float(G_drive.nodes[n]["y"]))**2)**0.5
        for sx, sy, n in zip(st_xs, st_ys, st_nodes_drive)
    ]

    ebike_m_per_min = speeds["ebike"] * 1000.0 / 60.0
    eauto_m_per_min = speeds["eauto"] * 1000.0 / 60.0

    st_snap_times_walk = {sid: d / walk_m_per_min for sid, d in zip(st_ids, st_snap_dists_walk_m)}
    st_snap_times_bike = {sid: d / ebike_m_per_min for sid, d in zip(st_ids, st_snap_dists_bike_m)}
    st_snap_times_drive = {sid: d / eauto_m_per_min for sid, d in zip(st_ids, st_snap_dists_drive_m)}

    
    # 5. Snap cells to graphs
    cell_xs = cells_gdf["centroid_x"].values
    cell_ys = cells_gdf["centroid_y"].values
    
    print("\n--- Snapping H3 Cells to Road Networks ---")
    cell_nodes_walk = ox.distance.nearest_nodes(G_walk, cell_xs, cell_ys)
    cell_nodes_drive = ox.distance.nearest_nodes(G_drive, cell_xs, cell_ys)
    raw_cell_nodes_bike = ox.distance.nearest_nodes(G_bike, cell_xs, cell_ys)

    # Snap bike cells to nearest node that has out_degree > 0 (can exit by bike)
    valid_bike_nodes = [n for n in G_bike.nodes if G_bike.out_degree(n) > 0]
    G_bike_valid = G_bike.subgraph(valid_bike_nodes)
    cell_nodes_bike = ox.distance.nearest_nodes(G_bike_valid, cell_xs, cell_ys)
    
    # Calculate snap distances (in meters) to road graphs
    snap_dists_walk_m = []
    for cx, cy, n in zip(cell_xs, cell_ys, cell_nodes_walk):
        nd = G_walk.nodes[n]
        d = ((cx - float(nd["x"]))**2 + (cy - float(nd["y"]))**2)**0.5
        snap_dists_walk_m.append(d)
        
    snap_dists_bike_m = []
    for cx, cy, n in zip(cell_xs, cell_ys, cell_nodes_bike):
        nd = G_bike.nodes[n]
        d = ((cx - float(nd["x"]))**2 + (cy - float(nd["y"]))**2)**0.5
        snap_dists_bike_m.append(d)
        
    snap_dists_drive_m = []
    for cx, cy, n in zip(cell_xs, cell_ys, cell_nodes_drive):
        nd = G_drive.nodes[n]
        d = ((cx - float(nd["x"]))**2 + (cy - float(nd["y"]))**2)**0.5
        snap_dists_drive_m.append(d)

    cells_gdf["snap_dist_m"] = snap_dists_walk_m
    cells_gdf["snap_dist_walk_m"] = snap_dists_walk_m
    cells_gdf["snap_dist_bike_m"] = snap_dists_bike_m
    cells_gdf["snap_dist_drive_m"] = snap_dists_drive_m
    cells_gdf["node_walk"] = [int(n) for n in cell_nodes_walk]
    cells_gdf["node_bike"] = [int(n) for n in cell_nodes_bike]
    cells_gdf["node_drive"] = [int(n) for n in cell_nodes_drive]

    print(f"  Walk Snap Distance: mean={np.mean(snap_dists_walk_m):.1f}m, median={np.median(snap_dists_walk_m):.1f}m, max={np.max(snap_dists_walk_m):.1f}m")
    print(f"  Bike Snap Distance: mean={np.mean(snap_dists_bike_m):.1f}m, median={np.median(snap_dists_bike_m):.1f}m, max={np.max(snap_dists_bike_m):.1f}m")
    print(f"  Drive Snap Distance: mean={np.mean(snap_dists_drive_m):.1f}m, median={np.median(snap_dists_drive_m):.1f}m, max={np.max(snap_dists_drive_m):.1f}m")
    
    # 6. Compute multi-source shortest path travel times
    print("\n--- Computing Multi-Source Shortest Travel Times ---")
    
    t0 = time.time()
    walk_times, walk_nearest_st = compute_multi_source_times(G_walk, st_nodes_walk, st_ids)
    print(f"  Walk Dijkstra completed in {time.time() - t0:.2f}s")
    
    t0 = time.time()
    bike_times, bike_nearest_st = compute_multi_source_times(G_bike, st_nodes_bike, st_ids)
    print(f"  Safe E-Bike Dijkstra completed in {time.time() - t0:.2f}s")
    
    t0 = time.time()
    drive_times, drive_nearest_st = compute_multi_source_times(G_drive, st_nodes_drive, st_ids)
    print(f"  E-Auto Dijkstra completed in {time.time() - t0:.2f}s")
    
    # 7. Assign door-to-station times to each cell
    walk_cell_times = []
    bike_cell_times = []
    drive_cell_times = []
    st_walk = []
    st_bike = []
    st_drive = []
    
    for i in range(len(cells_gdf)):
        nw = cell_nodes_walk[i]
        nb = cell_nodes_bike[i]
        nd = cell_nodes_drive[i]
        snap_walk_time = snap_dists_walk_m[i] / walk_m_per_min
        
        # Walk time (node time + cell snap walk + station snap walk)
        if nw in walk_times:
            s_w = walk_nearest_st[nw]
            t_w = round(walk_times[nw] + snap_walk_time + st_snap_times_walk[s_w], 2)
        else:
            t_w = 999.0
            s_w = None
        walk_cell_times.append(t_w)
        st_walk.append(s_w)
        
        # E-Bike time (node time + cell snap walk + vehicle overhead + station snap bike)
        if nb in bike_times:
            s_b = bike_nearest_st[nb]
            t_b = round(bike_times[nb] + snap_walk_time + ebike_overhead + st_snap_times_bike[s_b], 2)
        else:
            t_b = 999.0
            s_b = None
        bike_cell_times.append(t_b)
        st_bike.append(s_b)
        
        # E-Auto time (node time + cell snap walk + wait/boarding overhead + station snap drive)
        if nd in drive_times:
            s_d = drive_nearest_st[nd]
            t_d = round(drive_times[nd] + snap_walk_time + eauto_overhead + st_snap_times_drive[s_d], 2)
        else:
            t_d = 999.0
            s_d = None
        drive_cell_times.append(t_d)
        st_drive.append(s_d)
        
    cells_gdf["walk_time_min"] = walk_cell_times
    cells_gdf["ebike_time_min"] = bike_cell_times
    cells_gdf["eauto_time_min"] = drive_cell_times
    
    cells_gdf["nearest_station_walk"] = st_walk
    cells_gdf["nearest_station_ebike"] = st_bike
    cells_gdf["nearest_station_eauto"] = st_drive
    cells_gdf["is_corridor_assigned"] = ~cells_gdf["nearest_station_walk"].astype(str).str.startswith("CTX_")
    
    # 8. Compute Catchment Flags and Uplifts for T = 15 min
    cells_gdf["walk_covered"] = cells_gdf["walk_time_min"] <= threshold_T
    cells_gdf["ebike_covered"] = cells_gdf["ebike_time_min"] <= threshold_T
    cells_gdf["eauto_covered"] = cells_gdf["eauto_time_min"] <= threshold_T
    
    # Uplifts (incremental coverage)
    cells_gdf["ebike_uplift"] = cells_gdf["ebike_covered"] & (~cells_gdf["walk_covered"])
    cells_gdf["eauto_uplift"] = cells_gdf["eauto_covered"] & (~cells_gdf["walk_covered"]) & (~cells_gdf["ebike_covered"])
    
    # Combined Union Catchment
    cells_gdf["combined_covered"] = cells_gdf["walk_covered"] | cells_gdf["ebike_covered"] | cells_gdf["eauto_covered"]
    cells_gdf["combined_time_min"] = cells_gdf[["walk_time_min", "ebike_time_min", "eauto_time_min"]].min(axis=1)
    cells_gdf["residual"] = ~cells_gdf["combined_covered"]
    
    # Clean up auxiliary columns before export
    export_gdf = cells_gdf.drop(columns=["centroid_wgs84", "centroid_x", "centroid_y"])
    
    # 9. Save outputs to data/interim and data/output
    export_gdf.to_file(interim_dir / "cells_catchments.gpkg", driver="GPKG")
    export_gdf.drop(columns=["geometry"]).to_csv(interim_dir / "cells_catchments.csv", index=False)
    
    export_gdf.to_file(out_dir / "cells.gpkg", driver="GPKG")
    export_gdf.drop(columns=["geometry"]).to_csv(out_dir / "cells.csv", index=False)
    export_gdf.drop(columns=["geometry"]).to_parquet(out_dir / "cells.parquet", index=False)
    
    # 10. Generate Summary Headline Metrics
    total_pop = cells_gdf["population"].sum()
    walk_pop = cells_gdf[cells_gdf["walk_covered"]]["population"].sum()
    ebike_uplift_pop = cells_gdf[cells_gdf["ebike_uplift"]]["population"].sum()
    eauto_uplift_pop = cells_gdf[cells_gdf["eauto_uplift"]]["population"].sum()
    combined_pop = cells_gdf[cells_gdf["combined_covered"]]["population"].sum()
    residual_pop = cells_gdf[cells_gdf["residual"]]["population"].sum()

    corridor_cells = cells_gdf[cells_gdf["is_corridor_assigned"] == True]
    c_pop = corridor_cells["population"].sum()
    c_walk = corridor_cells[corridor_cells["walk_covered"]]["population"].sum()
    c_ebike_up = corridor_cells[corridor_cells["ebike_uplift"]]["population"].sum()
    c_eauto_up = corridor_cells[corridor_cells["eauto_uplift"]]["population"].sum()
    c_comb = corridor_cells[corridor_cells["combined_covered"]]["population"].sum()
    c_resid = corridor_cells[corridor_cells["residual"]]["population"].sum()
    
    metrics = {
        "study_area": "Whitefield 10-Station Metro Corridor",
        "threshold_T_min": threshold_T,
        "total_population": round(float(total_pop), 0),
        "walk_covered_pop": round(float(walk_pop), 0),
        "walk_covered_pct": round(float(walk_pop / total_pop * 100), 1),
        "ebike_uplift_pop": round(float(ebike_uplift_pop), 0),
        "ebike_uplift_pct": round(float(ebike_uplift_pop / total_pop * 100), 1),
        "eauto_uplift_pop": round(float(eauto_uplift_pop), 0),
        "eauto_uplift_pct": round(float(eauto_uplift_pop / total_pop * 100), 1),
        "combined_covered_pop": round(float(combined_pop), 0),
        "combined_covered_pct": round(float(combined_pop / total_pop * 100), 1),
        "residual_pop": round(float(residual_pop), 0),
        "residual_pct": round(float(residual_pop / total_pop * 100), 1),
        "corridor_assigned": {
            "corridor_population": round(float(c_pop), 0),
            "walk_covered_pop": round(float(c_walk), 0),
            "walk_covered_pct": round(float(c_walk / c_pop * 100), 1) if c_pop > 0 else 0.0,
            "ebike_uplift_pop": round(float(c_ebike_up), 0),
            "ebike_uplift_pct": round(float(c_ebike_up / c_pop * 100), 1) if c_pop > 0 else 0.0,
            "eauto_uplift_pop": round(float(c_eauto_up), 0),
            "eauto_uplift_pct": round(float(c_eauto_up / c_pop * 100), 1) if c_pop > 0 else 0.0,
            "combined_covered_pop": round(float(c_comb), 0),
            "combined_covered_pct": round(float(c_comb / c_pop * 100), 1) if c_pop > 0 else 0.0,
            "residual_pop": round(float(c_resid), 0),
            "residual_pct": round(float(c_resid / c_pop * 100), 1) if c_pop > 0 else 0.0,
        }
    }
    
    
    with open(out_dir / "catchment_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    print("\n=======================================================")
    print("           CATCHMENT & UPLIFT RESULTS (T = 15 MIN)     ")
    print("=======================================================")
    print(f"Total Study Area Population:   {metrics['total_population']:>10,.0f} (100.0%)")
    print(f"1. Pedestrian Walk Catchment:  {metrics['walk_covered_pop']:>10,.0f} ({metrics['walk_covered_pct']}%)")
    print(f"2. E-Bike Feeder Uplift:       {metrics['ebike_uplift_pop']:>10,.0f} ({metrics['ebike_uplift_pct']}%)")
    print(f"3. E-Auto Extra Uplift:        {metrics['eauto_uplift_pop']:>10,.0f} ({metrics['eauto_uplift_pct']}%)")
    print(f"-------------------------------------------------------")
    print(f"Total Combined Union Access:   {metrics['combined_covered_pop']:>10,.0f} ({metrics['combined_covered_pct']}%)")
    print(f"Residual Unserved Gap:         {metrics['residual_pop']:>10,.0f} ({metrics['residual_pct']}%)")
    print("=======================================================\n")
    
    return export_gdf


if __name__ == "__main__":
    build_catchments_and_uplift()
