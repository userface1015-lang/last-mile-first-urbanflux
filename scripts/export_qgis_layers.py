"""
export_qgis_layers.py - Generates dedicated, ready-to-load QGIS layers and GeoPackages
for Walkability catchments, E-Bike catchments, E-Bike Uplift, and boundary outlines.

Outputs:
1. data/output/catchments_qgis.gpkg (Multi-layer master GeoPackage for QGIS)
2. data/output/qgis_layers/ (Individual standalone GeoPackages for one-click drag-and-drop)
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def main():
    print("================================================================================")
    print("        EXPORTING MULTI-MODAL CATCHMENT LAYERS FOR QGIS VISUALIZATION           ")
    print("================================================================================")
    
    out_dir = Path("data/output")
    qgis_dir = out_dir / "qgis_layers"
    qgis_dir.mkdir(parents=True, exist_ok=True)
    master_gpkg = out_dir / "catchments_qgis.gpkg"
    
    # 1. Load cells
    cells_gdf = gpd.read_file(out_dir / "cells.gpkg")
    corr_mask = cells_gdf["is_corridor_assigned"] == True
    corr_cells = cells_gdf[corr_mask].copy()
    
    print(f"Loaded {len(cells_gdf)} total cells ({len(corr_cells)} core corridor cells).")
    
    # Define Catchment Subsets
    # T = 15 min
    w15_mask = corr_mask & (cells_gdf["walk_time_min"] <= 15.0)
    b15_mask = corr_mask & (cells_gdf["ebike_time_min"] <= 15.0)
    up15_mask = b15_mask & (~w15_mask)
    comb15_mask = corr_mask & (w15_mask | b15_mask)
    unserved15_mask = corr_mask & (cells_gdf["walk_time_min"] > 15.0) & (cells_gdf["ebike_time_min"] > 15.0) & (cells_gdf["eauto_time_min"] > 15.0)
    
    # T = 20 min
    w20_mask = corr_mask & (cells_gdf["walk_time_min"] <= 20.0)
    b20_mask = corr_mask & (cells_gdf["ebike_time_min"] <= 20.0)
    up20_mask = b20_mask & (~w20_mask)
    comb20_mask = corr_mask & (w20_mask | b20_mask)

    layers = {
        "walk_catchment_15min": cells_gdf[w15_mask].copy(),
        "ebike_catchment_15min": cells_gdf[b15_mask].copy(),
        "ebike_uplift_15min": cells_gdf[up15_mask].copy(),
        "combined_active_15min": cells_gdf[comb15_mask].copy(),
        "unserved_gap_15min": cells_gdf[unserved15_mask].copy(),
        "walk_catchment_20min": cells_gdf[w20_mask].copy(),
        "ebike_catchment_20min": cells_gdf[b20_mask].copy(),
        "ebike_uplift_20min": cells_gdf[up20_mask].copy(),
        "combined_active_20min": cells_gdf[comb20_mask].copy(),
    }

    # 2. Add dissolved boundary polygons
    w15_diss = cells_gdf[w15_mask].dissolve().copy()
    w15_diss["layer_name"] = "Walk Catchment Boundary (15 min)"
    w15_diss["population"] = cells_gdf[w15_mask]["population"].sum()
    w15_diss["cell_count"] = int(w15_mask.sum())
    layers["walk_boundary_15min"] = w15_diss[["layer_name", "population", "cell_count", "geometry"]]

    b15_diss = cells_gdf[b15_mask].dissolve().copy()
    b15_diss["layer_name"] = "E-Bike Catchment Boundary (15 min)"
    b15_diss["population"] = cells_gdf[b15_mask]["population"].sum()
    b15_diss["cell_count"] = int(b15_mask.sum())
    layers["ebike_boundary_15min"] = b15_diss[["layer_name", "population", "cell_count", "geometry"]]

    comb15_diss = cells_gdf[comb15_mask].dissolve().copy()
    comb15_diss["layer_name"] = "Active Catchment Boundary (15 min)"
    comb15_diss["population"] = cells_gdf[comb15_mask]["population"].sum()
    comb15_diss["cell_count"] = int(comb15_mask.sum())
    layers["combined_boundary_15min"] = comb15_diss[["layer_name", "population", "cell_count", "geometry"]]

    # 3. Build Metro Stations layer
    st_pilot = gpd.read_file("data/interim/stations_pilot.gpkg").to_crs("EPSG:4326")
    st_pilot["station_type"] = "Pilot Station (Core)"
    st_all = gpd.read_file("data/interim/stations_all.gpkg").to_crs("EPSG:4326")
    ctx_st = st_all[st_all["name"].isin(["Singayyanapalya", "Krishnarajapura"])].copy()
    ctx_st["station_type"] = "Context Station (Boundary Absorber)"
    ctx_st["station_id"] = ["CTX_01", "CTX_02"]
    
    # Merge with ranking if available
    ranking_csv = out_dir / "station_ranking.csv"
    if ranking_csv.exists():
        rank_df = pd.read_csv(ranking_csv)
        st_pilot = st_pilot.merge(rank_df[["station_id", "avg_daily_ridership", "priority_score", "rank"]], on="station_id", how="left")
        ctx_st["avg_daily_ridership"] = 0.0
        ctx_st["priority_score"] = 0.0
        ctx_st["rank"] = 0

    metro_stations = pd.concat([st_pilot, ctx_st], ignore_index=True)
    layers["metro_stations"] = metro_stations[["station_id", "name", "station_type", "avg_daily_ridership", "priority_score", "rank", "geometry"]]

    # Remove existing master file if present
    if master_gpkg.exists():
        master_gpkg.unlink()

    print("\n--- Writing Layers to Master GeoPackage and Standalone Files ---")
    for layer_name, gdf in layers.items():
        print(f"  -> Exporting layer: {layer_name} ({len(gdf)} features)...")
        # Write to master multi-layer GPKG
        gdf.to_file(master_gpkg, layer=layer_name, driver="GPKG")
        
        # Write standalone single-layer GPKG for direct drag-and-drop
        standalone_path = qgis_dir / f"{layer_name}.gpkg"
        gdf.to_file(standalone_path, layer=layer_name, driver="GPKG")

    print("\n================================================================================")
    print(f"SUCCESS: Exported {len(layers)} QGIS layers!")
    print(f"Master multi-layer file : {master_gpkg.resolve()}")
    print(f"Standalone layer folder : {qgis_dir.resolve()}")
    print("================================================================================")

if __name__ == "__main__":
    main()
