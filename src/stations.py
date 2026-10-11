"""
stations.py - Step S3: Clean, match, and extract metro stations across Bengaluru.
Reads raw metro stations GPKG (63 stations) and OSM coordinates (20 stations)
for all 83 operational stations, joins August 2025 ridership data, and outputs
clean stations table strictly matching the data model contract.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, List
import geopandas as gpd
import pandas as pd
import numpy as np

from src.config import load_config

# Canonical mapping for name variations between OpenStreetMap/GPKG and BMRCL ridership records
NAME_MAPPING: Dict[str, str] = {
    "Sathya Sai Hospital": "Sri Sathya Sai Hospital",
    "Baiyyappanahalli": "Baiyappanahalli",
    "Swami Vivekananda Road": "SV Road",
    "Mahatma Gandhi Road": "MG Road",
    "Dr. B R Ambedkar Station, Vidhana Soudha": "Vidhana Soudha",
    "Sir M Vishweshwariah - Central College": "Sir.M. Visveshwaraya",
    "Nadaprabhu Kempegowda Station, Majestic": "Kempegowda",
    "Krantivira Sangolli Rayanna": "Bangalore City Station",
    "Sri Balagangadaranatha Swamy, Hosahalli": "Hosahalli",
    "Vijayanagara": "Vijayanagar",
    "Mysore Road": "Mysuru Road",
    "Mahakavi Kuvempu Road": "Kuvempu Road",
    "Banashankari": "Banashankarl",
    "Rashtriya Vidyalaya Road": "RV Road",
    "Krishna Rajendra Market": "KR Market",
    "Chikkapete": "Chickpete",
    "Yeshwanthapura": "Yeshwanthpur",
    "J P Nagar": "JP Nagar",
    "Jnana Bharathi": "Jnanabharathi",
    "Nallurahalli": "Nallur Halli",
    "Pattanagere": "Pattangere",
    "Thalaghattapura": "Thalghattapura",
    "Goraguntepalya": "Yeshwanthpur Industry",
    "Yelachenahalli": "Puttenahalli",
}

# The 20 stations absent from the 63-station GPKG with their verified OSM coordinates
OSM_20_STATIONS: List[Dict] = [
    {"name": "BTM Layout", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6081182, "lat": 12.9165878},
    {"name": "Benniganahalli", "line": "Purple", "reason": "UNKNOWN", "lon": 77.6684788, "lat": 12.9964960},
    {"name": "Beratena Agrahara", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6579036, "lat": 12.8638780},
    {"name": "Biocon Hebbagodi", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6813744, "lat": 12.8290325},
    {"name": "Bommanahalli", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6264782, "lat": 12.9106157},
    {"name": "Central Silk Board", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6205670, "lat": 12.9165816},
    {"name": "Challaghatta", "line": "Purple", "reason": "UNKNOWN", "lon": 77.4612476, "lat": 12.8972890},
    {"name": "Chikkabidarakallu", "line": "Green", "reason": "UNKNOWN", "lon": 77.4879154, "lat": 13.0523616},
    {"name": "Delta Electronics Bommasandra", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6883453, "lat": 12.8193944},
    {"name": "Electronic City", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6635228, "lat": 12.8565053},
    {"name": "Hongasandra", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6319861, "lat": 12.9016952},
    {"name": "Hosa Road", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6524470, "lat": 12.8707491},
    {"name": "Huskur Road", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6773716, "lat": 12.8391572},
    {"name": "Infosys Foundation Konappana Agrahara", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6711872, "lat": 12.8464399},
    {"name": "Jayadeva Hospital", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.5999663, "lat": 12.9167310},
    {"name": "Kudlu Gate", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6392156, "lat": 12.8899259},
    {"name": "Madavara", "line": "Green", "reason": "UNKNOWN", "lon": 77.4728055, "lat": 13.0574214},
    {"name": "Manjunatha Nagar", "line": "Green", "reason": "UNKNOWN", "lon": 77.4944461, "lat": 13.0500898},
    {"name": "Ragigudda", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.5883015, "lat": 12.9170807},
    {"name": "Singasandra", "line": "Yellow", "reason": "Yellow Line opened to passengers on 11 Aug 2025", "lon": 77.6448456, "lat": 12.8808178}
]


def load_raw_ridership(excel_path: Path) -> pd.DataFrame:
    """Load and aggregate station-wise total boardings and average daily boardings for August 2025."""
    xl = pd.ExcelFile(excel_path)
    df = xl.parse(xl.sheet_names[0]).dropna(subset=["STATION"])
    
    # Strip numeric prefixes e.g. '11-Baiyappanahalli' -> 'Baiyappanahalli'
    df["station_name"] = df["STATION"].astype(str).str.replace(r"^\d+-", "", regex=True).str.strip()
    
    days = df.groupby("station_name")["BUSINESS DATE"].nunique()
    total = df.groupby("station_name")["TOTAL"].sum()
    avg_daily = total / days
    
    res = pd.DataFrame({
        "station_name": days.index,
        "days_of_data": days.values,
        "total_boardings": total.values,
        "avg_daily_boardings": avg_daily.values,
        "ridership": avg_daily.values
    })
    return res


def clean_stations(
    gpkg_path: str | Path = "data/raw/bengaluru_metro_stations.gpkg",
    ridership_path: str | Path = "data/raw/bmrcl_hourly_ridership_aug2025.xlsx",
    config_path: str | Path = "config/params.yaml",
    include_network_osm: bool = True
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Cleans raw metro stations (63 from GPKG + 20 from OSM), joins August 2025 ridership,
    sets pilot inclusion flag, and returns GeoDataFrames for all 83 stations and the pilot subset.
    """
    cfg = load_config(config_path)
    metric_crs = cfg["study"]["metric_crs"]
    pilot_names = set(cfg["study"]["stations_pilot"])
    selection_mode = cfg["study"].get("selection_mode", "pilot")
    
    # 1. Load stations GeoPackage (63 stations)
    raw_gdf = gpd.read_file(gpkg_path)
    gdf_metric = raw_gdf.to_crs(metric_crs)
    gdf_wgs84 = raw_gdf.to_crs("EPSG:4326")
    
    # 2. Load ridership
    ridership_df = load_raw_ridership(Path(ridership_path))
    ridership_lookup = dict(zip(ridership_df["station_name"].str.lower(), ridership_df["avg_daily_boardings"]))
    days_lookup = dict(zip(ridership_df["station_name"].str.lower(), ridership_df["days_of_data"]))
    total_lookup = dict(zip(ridership_df["station_name"].str.lower(), ridership_df["total_boardings"]))
    
    records = []
    unmatched_names = []
    
    for idx, row in raw_gdf.iterrows():
        raw_name = str(row["Name"]).strip()
        mapped_name = NAME_MAPPING.get(raw_name, raw_name)
        
        # Look up ridership
        r_val = ridership_lookup.get(mapped_name.lower())
        d_val = days_lookup.get(mapped_name.lower(), 18)
        t_val = total_lookup.get(mapped_name.lower())
        
        if r_val is None:
            for k, val in ridership_lookup.items():
                if mapped_name.lower() in k or k in mapped_name.lower():
                    r_val = val
                    d_val = days_lookup.get(k, 18)
                    t_val = total_lookup.get(k)
                    break
                    
        if r_val is None:
            unmatched_names.append(raw_name)
            
        geom_wgs = gdf_wgs84.loc[idx, "geometry"]
        geom_metric = gdf_metric.loc[idx, "geometry"]
        
        lon = float(geom_wgs.x)
        lat = float(geom_wgs.y)
        
        is_selected = True if selection_mode == "all" else (raw_name in pilot_names)
        
        records.append({
            "station_id": f"ST_{idx+1:03d}",
            "name": raw_name,
            "source": "GeoPackage",
            "lon": lon,
            "lat": lat,
            "node_walk": None,
            "node_bike": None,
            "node_drive": None,
            "snap_dist_walk_m": None,
            "snap_dist_bike_m": None,
            "snap_dist_drive_m": None,
            "days_of_data": int(d_val) if d_val is not None else 18,
            "total_boardings": float(t_val) if t_val is not None else np.nan,
            "ridership": float(r_val) if r_val is not None else np.nan,
            "include_flag": is_selected,
            "geometry": geom_metric
        })
        
    # 3. Add the 20 OSM stations if include_network_osm is True
    if include_network_osm:
        start_idx = len(records)
        df_20 = pd.DataFrame(OSM_20_STATIONS)
        gdf_20_wgs = gpd.GeoDataFrame(df_20, geometry=gpd.points_from_xy(df_20.lon, df_20.lat), crs="EPSG:4326")
        gdf_20_metric = gdf_20_wgs.to_crs(metric_crs)
        
        for idx, row in gdf_20_metric.iterrows():
            name = row["name"]
            mapped_name = NAME_MAPPING.get(name, name)
            r_val = ridership_lookup.get(mapped_name.lower())
            d_val = days_lookup.get(mapped_name.lower())
            t_val = total_lookup.get(mapped_name.lower())
            
            lon = float(row["lon"])
            lat = float(row["lat"])
            geom_metric = row["geometry"]
            
            is_selected = True if selection_mode == "all" else (name in pilot_names)
            
            records.append({
                "station_id": f"ST_{start_idx+idx+1:03d}",
                "name": name,
                "source": "OSM",
                "lon": lon,
                "lat": lat,
                "node_walk": None,
                "node_bike": None,
                "node_drive": None,
                "snap_dist_walk_m": None,
                "snap_dist_bike_m": None,
                "snap_dist_drive_m": None,
                "days_of_data": int(d_val) if d_val is not None else 0,
                "total_boardings": float(t_val) if t_val is not None else np.nan,
                "ridership": float(r_val) if r_val is not None else np.nan,
                "include_flag": is_selected,
                "geometry": geom_metric
            })
            
    all_stations_gdf = gpd.GeoDataFrame(records, crs=metric_crs)
    selected_stations_gdf = all_stations_gdf[all_stations_gdf["include_flag"]].copy().reset_index(drop=True)
    
    if selection_mode == "pilot":
        found_pilot_names = set(selected_stations_gdf["name"])
        missing_pilot = pilot_names - found_pilot_names
        if missing_pilot:
            raise ValueError(f"Requested pilot stations not found: {missing_pilot}")
        
    for _, st in all_stations_gdf.iterrows():
        if not (77.0 <= st["lon"] <= 78.5 and 12.0 <= st["lat"] <= 13.5):
            raise ValueError(f"Station {st['name']} has invalid Bengaluru coordinates: lon={st['lon']}, lat={st['lat']}")
            
    print(f"Station cleaning complete (mode: {selection_mode}):")
    print(f"  Total operational stations: {len(all_stations_gdf)} (63 GPKG + {len(all_stations_gdf)-63} OSM)")
    print(f"  Matched with ridership: {all_stations_gdf['ridership'].notna().sum()} / {len(all_stations_gdf)}")
    print(f"  Stations selected: {len(selected_stations_gdf)}")
    
    return all_stations_gdf, selected_stations_gdf


