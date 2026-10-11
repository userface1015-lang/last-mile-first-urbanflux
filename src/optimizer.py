"""
optimizer.py - Steps S12, S13, S14, S16:
1. Candidate sites generation & spatial thinning (S12)
2. Sparse site-to-cell coverage pairs computation (S13)
3. Greedy maximum-coverage optimization for k feeder zones (S14)
4. Station prioritization ranking with ridership weighting (S16)
5. Parametric sensitivity analysis across speed, overhead, and thresholds.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import json
import time

import networkx as nx
import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point

from src.config import load_config, get_meters_per_minute
from src.travel_times import snap_nodes_reachability_aware


def generate_candidate_sites(
    G_bike: nx.MultiDiGraph,
    G_walk: nx.MultiDiGraph,
    stations_gdf: gpd.GeoDataFrame,
    spacing_m: float = 120.0,
    max_ride_time_min: float = 10.0,
    metric_crs: str = "EPSG:32643"
) -> Tuple[gpd.GeoDataFrame, Dict[str, float], Dict[str, str]]:
    """
    Step S12: Thins bike-graph nodes by spatial grid and computes ride time to nearest station.
    """
    print(f"\n--- 1. Generating Candidate Sites (spacing: {spacing_m}m) ---")
    st_xs = stations_gdf.geometry.x.values
    st_ys = stations_gdf.geometry.y.values
    st_ids = stations_gdf["station_id"].tolist()
    st_nodes = snap_nodes_reachability_aware(G_bike, st_xs, st_ys, min_reach=1000)

    # Multi-source Dijkstra from all stations on reversed bike graph
    G_bike_rev = G_bike.reverse(copy=True)
    bike_ride_time = {}
    bike_nearest_st = {}

    for sid, sn in zip(st_ids, st_nodes):
        dists = nx.single_source_dijkstra_path_length(G_bike_rev, sn, weight="time_min")
        for n, t in dists.items():
            if n not in bike_ride_time or t < bike_ride_time[n]:
                bike_ride_time[n] = t
                bike_nearest_st[n] = sid

    # Spatial grid thinning
    grid_buckets = {}
    for n in G_bike.nodes:
        if n in bike_ride_time and bike_ride_time[n] <= max_ride_time_min:
            nd = G_bike.nodes[n]
            gx = int(float(nd["x"]) / spacing_m)
            gy = int(float(nd["y"]) / spacing_m)
            key = (gx, gy)
            if key not in grid_buckets:
                grid_buckets[key] = n

    thinned_bike_nodes = sorted(list(grid_buckets.values()))
    print(f"Thinned {len(thinned_bike_nodes)} candidate hub nodes from {len(G_bike.nodes)} road nodes.")

    # Snap candidate nodes to walk graph
    cand_xs = [float(G_bike.nodes[n]["x"]) for n in thinned_bike_nodes]
    cand_ys = [float(G_bike.nodes[n]["y"]) for n in thinned_bike_nodes]
    thinned_walk_nodes = ox.distance.nearest_nodes(G_walk, cand_xs, cand_ys)

    # Convert coordinates to WGS84 for display
    gdf_metric = gpd.GeoDataFrame(
        geometry=[Point(x, y) for x, y in zip(cand_xs, cand_ys)],
        crs=metric_crs
    )
    gdf_wgs84 = gdf_metric.to_crs("EPSG:4326")

    records = []
    for i, (bn, wn) in enumerate(zip(thinned_bike_nodes, thinned_walk_nodes)):
        site_id = f"SITE_{i+1:04d}"
        geom_m = gdf_metric.geometry.iloc[i]
        geom_w = gdf_wgs84.geometry.iloc[i]
        r_time = round(bike_ride_time[bn], 2)
        n_st = bike_nearest_st[bn]

        records.append({
            "site_id": site_id,
            "node_bike": int(bn),
            "node_walk": int(wn),
            "lon": round(float(geom_w.x), 6),
            "lat": round(float(geom_w.y), 6),
            "ride_time_to_station_min": r_time,
            "nearest_station": n_st,
            "allowed": True,
            "geometry": geom_m
        })

    sites_gdf = gpd.GeoDataFrame(records, crs=metric_crs)
    return sites_gdf, bike_ride_time, bike_nearest_st


def compute_coverage_pairs(
    G_walk: nx.MultiDiGraph,
    sites_gdf: gpd.GeoDataFrame,
    cells_gdf: gpd.GeoDataFrame,
    threshold_T: float = 15.0,
    overhead_min: float = 5.0,
    max_walk_to_site_min: float = 5.0,
    walk_speed_kmh: float = 4.5
) -> pd.DataFrame:
    """
    Step S13: For each candidate site, determines target cells reachable within 5 min walk
    where total trip (walk to site + overhead + ebike ride to station) <= T.
    """
    print("\n--- 2. Computing Sparse Site-to-Cell Coverage Pairs ---")
    walk_m_per_min = get_meters_per_minute(walk_speed_kmh)

    # Map walk nodes to cell IDs (only target unserved cells within corridor at threshold_T)
    if "is_corridor_assigned" in cells_gdf.columns:
        target_cells = cells_gdf[(cells_gdf["walk_time_min"] > threshold_T) & (cells_gdf["is_corridor_assigned"] == True)].copy()
    else:
        target_cells = cells_gdf[cells_gdf["walk_time_min"] > threshold_T].copy()
    print(f"Target unserved cells at T={threshold_T:.0f}m: {len(target_cells)} with population {target_cells['population'].sum():,.0f}")

    node_to_cells: Dict[int, List[Tuple[str, float]]] = {}
    for _, row in target_cells.iterrows():
        node = int(row["node_walk"])
        cid = str(row["cell_id"])
        snap_walk_t = float(row["snap_dist_m"]) / walk_m_per_min
        if node not in node_to_cells:
            node_to_cells[node] = []
        node_to_cells[node].append((cid, snap_walk_t))

    pairs = []
    t0 = time.time()

    for _, site in sites_gdf.iterrows():
        site_id = site["site_id"]
        wn = site["node_walk"]
        ride_time = site["ride_time_to_station_min"]

        # Remaining walk time budget to keep total trip <= T
        max_allowed_walk = min(max_walk_to_site_min, threshold_T - overhead_min - ride_time)
        if max_allowed_walk <= 0:
            continue

        # Outward Dijkstra on walk graph with cutoff
        walk_dists = nx.single_source_dijkstra_path_length(
            G_walk, wn, cutoff=max_allowed_walk, weight="time_min"
        )

        for reached_node, t_walk_node in walk_dists.items():
            if reached_node in node_to_cells:
                for cid, snap_t in node_to_cells[reached_node]:
                    tot_walk_to_site = t_walk_node + snap_t
                    if tot_walk_to_site <= max_walk_to_site_min:
                        tot_trip = tot_walk_to_site + overhead_min + ride_time
                        if tot_trip <= threshold_T:
                            pairs.append({
                                "site_id": site_id,
                                "cell_id": cid,
                                "walk_time_to_site_min": round(tot_walk_to_site, 2),
                                "total_trip_min": round(tot_trip, 2)
                            })

    pairs_df = pd.DataFrame(pairs)
    # Deduplicate in case multiple nodes connect to the same cell
    if not pairs_df.empty:
        pairs_df = pairs_df.sort_values(by="walk_time_to_site_min").drop_duplicates(subset=["site_id", "cell_id"]).reset_index(drop=True)
        
    print(f"Coverage pairs computed in {time.time() - t0:.2f}s: {len(pairs_df)} sparse pairs.")
    return pairs_df


def run_greedy_max_coverage(
    sites_gdf: gpd.GeoDataFrame,
    coverage_pairs_df: pd.DataFrame,
    cells_gdf: gpd.GeoDataFrame,
    k_max: int = 15,
    baseline_walk_covered_pop: float = 0.0
) -> pd.DataFrame:
    """
    Step S14: Greedy maximum-coverage optimizer choosing k feeder sites to maximize
    newly covered unserved population without double-counting.
    """
    print(f"\n--- 3. Running Greedy Max-Coverage Optimizer (up to k = {k_max}) ---")
    pop_lookup = dict(zip(cells_gdf["cell_id"].astype(str), cells_gdf["population"].astype(float)))

    # Build site -> set of cells mapping
    site_to_cells = {}
    for sid, group in coverage_pairs_df.groupby("site_id"):
        site_to_cells[sid] = set(group["cell_id"])

    # All allowed sites
    all_sites = set(sites_gdf["site_id"])
    for sid in all_sites:
        if sid not in site_to_cells:
            site_to_cells[sid] = set()

    covered_cells = set()
    unselected_sites = set(all_sites)
    results = []
    cum_covered = 0.0

    for step in range(1, k_max + 1):
        best_site = None
        best_gain = -1.0
        best_new_cells = set()

        for sid in sorted(unselected_sites):  # deterministic tie-break
            cells = site_to_cells[sid]
            new_cells = cells - covered_cells
            gain = sum(pop_lookup.get(c, 0.0) for c in new_cells)

            if gain > best_gain:
                best_gain = gain
                best_site = sid
                best_new_cells = new_cells

        if best_site is None or best_gain <= 0:
            print(f"Stopping early at step {step}: no remaining site adds coverage.")
            break

        covered_cells.update(best_new_cells)
        unselected_sites.remove(best_site)
        cum_covered += best_gain

        results.append({
            "k": step,
            "order": step,
            "site_id": best_site,
            "marginal_gain": round(best_gain, 1),
            "cumulative_feeder_pop": round(cum_covered, 1),
            "coverage_before": round(baseline_walk_covered_pop, 1),
            "coverage_after": round(baseline_walk_covered_pop + cum_covered, 1)
        })

    selected_df = pd.DataFrame(results)
    print("Optimization results summary (Top 5 selected hubs):")
    print(selected_df.head(5)[["k", "site_id", "marginal_gain", "coverage_after"]].to_string(index=False))
    return selected_df


def rank_stations(
    stations_gdf: gpd.GeoDataFrame,
    cells_gdf: gpd.GeoDataFrame,
    output_dir: str | Path = "data/output"
) -> pd.DataFrame:
    """
    Step S16: Ranks stations by uncovered population, weighted by August 2025 ridership.
    """
    print("\n--- 4. Computing Station Prioritization Ranking ---")
    # Identify unserved cells and their nearest walk station (within corridor)
    unserved_cells = cells_gdf[cells_gdf["walk_covered"] == False].copy()
    if "is_corridor_assigned" in unserved_cells.columns:
        unserved_cells = unserved_cells[unserved_cells["is_corridor_assigned"] == True]
    unserved_by_station = unserved_cells.groupby("nearest_station_walk")["population"].sum().to_dict()

    # Calculate average daily ridership (18 operational days in August RTI dataset)
    st_records = []
    known_daily = []
    for _, st in stations_gdf.iterrows():
        sid = st["station_id"]
        r = float(st["ridership"]) if pd.notna(st["ridership"]) and st["ridership"] > 0 else np.nan
        if not np.isnan(r):
            known_daily.append(r / 18.0)

    mean_daily = np.mean(known_daily) if known_daily else 1.0

    for _, st in stations_gdf.iterrows():
        sid = st["station_id"]
        s_name = st["name"]
        uncov_pop = round(float(unserved_by_station.get(sid, 0.0)), 1)
        r = float(st["ridership"]) if pd.notna(st["ridership"]) and st["ridership"] > 0 else (mean_daily * 18.0)
        daily_r = round(r / 18.0, 0)
        weight = round(float(daily_r / mean_daily), 4)
        score = round(float(uncov_pop * (daily_r / mean_daily)), 1)

        st_records.append({
            "station_id": sid,
            "name": s_name,
            "walk_uncovered_need": uncov_pop,
            "avg_daily_ridership": daily_r,
            "total_ridership": round(r, 0),
            "weight": weight,
            "priority_score": score
        })

    ranking_df = pd.DataFrame(st_records)
    ranking_df = ranking_df.sort_values(by="priority_score", ascending=False).reset_index(drop=True)
    ranking_df["rank"] = ranking_df.index + 1

    out_path = Path(output_dir) / "station_ranking.csv"
    ranking_df.to_csv(out_path, index=False)
    print("Station Ranking Table (Top stations by priority score):")
    print(ranking_df[["rank", "name", "walk_uncovered_need", "avg_daily_ridership", "priority_score"]].to_string(index=False))
    return ranking_df


def compute_sensitivity_grid(
    cells_gdf: gpd.GeoDataFrame,
    speeds: list = [12.0, 13.5, 15.0],
    overheads: list = [3.0, 5.0, 7.0],
    thresholds: list = [10.0, 15.0, 20.0],
    output_dir: str | Path = "data/output"
) -> pd.DataFrame:
    """
    Step S9 / S18: Computes uplift sensitivity across speed, overhead, and time threshold grids.
    """
    print("\n--- 5. Generating Parametric Sensitivity Grid ---")
    if "is_corridor_assigned" in cells_gdf.columns:
        target_cells = cells_gdf[cells_gdf["is_corridor_assigned"] == True].copy()
    else:
        target_cells = cells_gdf.copy()
    total_pop = target_cells["population"].sum()
    rows = []

    for s in speeds:
        for ov in overheads:
            for t in thresholds:
                # Approximate scale factor for e-bike riding time relative to default 13.5 km/h
                # t_ride_scaled = t_ride_default * (13.5 / s)
                # Cell ebike time = (ebike_time_default - 5.0) * (13.5 / s) + ov
                ebike_times = np.maximum(0.0, target_cells["ebike_time_min"] - 5.0) * (13.5 / s) + ov
                walk_times = target_cells["walk_time_min"]

                walk_cov = walk_times <= t
                ebike_cov = ebike_times <= t
                uplift = ebike_cov & (~walk_cov)
                resid = (~walk_cov) & (~ebike_cov)

                w_pop = round(float(target_cells[walk_cov]["population"].sum()), 0)
                e_pop = round(float(target_cells[ebike_cov]["population"].sum()), 0)
                up_pop = round(float(target_cells[uplift]["population"].sum()), 0)
                res_pop = round(float(target_cells[resid]["population"].sum()), 0)

                rows.append({
                    "speed_ebike_kmh": s,
                    "overhead_min": ov,
                    "threshold_T_min": t,
                    "corridor_population": round(float(total_pop), 0),
                    "walk_covered_pop": w_pop,
                    "walk_covered_pct": round(float(w_pop / total_pop * 100), 1),
                    "ebike_covered_pop": e_pop,
                    "ebike_covered_pct": round(float(e_pop / total_pop * 100), 1),
                    "uplift_pop": up_pop,
                    "uplift_pct": round(float(up_pop / total_pop * 100), 1),
                    "residual_pop": res_pop,
                    "residual_pct": round(float(res_pop / total_pop * 100), 1)
                })

    sens_df = pd.DataFrame(rows)
    out_path = Path(output_dir) / "sensitivity.csv"
    sens_df.to_csv(out_path, index=False)
    print(f"Sensitivity grid generated ({len(sens_df)} combinations) -> saved to {out_path}")
    return sens_df


def run_full_optimization_pipeline(
    config_path: str | Path = "config/params.yaml",
    output_dir: str | Path = "data/output"
) -> None:
    """Runs Steps S12, S13, S14, and S16 end to end and writes all cached output files."""
    cfg = load_config(config_path)
    metric_crs = cfg["study"]["metric_crs"]
    site_spacing = float(cfg["optimiser"].get("site_spacing_m", 120.0))
    threshold_T = float(cfg["thresholds"]["T_min"])
    ebike_overhead = float(cfg["overhead_min"]["ebike"])
    walk_to_zone_max = float(cfg["thresholds"]["walk_to_zone_max_min"])
    walk_speed = float(cfg["speeds_kmh"]["walk"])
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load prerequisite data
    G_walk = ox.load_graphml("data/interim/graph_walk.graphml")
    for _, _, _, d in G_walk.edges(keys=True, data=True):
        d["time_min"] = float(d["time_min"])
        d["length"] = float(d.get("length", 1.0))

    G_bike_safe = ox.load_graphml("data/interim/graph_bike_safe.graphml")
    for _, _, _, d in G_bike_safe.edges(keys=True, data=True):
        d["time_min"] = float(d["time_min"])
        d["length"] = float(d.get("length", 1.0))

    stations_gdf = gpd.read_file("data/interim/stations_selected.gpkg").to_crs(metric_crs)
    context_names = cfg.get("study", {}).get("stations_context", [])
    if context_names:
        stations_all = gpd.read_file("data/interim/stations_all.gpkg").to_crs(metric_crs)
        ctx_gdf = stations_all[stations_all["name"].isin(context_names)].copy()
        ctx_gdf["station_id"] = [f"CTX_{i+1:02d}" for i in range(len(ctx_gdf))]
        all_stations_cand = pd.concat([stations_gdf, ctx_gdf], ignore_index=True)
    else:
        all_stations_cand = stations_gdf

    cells_gdf = gpd.read_file(out_dir / "cells.gpkg")

    # 2. Step S12: Candidate Sites
    sites_gdf, _, _ = generate_candidate_sites(
        G_bike_safe, G_walk, all_stations_cand, spacing_m=site_spacing, metric_crs=metric_crs
    )
    sites_gdf.to_file(out_dir / "candidate_sites.gpkg", driver="GPKG")
    sites_gdf.drop(columns=["geometry"]).to_csv(out_dir / "candidate_sites.csv", index=False)

    # 3. Step S13: Coverage Pairs
    pairs_df = compute_coverage_pairs(
        G_walk, sites_gdf, cells_gdf,
        threshold_T=threshold_T,
        overhead_min=ebike_overhead,
        max_walk_to_site_min=walk_to_zone_max,
        walk_speed_kmh=walk_speed
    )
    pairs_df.to_csv(out_dir / "coverage_pairs.csv", index=False)
    pairs_df.to_parquet(out_dir / "coverage_pairs.parquet", index=False)

    # 4. Step S14: Greedy Max-Coverage Optimizer
    if "is_corridor_assigned" in cells_gdf.columns:
        corr_cells = cells_gdf[cells_gdf["is_corridor_assigned"] == True]
        walk_baseline_pop = corr_cells[corr_cells["walk_covered"]]["population"].sum()
    else:
        walk_baseline_pop = cells_gdf[cells_gdf["walk_covered"]]["population"].sum()

    selected_df = run_greedy_max_coverage(
        sites_gdf, pairs_df, cells_gdf, k_max=15, baseline_walk_covered_pop=walk_baseline_pop
    )
    selected_df.to_csv(out_dir / "selected_sites.csv", index=False)

    # Attach geometry to selected sites for mapping
    selected_merged = selected_df.merge(
        sites_gdf[["site_id", "lon", "lat", "geometry"]], on="site_id", how="left"
    )
    gpd.GeoDataFrame(selected_merged, crs=metric_crs).to_file(out_dir / "selected_sites.gpkg", driver="GPKG")

    # 5. Step S16: Station Ranking
    rank_stations(stations_gdf, cells_gdf, output_dir=out_dir)

    # 6. Sensitivity Grid
    compute_sensitivity_grid(cells_gdf, output_dir=out_dir)

    print("\nAll optimizer and ranking outputs successfully exported to data/output/!")


if __name__ == "__main__":
    run_full_optimization_pipeline()
