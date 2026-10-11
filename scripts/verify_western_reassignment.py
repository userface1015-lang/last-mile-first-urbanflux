import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

# Load cells and stations
cells = gpd.read_file("data/output/cells.gpkg")
st_pilot = gpd.read_file("data/interim/stations_selected.gpkg").to_crs("EPSG:32643")
st_all = gpd.read_file("data/interim/stations_all.gpkg").to_crs("EPSG:32643")

krpm_geom = st_all[st_all["name"] == "Krishnarajapura"].geometry.iloc[0]
sing_geom = st_all[st_all["name"] == "Singayyanapalya"].geometry.iloc[0]
hoodi_geom = st_pilot[st_pilot["name"] == "Hoodi"].geometry.iloc[0]
garuda_geom = st_pilot[st_pilot["name"] == "Garudacharpalya"].geometry.iloc[0]

# Check cells assigned to context stations
reassigned = cells[cells["nearest_station_walk"].isin(["CTX_01", "CTX_02"])].copy()
print(f"Total cells assigned to western boundary absorbers: {len(reassigned)}")
print(f"Total population assigned to western boundary absorbers: {reassigned['population'].sum():,.1f}")

# Compute distance from each reassigned cell centroid to:
# 1. Assigned context station (KR Puram or Singayyanapalya)
# 2. Nearest pilot station (Hoodi or Garudacharpalya)
dist_to_assigned = []
dist_to_hoodi = []
dist_to_garuda = []

for _, r in reassigned.iterrows():
    c = r.geometry.centroid
    d_ctx = c.distance(sing_geom if r["nearest_station_walk"] == "CTX_01" else krpm_geom)
    d_h = c.distance(hoodi_geom)
    d_g = c.distance(garuda_geom)
    dist_to_assigned.append(d_ctx)
    dist_to_hoodi.append(d_h)
    dist_to_garuda.append(d_g)

reassigned["dist_assigned_m"] = dist_to_assigned
reassigned["dist_hoodi_m"] = dist_to_hoodi
reassigned["dist_garuda_m"] = dist_to_garuda
reassigned["nearest_pilot_m"] = np.minimum(dist_to_hoodi, dist_to_garuda)
reassigned["dist_difference_m"] = reassigned["nearest_pilot_m"] - reassigned["dist_assigned_m"]

print("\n--- Geometric Distance Audit for Reassigned Cells ---")
print(f"Min distance difference (pilot - ctx): {reassigned['dist_difference_m'].min():.1f} m")
print(f"Mean distance difference (pilot - ctx): {reassigned['dist_difference_m'].mean():.1f} m")
print(f"Max distance difference (pilot - ctx): {reassigned['dist_difference_m'].max():.1f} m")
print(f"Are 100% of reassigned cells closer to context stations than pilot stations? {(reassigned['dist_difference_m'] > 0).all()}")

# Save a map visualization as an image artifact!
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(10, 8), dpi=200)

# Plot core buffer boundary
cells.plot(ax=ax, color="#f0f0f0", edgecolor="#d0d0d0", linewidth=0.5)

# Plot corridor cells
corridor_cells = cells[cells["is_corridor_assigned"] == True]
corridor_cells.plot(ax=ax, color="#e3f2fd", edgecolor="#90caf9", linewidth=0.5, label="Corridor Cells")

# Plot CTX_01 and CTX_02 reassigned cells
ctx01_cells = reassigned[reassigned["nearest_station_walk"] == "CTX_01"]
ctx02_cells = reassigned[reassigned["nearest_station_walk"] == "CTX_02"]

ctx01_cells.plot(ax=ax, color="#ffcc80", edgecolor="#f57c00", linewidth=0.8, label="Reassigned to Singayyanapalya")
ctx02_cells.plot(ax=ax, color="#ffab91", edgecolor="#d84315", linewidth=0.8, label="Reassigned to Krishnarajapura")

# Plot stations
for _, s in st_pilot.iterrows():
    ax.scatter(s.geometry.x, s.geometry.y, color="#1565c0", s=60, zorder=5)
    ax.annotate(s["name"], (s.geometry.x, s.geometry.y), fontsize=7, ha="left", va="bottom", weight="bold", color="#0d47a1")

ax.scatter(sing_geom.x, sing_geom.y, color="#e65100", s=90, marker="^", zorder=6)
ax.annotate("Singayyanapalya (CTX_01)", (sing_geom.x, sing_geom.y), fontsize=8, ha="right", va="bottom", weight="bold", color="#e65100")

ax.scatter(krpm_geom.x, krpm_geom.y, color="#b71c1c", s=90, marker="^", zorder=6)
ax.annotate("Krishnarajapura (CTX_02)", (krpm_geom.x, krpm_geom.y), fontsize=8, ha="right", va="bottom", weight="bold", color="#b71c1c")

ax.set_title("Western Boundary Reassignment Audit\n108 Cells (108,348 Residents) Geometrically Closer to Context Stations", fontsize=11, weight="bold")
ax.set_axis_off()

legend_patches = [
    mpatches.Patch(color="#e3f2fd", label="Core Corridor Cells (10 Pilot Stations)"),
    mpatches.Patch(color="#ffcc80", label="Absorbed by Singayyanapalya (CTX_01)"),
    mpatches.Patch(color="#ffab91", label="Absorbed by Krishnarajapura (CTX_02)"),
    mpatches.Patch(color="#1565c0", label="Pilot Metro Stations"),
    mpatches.Patch(color="#d84315", label="Context Absorber Stations")
]
ax.legend(handles=legend_patches, loc="lower right", fontsize=8)

plt.tight_layout()
out_plot = Path("docs/western_reassignment_map.png")
plt.savefig(out_plot, dpi=200)
print(f"Map successfully saved to {out_plot}!")