def export_station_tables(output_dir: str | Path = "data/interim", network_dir: str | Path = "data/output_network") -> None:
    """Run cleaning and export CSV and GPKG tables."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    net_out = Path(network_dir)
    net_out.mkdir(parents=True, exist_ok=True)
    
    all_gdf, selected_gdf = clean_stations()
    
    # Export all 83 stations to network directory and interim
    all_gdf.drop(columns=["geometry"]).to_csv(net_out / "stations_83_network.csv", index=False)
    all_gdf.to_file(net_out / "stations_83_network.gpkg", driver="GPKG")
    all_gdf.drop(columns=["geometry"]).to_csv(out / "stations_all.csv", index=False)
    all_gdf.to_file(out / "stations_all.gpkg", driver="GPKG")
    
    # Preserve pilot tables
    pilot_gdf = all_gdf[all_gdf["name"].isin(load_config()["study"]["stations_pilot"])].copy().reset_index(drop=True)
    pilot_gdf.drop(columns=["geometry"]).to_csv(out / "stations_pilot.csv", index=False)
    pilot_gdf.to_file(out / "stations_pilot.gpkg", driver="GPKG")
    
    print(f"Exported station tables to {out.resolve()} and {net_out.resolve()}")


if __name__ == "__main__":
    export_station_tables()
