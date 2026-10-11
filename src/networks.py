"""
networks.py - Step S5: Download, clean, filter, and process road networks for Walk, E-Bike, and E-Auto.
Assigns exact edge travel times, applies the OSM road-class safety filter, and caches graphs.
"""

from pathlib import Path
from typing import Dict, Tuple
import osmnx as ox
import networkx as nx
import geopandas as gpd

from src.config import load_config, get_meters_per_minute


def get_largest_connected_component(G: nx.MultiDiGraph) -> Tuple[nx.MultiDiGraph, float]:
    """
    Extracts the largest strongly connected component (for directed graph)
    or weakly connected component if strongly connected drops too many nodes.
    Returns (filtered_graph, node_retention_ratio).
    """
    total_nodes = len(G)
    if total_nodes == 0:
        return G, 0.0

    # For accessibility routing to destination, weakly connected components
    # are kept first, and unreachable nodes are caught during Dijkstra.
    components = list(nx.weakly_connected_components(G))
    largest_comp = max(components, key=len)
    G_sub = G.subgraph(largest_comp).copy()
    retention = len(G_sub) / total_nodes
    return G_sub, retention


def parse_numeric_tag(val, default: float = 0.0) -> float:
    """Safely parse lanes or maxspeed tags that might be lists, strings, or None."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, list):
        val = val[0]
    s = str(val).split()[0].split(";")[0]
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def apply_safety_filter(
    G_bike: nx.MultiDiGraph,
    exclude_classes: list,
    lanes_threshold: int = 3,
    speed_threshold: float = 50.0,
    mode: str = "exclude",
    penalty_factor: float = 2.0
) -> Tuple[nx.MultiDiGraph, dict]:
    """
    Filters high-speed and multi-lane roads from the bike network.
    In 'exclude' mode, drops unsafe edges. In 'penalise' mode, inflates edge travel time.
    """
    G_filtered = G_bike.copy()
    edges_to_remove = []
    edges_penalised = 0
    total_edges = G_filtered.number_of_edges()
    
    for u, v, k, data in G_filtered.edges(keys=True, data=True):
        hw = data.get("highway", "")
        if isinstance(hw, list):
            hw = hw[0]
            
        lanes = parse_numeric_tag(data.get("lanes"), default=1.0)
        maxspeed = parse_numeric_tag(data.get("maxspeed"), default=30.0)
        
        is_unsafe_class = hw in exclude_classes
        is_high_speed_primary = (hw == "primary") and (lanes >= lanes_threshold or maxspeed >= speed_threshold)
        
        if is_unsafe_class or is_high_speed_primary:
            if mode == "exclude":
                edges_to_remove.append((u, v, k))
            else:
                data["time_min"] = data["time_min"] * penalty_factor
                edges_penalised += 1
                
    if mode == "exclude":
        G_filtered.remove_edges_from(edges_to_remove)
        # Retain largest connected component after edge removal
        G_filtered, _ = get_largest_connected_component(G_filtered)
        
    stats = {
        "total_edges": total_edges,
        "removed_edges": len(edges_to_remove),
        "penalised_edges": edges_penalised,
        "remaining_edges": G_filtered.number_of_edges(),
        "remaining_nodes": G_filtered.number_of_nodes()
    }
    return G_filtered, stats


def build_and_process_networks(
    build_poly_path: str | Path = "data/interim/study_area_build_wgs84.gpkg",
    config_path: str | Path = "config/params.yaml",
    output_dir: str | Path = "data/interim"
) -> Dict[str, nx.MultiDiGraph]:
    """
    Builds walk, bike, safe-bike, and drive networks for the build polygon,
    projects to metric CRS, assigns edge times, and caches them to GraphML.
    """
    cfg = load_config(config_path)
    metric_crs = cfg["study"]["metric_crs"]
    speeds = cfg["speeds_kmh"]
    safety_cfg = cfg["safety_filter"]
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    walk_m_per_min = get_meters_per_minute(speeds["walk"])
    ebike_m_per_min = get_meters_per_minute(speeds["ebike"])
    eauto_m_per_min = get_meters_per_minute(speeds.get("eauto", 18.0))
    
    # 1. Load build polygon in WGS84
    build_gdf = gpd.read_file(build_poly_path)
    poly = build_gdf.geometry.iloc[0]
    
    print("\n--- 1. Downloading / Loading OSM Networks ---")
    
    # Walk Graph
    walk_path = out_dir / "graph_walk.graphml"
    if walk_path.exists():
        print(f"Loading cached walk graph from {walk_path}...")
        G_walk = ox.load_graphml(walk_path)
    else:
        print("Downloading OSM walk graph...")
        G_walk = ox.graph_from_polygon(poly, network_type="walk")
        G_walk = ox.project_graph(G_walk, to_crs=metric_crs)
        G_walk, ret = get_largest_connected_component(G_walk)
        print(f"Walk graph: {len(G_walk.nodes)} nodes, {len(G_walk.edges)} edges (retention: {ret*100:.1f}%)")
        ox.save_graphml(G_walk, walk_path)

    # Bike Graph
    bike_path = out_dir / "graph_bike_unfiltered.graphml"
    if bike_path.exists():
        print(f"Loading cached bike graph from {bike_path}...")
        G_bike = ox.load_graphml(bike_path)
    else:
        print("Downloading OSM bike graph...")
        G_bike = ox.graph_from_polygon(poly, network_type="bike")
        G_bike = ox.project_graph(G_bike, to_crs=metric_crs)
        G_bike, ret = get_largest_connected_component(G_bike)
        print(f"Bike graph: {len(G_bike.nodes)} nodes, {len(G_bike.edges)} edges (retention: {ret*100:.1f}%)")
        ox.save_graphml(G_bike, bike_path)

    # Drive Graph (for E-Auto)
    drive_path = out_dir / "graph_drive.graphml"
    if drive_path.exists():
        print(f"Loading cached drive graph from {drive_path}...")
        G_drive = ox.load_graphml(drive_path)
    else:
        print("Downloading OSM drive graph...")
        G_drive = ox.graph_from_polygon(poly, network_type="drive")
        G_drive = ox.project_graph(G_drive, to_crs=metric_crs)
        G_drive, ret = get_largest_connected_component(G_drive)
        print(f"Drive graph: {len(G_drive.nodes)} nodes, {len(G_drive.edges)} edges (retention: {ret*100:.1f}%)")
        ox.save_graphml(G_drive, drive_path)

    print("\n--- 2. Assigning Travel Times ---")
    
    # Assign walk times (bidirectional for pedestrian safety)
    for _, _, _, data in G_walk.edges(keys=True, data=True):
        length = max(float(data.get("length", 1.0)), 1.0)
        data["time_min"] = length / walk_m_per_min

    # Assign bike times
    for _, _, _, data in G_bike.edges(keys=True, data=True):
        length = max(float(data.get("length", 1.0)), 1.0)
        data["time_min"] = length / ebike_m_per_min

    # Assign drive times
    for _, _, _, data in G_drive.edges(keys=True, data=True):
        length = max(float(data.get("length", 1.0)), 1.0)
        data["time_min"] = length / eauto_m_per_min

    print(f"Travel times assigned: Walk @ {speeds['walk']} km/h, E-bike @ {speeds['ebike']} km/h, E-auto @ {speeds.get('eauto', 18.0)} km/h")

    # 3. Apply Safety Filter to Bike Graph
    print("\n--- 3. Applying Safety Filter to E-Bike Network ---")
    G_bike_safe, safety_stats = apply_safety_filter(
        G_bike,
        exclude_classes=safety_cfg["exclude_highway_classes"],
        lanes_threshold=safety_cfg["penalise_or_exclude_primary_if"]["lanes_at_least"],
        speed_threshold=safety_cfg["penalise_or_exclude_primary_if"]["maxspeed_at_least_kmh"],
        mode=safety_cfg.get("mode", "exclude"),
        penalty_factor=safety_cfg.get("penalty_factor", 2.0)
    )
    print(f"Safety filter stats: Removed {safety_stats['removed_edges']} dangerous edges.")
    print(f"Safe E-bike network: {safety_stats['remaining_nodes']} nodes, {safety_stats['remaining_edges']} edges")
    
    # Save processed safe bike graph
    safe_bike_path = out_dir / "graph_bike_safe.graphml"
    ox.save_graphml(G_bike_safe, safe_bike_path)
    
    # Resave graphs with updated travel time attributes
    ox.save_graphml(G_walk, walk_path)
    ox.save_graphml(G_bike, bike_path)
    ox.save_graphml(G_drive, drive_path)
    
    return {
        "walk": G_walk,
        "bike_unfiltered": G_bike,
        "bike_safe": G_bike_safe,
        "drive": G_drive
    }


if __name__ == "__main__":
    build_and_process_networks()
