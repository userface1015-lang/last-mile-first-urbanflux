import geopandas as gpd
import pandas as pd

cells = gpd.read_file("data/output/cells.gpkg")
corr = cells[cells["is_corridor_assigned"] == True]
gap = corr[(corr["walk_time_min"] <= 20.0) & (corr["ebike_time_min"] > 20.0)]
print(f"Total corridor cells with walk <= 20 and ebike > 20: {len(gap)}")
pop_sum = gap["population"].sum()
print(f"Total population in this gap: {pop_sum:,.1f}")
print("\nBreakdown by nearest walk station:")
print(gap["nearest_station_walk"].value_counts())
print("\nDetails of each cell in the gap:")
for _, r in gap.iterrows():
    cid = r["cell_id"]
    pop = r["population"]
    wt = r["walk_time_min"]
    bt = r["ebike_time_min"]
    sw = r["nearest_station_walk"]
    sb = r["nearest_station_ebike"]
    print(f"Cell {cid}: pop={pop:5.1f}, walk={wt:5.2f}m, ebike={bt:5.2f}m, st_walk={sw}, st_bike={sb}")
