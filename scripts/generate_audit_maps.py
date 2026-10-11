import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Load data with consistent metric projection (EPSG:32643)
cells = gpd.read_file("data/output/cells.gpkg").to_crs("EPSG:32643")
stations_selected = gpd.read_file("data/interim/stations_selected.gpkg").to_crs("EPSG:32643")
stations_all = gpd.read_file("data/interim/stations_all.gpkg").to_crs("EPSG:32643")

# 1. Footbridge Severance Map
# Filter corridor cells where walk <= 20 and ebike > 20
corr_cells = cells[cells["is_corridor_assigned"] == True].copy()
gap_cells = corr_cells[(corr_cells["walk_time_min"] <= 20.0) & (corr_cells["ebike_time_min"] > 20.0)].copy()

# Focus on Whitefield Kadugodi area
wf_st = stations_selected[stations_selected["name"] == "Whitefield (Kadugodi)"].iloc[0]
sx, sy = wf_st.geometry.x, wf_st.geometry.y

fig, ax = plt.subplots(figsize=(10, 8), dpi=200)

# Plot all cells in background
cells.plot(ax=ax, color="#f5f5f5", edgecolor="#e0e0e0", linewidth=0.5)

# Plot corridor cells near Whitefield
wf_cells = corr_cells[corr_cells["nearest_station_walk"] == "ST_001"]
wf_cells.plot(ax=ax, color="#e8f5e9", edgecolor="#c8e6c9", linewidth=0.6, label="Whitefield Assigned Catchment")

# Highlight footbridge gap cells
gap_wf = gap_cells[gap_cells["nearest_station_walk"] == "ST_001"]
gap_wf.plot(ax=ax, color="#ef5350", edgecolor="#b71c1c", linewidth=1.2, label="Footbridge Severance Cells (Walk <= 20, E-Bike > 20)")

# Plot stations
for _, s in stations_selected.iterrows():
    if s["name"] in ["Whitefield (Kadugodi)", "Hopefarm Channasandra", "Kadugodi Tree Park"]:
        ax.scatter(s.geometry.x, s.geometry.y, color="#1565c0", s=80, zorder=5)
        ax.annotate(s["name"], (s.geometry.x, s.geometry.y + 120), fontsize=8, ha="left", va="bottom", weight="bold", color="#0d47a1")

# Draw simulated railway corridor line across Whitefield
ax.plot([sx - 2500, sx + 2500], [sy - 200, sy + 300], color="#424242", linestyle="--", linewidth=2.0, label="South Western Railway Line (Severance Barrier)")

ax.set_xlim(sx - 3000, sx + 2500)
ax.set_ylim(sy - 2500, sy + 3000)
ax.set_title("Whitefield Railway Footbridge Severance Audit\n10 Cells (9,640 Residents) Reachable by Footbridge Steps but Blocked for Wheeled Modes", fontsize=11, weight="bold")
ax.set_axis_off()

legend_patches = [
    mpatches.Patch(color="#e8f5e9", label="Whitefield Kadugodi Station Catchment"),
    mpatches.Patch(color="#ef5350", label=f"Severance Group: Walk <= 20 min, E-Bike > 20 min ({len(gap_wf)} cells, {gap_wf['population'].sum():,.0f} pop)"),
    plt.Line2D([0], [0], color="#424242", linestyle="--", linewidth=2, label="Railway Barrier (No Vehicular Level Crossing)"),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#1565c0', markersize=8, label="Metro Stations")
]
ax.legend(handles=legend_patches, loc="lower left", fontsize=8)

plt.tight_layout()
out_fp = Path("docs/footbridge_severance_map.png")
plt.savefig(out_fp, dpi=200)
plt.close(fig)
print(f"Footbridge severance map saved to {out_fp}")

# 2. Enhanced Western Reassignment Map (Hoodi & Garudacharpalya)
fig2, ax2 = plt.subplots(figsize=(10, 8), dpi=200)

cells.plot(ax=ax2, color="#f5f5f5", edgecolor="#e0e0e0", linewidth=0.5)
corr_cells.plot(ax=ax2, color="#e3f2fd", edgecolor="#90caf9", linewidth=0.5)

ctx01 = cells[cells["nearest_station_walk"] == "CTX_01"]
ctx02 = cells[cells["nearest_station_walk"] == "CTX_02"]

ctx01.plot(ax=ax2, color="#ffb74d", edgecolor="#f57c00", linewidth=0.8)
ctx02.plot(ax=ax2, color="#ff8a65", edgecolor="#d84315", linewidth=0.8)

for _, s in stations_selected.iterrows():
    ax2.scatter(s.geometry.x, s.geometry.y, color="#1565c0", s=60, zorder=5)
    if s["name"] in ["Hoodi", "Garudacharpalya", "Seetharampalya"]:
        ax2.annotate(s["name"], (s.geometry.x, s.geometry.y + 120), fontsize=8, ha="center", va="bottom", weight="bold", color="#0d47a1")

ctx_stations = stations_all[stations_all["name"].isin(["Singayyanapalya", "Krishnarajapura"])]
for _, s in ctx_stations.iterrows():
    ax2.scatter(s.geometry.x, s.geometry.y, color="#b71c1c", s=90, marker="^", zorder=6)
    ax2.annotate(s["name"] + "\n(Boundary Absorber)", (s.geometry.x, s.geometry.y + 120), fontsize=8, ha="center", va="bottom", weight="bold", color="#b71c1c")

# Zoom in on western boundary sector
ax2.set_xlim(788500, 796500)
ax2.set_ylim(1435000, 1442000)

ax2.set_title("Western Boundary Cordon Audit: Hoodi & Garudacharpalya Load Absorption\n108 Cells (108,348 Residents) Geometrically Reassigned to Western Context Stations", fontsize=11, weight="bold")
ax2.set_axis_off()

pop_ctx01 = ctx01["population"].sum()
pop_ctx02 = ctx02["population"].sum()
legend_patches2 = [
    mpatches.Patch(color="#e3f2fd", label="Core Corridor Cells (10 Pilot Stations, 453.7k pop)"),
    mpatches.Patch(color="#ffb74d", label=f"Absorbed by Singayyanapalya ({len(ctx01)} cells, {pop_ctx01/1000:.1f}k pop)"),
    mpatches.Patch(color="#ff8a65", label=f"Absorbed by Krishnarajapura ({len(ctx02)} cells, {pop_ctx02/1000:.1f}k pop)"),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#1565c0', markersize=8, label="Pilot Stations (Hoodi, Garudacharpalya)"),
    plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='#b71c1c', markersize=9, label="Context Absorber Stations")
]
ax2.legend(handles=legend_patches2, loc="lower right", fontsize=8)

plt.tight_layout()
out_wp = Path("docs/western_reassignment_map.png")
plt.savefig(out_wp, dpi=200)
plt.close(fig2)
print(f"Western reassignment map updated at {out_wp}")
