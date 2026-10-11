import geopandas as gpd
import pandas as pd
import numpy as np

cells = gpd.read_file("data/output/cells.gpkg")
corr = cells[cells["is_corridor_assigned"] == True].copy()
c_pop = corr["population"].sum()

walk_speeds = [4.0, 4.5, 5.0]
ebike_speeds = [12.0, 13.5, 15.0]

print("==========================================================================================")
print("SPEED SENSITIVITY MATRIX: WALKING (4.0, 4.5, 5.0 km/h) x E-BIKE (12.0, 13.5, 15.0 km/h)")
print(f"Core Corridor Territory: {c_pop:,.0f} residents")
print("==========================================================================================")

for t in [15.0, 20.0]:
    print(f"\n--- TRAVEL TIME THRESHOLD T = {t:.0f} MIN ---")
    matrix_data = []
    for ws in walk_speeds:
        # Scale walk time relative to 4.5 km/h baseline
        scale_w = 4.5 / ws
        w_time = corr["walk_time_min"] * scale_w
        w_cov = w_time <= t
        w_pop = corr[w_cov]["population"].sum()
        
        row = {"Walk Speed (km/h)": f"{ws:.1f} km/h (Walk: {w_pop:,.0f} / {w_pop/c_pop*100:.1f}%)"}
        for bs in ebike_speeds:
            # Scale ebike riding time (excluding 5 min overhead)
            # ebike_time = (default_ebike_time - 5.0) * (13.5 / bs) + 5.0
            ebike_ride_time = np.maximum(0.0, corr["ebike_time_min"] - 5.0) * (13.5 / bs)
            ebike_total_time = ebike_ride_time + 5.0
            e_cov = ebike_total_time <= t
            
            # Incremental e-bike uplift (reachable by e-bike but not by walk)
            e_uplift = e_cov & (~w_cov)
            e_up_pop = corr[e_uplift]["population"].sum()
            total_reach = corr[w_cov | e_cov]["population"].sum()
            
            row[f"E-Bike {bs:.1f} km/h"] = f"+{e_up_pop:,.0f} (+{e_up_pop/c_pop*100:.1f}%) [Tot: {total_reach/c_pop*100:.1f}%]"
        matrix_data.append(row)
    
    df_matrix = pd.DataFrame(matrix_data)
    print(df_matrix.to_string(index=False))

# Also export as CSV
matrix_all = []
for t in [15.0, 20.0]:
    for ws in walk_speeds:
        scale_w = 4.5 / ws
        w_time = corr["walk_time_min"] * scale_w
        w_cov = w_time <= t
        w_pop = corr[w_cov]["population"].sum()
        for bs in ebike_speeds:
            ebike_ride_time = np.maximum(0.0, corr["ebike_time_min"] - 5.0) * (13.5 / bs)
            ebike_total_time = ebike_ride_time + 5.0
            e_cov = ebike_total_time <= t
            e_uplift = e_cov & (~w_cov)
            e_up_pop = corr[e_uplift]["population"].sum()
            total_reach = corr[w_cov | e_cov]["population"].sum()
            matrix_all.append({
                "threshold_min": t,
                "walk_speed_kmh": ws,
                "ebike_speed_kmh": bs,
                "walk_covered_pop": round(w_pop, 1),
                "walk_covered_pct": round(w_pop / c_pop * 100, 1),
                "ebike_uplift_pop": round(e_up_pop, 1),
                "ebike_uplift_pct": round(e_up_pop / c_pop * 100, 1),
                "total_walk_ebike_pop": round(total_reach, 1),
                "total_walk_ebike_pct": round(total_reach / c_pop * 100, 1)
            })

pd.DataFrame(matrix_all).to_csv("data/output/speed_sensitivity_matrix.csv", index=False)
print("\nExported full speed matrix to data/output/speed_sensitivity_matrix.csv!")
