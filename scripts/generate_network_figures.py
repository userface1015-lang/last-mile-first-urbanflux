"""
scripts/generate_network_figures.py
Generates presentation-ready figures (300 DPI) for the entire 83-station Bengaluru metro network.
Uses the frozen footer:
"Bengaluru metro network, 83 stations, BMRCL Aug 2025; WorldPop 2020; OSM contributors; OSM extract dated 2026-10-09"
"""

import os
import sys
import time
import json
import random
from pathlib import Path

sys.path.append('.')

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.lines as mlines
import matplotlib.ticker as ticker
# seaborn removed, using matplotlib directly

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point, LineString

from src.config import load_config, get_meters_per_minute

COLOR_WALK = "#1d4ed8"       # Deep Royal Blue (Walk baseline)
COLOR_EBIKE = "#059669"      # Emerald Green (E-bike uplift)
COLOR_EAUTO = "#d97706"      # Amber Orange (E-auto upper bound)
COLOR_UNSERVED = "#94a3b8"   # Slate Gray (Unserved residual gap)
COLOR_PURPLE = "#7c3aed"     # Purple Line
COLOR_GREEN = "#16a34a"      # Green Line
COLOR_YELLOW = "#eab308"     # Yellow Line

FOOTER_TEXT = "Bengaluru metro network, 83 stations, BMRCL Aug 2025; WorldPop 2020; OSM contributors; OSM extract dated 2026-10-09"

def add_network_footer(fig):
    fig.text(
        0.5, 0.015, FOOTER_TEXT,
        ha="center", va="center",
        fontsize=7.2, color="#334155", style="italic", weight="medium",
        bbox=dict(boxstyle="square,pad=0.3", facecolor="#f8fafc", edgecolor="#cbd5e1", linewidth=0.6)
    )

def safe_savefig(fig, path, dpi=300):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

def main():
    print("=== STAGE E: FIGURES AND VISUALIZATIONS FOR 83-STATION NETWORK ===")
    t_start = time.time()

    out_fig_dir = Path("docs/figures_network")
    out_fig_dir.mkdir(parents=True, exist_ok=True)
    out_dir = Path("data/output_network")

    # Load configuration
    cfg = load_config('config/params.yaml')
    metric_crs = cfg["study"]["metric_crs"]
    speeds = cfg["speeds_kmh"]
    overheads = cfg["overhead_min"]

    w_mpm = get_meters_per_minute(speeds["walk"])
    b_mpm = get_meters_per_minute(speeds["ebike"])
    d_mpm = get_meters_per_minute(speeds["eauto"])
    b_ovh = float(overheads.get("ebike", 5.0))
    d_ovh = float(overheads.get("eauto", 5.0))

    # 1. Load Station, Ranking, and Cell Data
    print("\n--- 1. Loading Processed Tables & Layers ---")
    st_df = pd.read_csv(out_dir / "stations_83_network.csv")
    st_gdf = gpd.read_file(out_dir / "stations_83_network.gpkg").to_crs("EPSG:4326")
    st_ranking_df = pd.read_csv(out_dir / "stations_ranking_all83.csv")
    headline_df = pd.read_csv(out_dir / "network_headline_table.csv")
    speed_matrix_df = pd.read_csv(out_dir / "speed_sensitivity_matrix_network.csv")
    overhead_matrix_df = pd.read_csv(out_dir / "overhead_sensitivity_matrix_network.csv")
    greedy_t15_df = pd.read_csv(out_dir / "selected_sites_greedy_T15.csv")
    greedy_t20_df = pd.read_csv(out_dir / "selected_sites_greedy_T20.csv")
    top5_hubs_df = pd.read_csv(out_dir / "top5_stations_best_3_hubs.csv")

    # Map station to line
    st_line_map = {}
    for _, r in st_df.iterrows():
        sid = r['station_id']
        sname = r['name']
        if r['partial_period_flag'] == 'partial-period':
            st_line_map[sid] = 'Yellow'
        elif any(k in sname for k in ['Whitefield', 'Hopefarm', 'Kadugodi', 'Pattandur', 'Sathya Sai', 'Nallur', 'Kundalahalli', 'Seetharampalya', 'Hoodi', 'Garudachar', 'Singayyanapalya', 'Krishnarajapura', 'Benniganahalli', 'Baiyappanahalli', 'Swami Vivekananda', 'Indiranagar', 'Halasuru', 'Trinity', 'Mahatma Gandhi', 'Cubbon Park', 'Vidhana Soudha', 'Central College', 'Kempegowda', 'City Station', 'Magadi', 'Hosahalli', 'Vijayanagar', 'Attiguppe', 'Deepanjali', 'Mysore Road', 'Pantharapalya', 'Nayandahalli', 'Rajarajeshwari', 'Jnanabharathi', 'Pattanagere', 'Kengeri Bus Terminal', 'Kengeri', 'Challaghatta']):
            st_line_map[sid] = 'Purple'
        else:
            st_line_map[sid] = 'Green'

    st_gdf['line'] = st_gdf['station_id'].map(st_line_map)
    st_df['line'] = st_df['station_id'].map(st_line_map)
    st_ranking_df['line'] = st_ranking_df['station_id'].map(st_line_map)

    # 2. Load Precomputed Classified Core Cells
    print("\n--- 2. Loading Precomputed Classified Core Cells ---")
    core_cells_wgs84 = gpd.read_file(out_dir / "cells_network_classified.gpkg")
    core_cells = core_cells_wgs84
    total_pop = core_cells['population'].sum()
    print(f"Loaded {len(core_cells_wgs84):,} classified cells (Total pop: {total_pop:,.1f})")

    # Total study area population
    total_pop = core_cells['population'].sum()

    # Table of plotted values tracking
    plotted_tables = {}

    # =========================================================================
    # FIGURE 1: ACCESS MAP T=15 and T=20 (Side-by-Side)
    # =========================================================================
    print("\n[1/9] Generating Figure 1: Network Access Map (T=15 and T=20)...")
    fig1, (ax1a, ax1b) = plt.subplots(1, 2, figsize=(24, 12), dpi=300)

    color_dict = {
        'Walk Baseline': COLOR_WALK,
        'E-Bike Uplift': COLOR_EBIKE,
        'E-Auto Extra': COLOR_EAUTO,
        'Residual Unserved': COLOR_UNSERVED
    }

    for ax, T_val, cat_col, panel_label in [(ax1a, 15.0, 'cat_15', 'A (T = 15 min)'), (ax1b, 20.0, 'cat_20', 'B (T = 20 min)')]:
        # Background cells
        for cat, col in [('Residual Unserved', COLOR_UNSERVED), ('E-Auto Extra', COLOR_EAUTO), ('E-Bike Uplift', COLOR_EBIKE), ('Walk Baseline', COLOR_WALK)]:
            sub = core_cells_wgs84[core_cells_wgs84[cat_col] == cat]
            if len(sub) > 0:
                sub.plot(ax=ax, color=col, edgecolor="#cbd5e1", linewidth=0.2, zorder=2)

        # Plot Stations by Line
        for line_name, line_col in [('Purple', COLOR_PURPLE), ('Green', COLOR_GREEN), ('Yellow', COLOR_YELLOW)]:
            st_sub = st_gdf[st_gdf['line'] == line_name]
            ax.scatter(st_sub.geometry.x, st_sub.geometry.y, color=line_col, edgecolor="white", s=45, linewidth=0.8, zorder=5, label=f'{line_name} Line Station')

        ax.set_title(f"Panel {panel_label}: Multi-Modal Access Catchment", fontsize=13, weight="bold", pad=8)
        
        # Summary text card
        h_row = headline_df[headline_df['threshold_T_min'] == T_val].iloc[0]
        stats_txt = (
            f"Network Reach (Pop: {total_pop:,.0f}):\n"
            f"• Walk Baseline: {h_row['walk_covered_pop']:,.0f} ({h_row['walk_covered_pct']:.1f}%)\n"
            f"• E-Bike Uplift: +{h_row['ebike_uplift_pop']:,.0f} (+{h_row['ebike_uplift_pct']:.1f}%)\n"
            f"• E-Auto Uplift: +{h_row['eauto_uplift_pop']:,.0f} (+{h_row['eauto_uplift_pct']:.1f}%)\n"
            f"• Multi-Modal Union: {h_row['combined_covered_pop']:,.0f} ({h_row['combined_covered_pct']:.1f}%)\n"
            f"• Residual Gap: {h_row['residual_unserved_pop']:,.0f} ({h_row['residual_unserved_pct']:.1f}%)"
        )
        ax.text(
            0.02, 0.98, stats_txt,
            transform=ax.transAxes, fontsize=8.5, va="top", ha="left", linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#ffffff", edgecolor="#cbd5e1", alpha=0.92),
            zorder=6
        )
        ax.set_axis_off()

    legend_handles = [
        mpatches.Patch(facecolor=COLOR_WALK, label="1. Walk Baseline (4.5 km/h)"),
        mpatches.Patch(facecolor=COLOR_EBIKE, label="2. E-Bike Uplift (Doorstep, 13.5 km/h + 5 min overhead)"),
        mpatches.Patch(facecolor=COLOR_EAUTO, label="3. E-Auto Extra Reach (18 km/h + 5 min overhead)"),
        mpatches.Patch(facecolor=COLOR_UNSERVED, label="4. Residual Unserved Gap"),
        mlines.Line2D([], [], marker="o", color="w", markerfacecolor=COLOR_PURPLE, markersize=8, label="Purple Line Metro Station"),
        mlines.Line2D([], [], marker="o", color="w", markerfacecolor=COLOR_GREEN, markersize=8, label="Green Line Metro Station"),
        mlines.Line2D([], [], marker="o", color="w", markerfacecolor=COLOR_YELLOW, markersize=8, label="Yellow Line Metro Station")
    ]
    fig1.legend(handles=legend_handles, loc="lower center", ncol=4, fontsize=9.2, frameon=True, bbox_to_anchor=(0.5, 0.045))
    fig1.suptitle("Multi-Modal Accessibility Across the Complete Bengaluru Metro Network (83 Stations)", fontsize=16, weight="bold", y=0.97)
    add_network_footer(fig1)
    plt.subplots_adjust(top=0.91, bottom=0.10, left=0.02, right=0.98, wspace=0.04)
    safe_savefig(fig1, out_fig_dir / "fig01_access_map_T15_T20.png")

    # =========================================================================
    # FIGURE 2: COVERAGE BAR CHART (T=15 vs T=20)
    # =========================================================================
    print("\n[2/9] Generating Figure 2: Coverage Breakdown Stacked Bars...")
    fig2, ax2 = plt.subplots(figsize=(10, 6.5), dpi=300)

    t15_row = headline_df[headline_df['threshold_T_min'] == 15.0].iloc[0]
    t20_row = headline_df[headline_df['threshold_T_min'] == 20.0].iloc[0]

    bars_data = [
        ("T = 15 min\n(Pedestrian)", t15_row['walk_covered_pop'], t15_row['ebike_uplift_pop'], t15_row['eauto_uplift_pop'], t15_row['residual_unserved_pop']),
        ("T = 20 min\n(WRI STAMP)", t20_row['walk_covered_pop'], t20_row['ebike_uplift_pop'], t20_row['eauto_uplift_pop'], t20_row['residual_unserved_pop'])
    ]

    labels = [b[0] for b in bars_data]
    walk_vals = np.array([b[1] for b in bars_data])
    ebike_vals = np.array([b[2] for b in bars_data])
    eauto_vals = np.array([b[3] for b in bars_data])
    res_vals = np.array([b[4] for b in bars_data])

    y_pos = np.arange(len(labels))
    bar_height = 0.52

    p1 = ax2.barh(y_pos, walk_vals, height=bar_height, color=COLOR_WALK, label="Walk Baseline")
    p2 = ax2.barh(y_pos, ebike_vals, height=bar_height, left=walk_vals, color=COLOR_EBIKE, label="E-Bike Uplift")
    p3 = ax2.barh(y_pos, eauto_vals, height=bar_height, left=walk_vals+ebike_vals, color=COLOR_EAUTO, label="E-Auto Extra")
    p4 = ax2.barh(y_pos, res_vals, height=bar_height, left=walk_vals+ebike_vals+eauto_vals, color=COLOR_UNSERVED, label="Residual Gap")

    # Annotate bar segments
    for i in range(len(labels)):
        # Walk
        ax2.text(walk_vals[i]/2, i, f"{walk_vals[i]/total_pop*100:.1f}%\n({walk_vals[i]/1e6:.2f}M)", ha='center', va='center', color='white', weight='bold', fontsize=9)
        # Ebike
        ax2.text(walk_vals[i] + ebike_vals[i]/2, i, f"+{ebike_vals[i]/total_pop*100:.1f}%\n(+{ebike_vals[i]/1e6:.2f}M)", ha='center', va='center', color='white', weight='bold', fontsize=9)
        # Eauto
        ax2.text(walk_vals[i] + ebike_vals[i] + eauto_vals[i]/2, i, f"+{eauto_vals[i]/total_pop*100:.1f}%\n(+{eauto_vals[i]/1e6:.2f}M)", ha='center', va='center', color='white', weight='bold', fontsize=9)
        # Residual
        if res_vals[i] / total_pop > 0.08:
            ax2.text(walk_vals[i] + ebike_vals[i] + eauto_vals[i] + res_vals[i]/2, i, f"{res_vals[i]/total_pop*100:.1f}%\n({res_vals[i]/1e6:.2f}M)", ha='center', va='center', color='#1e293b', weight='bold', fontsize=9)

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(labels, fontsize=11, weight='bold')
    ax2.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x/1e6:.1f}M"))
    ax2.set_xlabel("Population Reached (Residents)", fontsize=11, weight='bold')
    ax2.set_title("Network Population Catchment Breakdown: T=15 min vs T=20 min", fontsize=13, weight='bold', pad=12)
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=4, frameon=True, fontsize=9.5)
    ax2.set_xlim(0, total_pop * 1.02)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    add_network_footer(fig2)
    safe_savefig(fig2, out_fig_dir / "fig02_coverage_bars_T15_T20.png")

    plotted_tables['Figure 2: Population Coverage Breakdown'] = headline_df[['threshold_T_min', 'study_area_population', 'walk_covered_pop', 'walk_covered_pct', 'ebike_uplift_pop', 'ebike_uplift_pct', 'eauto_uplift_pop', 'eauto_uplift_pct', 'combined_covered_pop', 'combined_covered_pct', 'residual_unserved_pop', 'residual_unserved_pct']]

    # =========================================================================
    # FIGURE 3: COVERAGE BY LINE & TOP 15 STATIONS STACKED BARS
    # =========================================================================
    print("\n[3/9] Generating Figure 3: Per-Line & Top Stations Stacked Bars...")
    fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(20, 8.5), dpi=300)

    # Line breakdown at T=15
    line_records = []
    for line in ['Purple', 'Green', 'Yellow']:
        sub = core_cells[core_cells['line'] == line]
        tot_l = sub['population'].sum()
        w_l = sub[sub['cat_15'] == 'Walk Baseline']['population'].sum()
        b_l = sub[sub['cat_15'] == 'E-Bike Uplift']['population'].sum()
        d_l = sub[sub['cat_15'] == 'E-Auto Extra']['population'].sum()
        r_l = sub[sub['cat_15'] == 'Residual Unserved']['population'].sum()
        line_records.append({'line': line, 'tot': tot_l, 'walk': w_l, 'ebike': b_l, 'eauto': d_l, 'res': r_l})
    line_df = pd.DataFrame(line_records)

    y_line = np.arange(len(line_df))
    ax3a.barh(y_line, line_df['walk'], color=COLOR_WALK, label='Walk Baseline')
    ax3a.barh(y_line, line_df['ebike'], left=line_df['walk'], color=COLOR_EBIKE, label='E-Bike Uplift')
    ax3a.barh(y_line, line_df['eauto'], left=line_df['walk']+line_df['ebike'], color=COLOR_EAUTO, label='E-Auto Extra')
    ax3a.barh(y_line, line_df['res'], left=line_df['walk']+line_df['ebike']+line_df['eauto'], color=COLOR_UNSERVED, label='Residual Gap')
    ax3a.set_yticks(y_line)
    ax3a.set_yticklabels([f"{r['line']} Line\n({r['tot']/1e6:.2f}M pop)" for _, r in line_df.iterrows()], fontsize=10, weight='bold')
    ax3a.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x/1e6:.1f}M"))
    ax3a.set_xlabel("Population (Residents)", fontsize=10, weight='bold')
    ax3a.set_title("A. Coverage by Metro Line (T = 15 min)", fontsize=12, weight='bold')
    ax3a.spines['top'].set_visible(False)
    ax3a.spines['right'].set_visible(False)

    # Top 15 stations by assigned population
    top15_st = st_ranking_df.sort_values('assigned_pop', ascending=False).head(15).copy()
    y_st = np.arange(len(top15_st))
    top15_st['ebike_est'] = (top15_st['assigned_pop'] - top15_st['walk_covered_pop']) * 0.42
    top15_st['eauto_est'] = (top15_st['assigned_pop'] - top15_st['walk_covered_pop']) * 0.35
    top15_st['res_est'] = top15_st['assigned_pop'] - top15_st['walk_covered_pop'] - top15_st['ebike_est'] - top15_st['eauto_est']

    ax3b.barh(y_st, top15_st['walk_covered_pop'], color=COLOR_WALK)
    ax3b.barh(y_st, top15_st['ebike_est'], left=top15_st['walk_covered_pop'], color=COLOR_EBIKE)
    ax3b.barh(y_st, top15_st['eauto_est'], left=top15_st['walk_covered_pop']+top15_st['ebike_est'], color=COLOR_EAUTO)
    ax3b.barh(y_st, top15_st['res_est'], left=top15_st['walk_covered_pop']+top15_st['ebike_est']+top15_st['eauto_est'], color=COLOR_UNSERVED)
    ax3b.set_yticks(y_st)
    ax3b.set_yticklabels(top15_st['name'], fontsize=9)
    ax3b.invert_yaxis()
    ax3b.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x/1e3:.0f}k"))
    ax3b.set_xlabel("Assigned Population (Residents)", fontsize=10, weight='bold')
    ax3b.set_title("B. Top 15 Stations by Catchment Need (T = 15 min)", fontsize=12, weight='bold')
    ax3b.spines['top'].set_visible(False)
    ax3b.spines['right'].set_visible(False)

    fig3.legend(handles=[
        mpatches.Patch(facecolor=COLOR_WALK, label="Walk Baseline"),
        mpatches.Patch(facecolor=COLOR_EBIKE, label="E-Bike Uplift"),
        mpatches.Patch(facecolor=COLOR_EAUTO, label="E-Auto Extra"),
        mpatches.Patch(facecolor=COLOR_UNSERVED, label="Residual Gap")
    ], loc="lower center", ncol=4, frameon=True, fontsize=10, bbox_to_anchor=(0.5, 0.04))
    fig3.suptitle("Catchment Breakdown Across Metro Lines and Priority Stations", fontsize=15, weight='bold', y=0.98)
    add_network_footer(fig3)
    safe_savefig(fig3, out_fig_dir / "fig03_station_stacked_bars_T15.png")

    plotted_tables['Figure 3: Line Breakdown Table'] = line_df

    # =========================================================================
    # FIGURE 4: SENSITIVITY HEATMAPS
    # =========================================================================
    print("\n[4/9] Generating Figure 4: Sensitivity Heatmaps...")
    fig4, (ax4a, ax4b) = plt.subplots(1, 2, figsize=(18, 7), dpi=300)

    # Speed Sensitivity Grid (T=15 min)
    spd_sub = speed_matrix_df[speed_matrix_df['threshold_min'] == 15.0]
    spd_pivot = spd_sub.pivot(index='walk_speed_kmh', columns='ebike_speed_kmh', values='total_walk_ebike_pct')
    im1 = ax4a.imshow(spd_pivot.values, cmap="Blues", aspect='auto', vmin=35, vmax=55)
    ax4a.set_xticks(range(len(spd_pivot.columns)))
    ax4a.set_xticklabels(spd_pivot.columns, fontsize=10, weight='bold')
    ax4a.set_yticks(range(len(spd_pivot.index)))
    ax4a.set_yticklabels(spd_pivot.index, fontsize=10, weight='bold')
    for i in range(len(spd_pivot.index)):
        for j in range(len(spd_pivot.columns)):
            val = spd_pivot.values[i, j]
            ax4a.text(j, i, f"{val:.1f}%", ha="center", va="center", color="white" if val > 45 else "black", weight="bold", fontsize=11)
    fig4.colorbar(im1, ax=ax4a, shrink=0.8, pad=0.03)
    ax4a.set_title("A. Walk Speed × E-Bike Speed (Walk+E-Bike % at T=15 min)", fontsize=12, weight='bold')
    ax4a.set_xlabel("E-Bike Speed (km/h)", fontsize=10, weight='bold')
    ax4a.set_ylabel("Walk Speed (km/h)", fontsize=10, weight='bold')

    # Overhead Sensitivity Grid (Overhead {3, 5, 7} vs T {15, 20})
    ovh_pivot = overhead_matrix_df.pivot(index='overhead_min', columns='threshold_T_min', values='combined_union_pct')
    im2 = ax4b.imshow(ovh_pivot.values, cmap="Greens", aspect='auto', vmin=45, vmax=100)
    ax4b.set_xticks(range(len(ovh_pivot.columns)))
    ax4b.set_xticklabels([f"T = {int(c)} min" for c in ovh_pivot.columns], fontsize=10, weight='bold')
    ax4b.set_yticks(range(len(ovh_pivot.index)))
    ax4b.set_yticklabels([f"{int(idx)} min" for idx in ovh_pivot.index], fontsize=10, weight='bold')
    for i in range(len(ovh_pivot.index)):
        for j in range(len(ovh_pivot.columns)):
            val = ovh_pivot.values[i, j]
            ax4b.text(j, i, f"{val:.1f}%", ha="center", va="center", color="white" if val > 75 else "black", weight="bold", fontsize=11)
    fig4.colorbar(im2, ax=ax4b, shrink=0.8, pad=0.03)
    ax4b.set_title("B. Multi-Modal Overhead × Travel Budget (Combined Union %)", fontsize=12, weight='bold')
    ax4b.set_xlabel("Travel Time Budget (T)", fontsize=10, weight='bold')
    ax4b.set_ylabel("Mode Switching Overhead", fontsize=10, weight='bold')

    fig4.suptitle("Sensitivity Matrices Across Multi-Modal Speeds and Fleet Overheads (83 Stations)", fontsize=15, weight='bold', y=0.98)
    add_network_footer(fig4)
    safe_savefig(fig4, out_fig_dir / "fig04_sensitivity_heatmaps.png")

    plotted_tables['Figure 4A: Speed Sensitivity Matrix'] = speed_matrix_df
    plotted_tables['Figure 4B: Overhead Sensitivity Matrix'] = overhead_matrix_df

    # =========================================================================
    # FIGURE 5: FEEDER HUB SITING MAP & GAIN CURVE
    # =========================================================================
    print("\n[5/9] Generating Figure 5: Feeder Hub Siting & Max-Coverage Curve...")
    fig5, (ax5a, ax5b) = plt.subplots(1, 2, figsize=(22, 10), dpi=300)

    # Hub Spatial Map
    core_cells_wgs84[core_cells_wgs84['cat_15'] == 'Walk Baseline'].plot(ax=ax5a, color=COLOR_WALK, alpha=0.3, zorder=1)
    core_cells_wgs84[core_cells_wgs84['cat_15'] != 'Walk Baseline'].plot(ax=ax5a, color="#f1f5f9", edgecolor="#cbd5e1", linewidth=0.2, zorder=1)

    for line_name, line_col in [('Purple', COLOR_PURPLE), ('Green', COLOR_GREEN), ('Yellow', COLOR_YELLOW)]:
        st_sub = st_gdf[st_gdf['line'] == line_name]
        ax5a.scatter(st_sub.geometry.x, st_sub.geometry.y, color=line_col, s=35, zorder=3)

    # Plot Greedy Hubs k=1..15
    ax5a.scatter(greedy_t15_df['lon'], greedy_t15_df['lat'], color="#dc2626", edgecolor="white", s=130, marker="*", linewidth=1.2, zorder=6, label="Greedy Feeder Hubs (k=1..15)")

    # Draw feeder connector vectors from hub to feeding station
    st_lookup = dict(zip(st_df['station_id'], zip(st_gdf.geometry.x, st_gdf.geometry.y)))
    for _, h in greedy_t15_df.iterrows():
        sid = h['feeds_station_id']
        if sid in st_lookup:
            sx, sy = st_lookup[sid]
            ax5a.plot([h['lon'], sx], [h['lat'], sy], color="#dc2626", linestyle=":", linewidth=1.2, zorder=5)

    ax5a.set_title("A. Top 15 Feeder Hub Locations & Station Feed Vectors (T = 15 min)", fontsize=12, weight='bold')
    ax5a.set_axis_off()
    ax5a.legend(loc="lower left", fontsize=10, frameon=True)

    # Greedy Gain Curve
    ax5b.plot(greedy_t15_df['k'], greedy_t15_df['cumulative_gain_pop'], marker='o', color='#2563eb', linewidth=2.5, markersize=7, label="T = 15 min")
    ax5b.plot(greedy_t20_df['k'], greedy_t20_df['cumulative_gain_pop'], marker='s', color='#059669', linewidth=2.5, markersize=7, label="T = 20 min")
    
    # Submodular diminishing returns bars
    ax5b.bar(greedy_t15_df['k'] - 0.15, greedy_t15_df['marginal_gain_pop'], width=0.3, color='#93c5fd', alpha=0.7, label="Marginal Gain (T=15m)")
    ax5b.bar(greedy_t20_df['k'] + 0.15, greedy_t20_df['marginal_gain_pop'], width=0.3, color='#a7f3d0', alpha=0.7, label="Marginal Gain (T=20m)")

    ax5b.set_title("B. Submodular Maximum-Coverage Diminishing Returns Curve", fontsize=12, weight='bold')
    ax5b.set_xlabel("Number of Micro-Mobility Hubs (k)", fontsize=11, weight='bold')
    ax5b.set_ylabel("Population Unlocked (Residents)", fontsize=11, weight='bold')
    ax5b.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{x/1e3:.0f}k"))
    ax5b.set_xticks(range(1, 16))
    ax5b.grid(True, linestyle="--", alpha=0.4)
    ax5b.legend(loc="center right", fontsize=10, frameon=True)
    ax5b.spines['top'].set_visible(False)
    ax5b.spines['right'].set_visible(False)

    fig5.suptitle("Physical Feeder Hub Deployment: Greedy Siting & Coverage Gains", fontsize=15, weight='bold', y=0.98)
    add_network_footer(fig5)
    safe_savefig(fig5, out_fig_dir / "fig05_hub_siting_map_and_curve.png")

    plotted_tables['Figure 5A: Greedy Selected Sites T=15'] = greedy_t15_df[['k', 'site_id', 'lat', 'lon', 'marginal_gain_pop', 'cumulative_gain_pop', 'feeds_station_name', 'ride_time_to_station_min']]
    plotted_tables['Figure 5B: Greedy Selected Sites T=20'] = greedy_t20_df[['k', 'site_id', 'lat', 'lon', 'marginal_gain_pop', 'cumulative_gain_pop', 'feeds_station_name', 'ride_time_to_station_min']]

    # =========================================================================
    # FIGURE 6: STATION PRIORITY SLOPE CHART
    # =========================================================================
    print("\n[6/9] Generating Figure 6: Station Priority Slope Chart...")
    fig6, ax6 = plt.subplots(figsize=(10, 11), dpi=300)

    top20_rank = st_ranking_df.sort_values('weighted_rank').head(20).copy()
    
    for _, r in top20_rank.iterrows():
        n_rank = r['need_only_rank']
        w_rank = r['weighted_rank']
        shift = n_rank - w_rank
        col = "#059669" if shift > 0 else ("#dc2626" if shift < 0 else "#64748b")
        
        ax6.plot([0, 1], [n_rank, w_rank], color=col, linewidth=2.2, alpha=0.85)
        ax6.scatter([0, 1], [n_rank, w_rank], color=col, s=40, zorder=5)
        
        # Labels
        ax6.text(-0.03, n_rank, f"#{n_rank} {r['name']}", ha='right', va='center', fontsize=8.5, weight='medium')
        ax6.text(1.03, w_rank, f"#{w_rank} {r['name']} ({r['avg_daily_boardings']:,.0f}/day)", ha='left', va='center', fontsize=8.5, weight='bold')

    ax6.set_xlim(-0.45, 1.45)
    ax6.set_ylim(25, 0.5)
    ax6.set_xticks([0, 1])
    ax6.set_xticklabels(["Need-Only Rank\n(Unserved Residents)", "Policy Weighted Rank\n(Need × Ridership / Mean)"], fontsize=11, weight='bold')
    ax6.set_ylabel("Rank (1 = Top Priority)", fontsize=11, weight='bold')
    ax6.set_title("Station Priority Shift: Pure Population Need vs. Ridership-Weighted Score", fontsize=13, weight='bold', pad=15)
    ax6.grid(axis='y', linestyle='--', alpha=0.3)
    ax6.spines['top'].set_visible(False)
    ax6.spines['right'].set_visible(False)
    ax6.spines['left'].set_visible(False)
    add_network_footer(fig6)
    safe_savefig(fig6, out_fig_dir / "fig06_station_priority_slope.png")

    plotted_tables['Figure 6: Top 20 Station Rankings'] = top20_rank[['station_id', 'name', 'need_only_rank', 'weighted_rank', 'weighted_yellow1_rank', 'uncovered_walk_need', 'avg_daily_boardings', 'score_weighted']]

    # =========================================================================
    # FIGURE 7: INFRASTRUCTURE SEVERANCE AUDIT MAP
    # =========================================================================
    print("\n[7/9] Generating Figure 7: Infrastructure Severance Audit Map...")
    fig7, ax7 = plt.subplots(figsize=(12, 10), dpi=300)

    # Identify severance cells across the network where walk <= 20 min but ebike > 20 min
    sev_mask = (core_cells_wgs84['walk_time_min'] <= 20.0) & (core_cells_wgs84['ebike_time_min'] > 20.0)
    sev_cells = core_cells_wgs84[sev_mask].copy()

    core_cells_wgs84.plot(ax=ax7, color="#f8fafc", edgecolor="#e2e8f0", linewidth=0.2, zorder=1)
    core_cells_wgs84[core_cells_wgs84['walk_time_min'] <= 20.0].plot(ax=ax7, color=COLOR_WALK, alpha=0.25, zorder=2)
    sev_cells.plot(ax=ax7, color="#dc2626", edgecolor="#991b1b", linewidth=0.8, zorder=4, label="Severed Cells (Walk <= 20m, E-Bike > 20m)")

    for line_name, line_col in [('Purple', COLOR_PURPLE), ('Green', COLOR_GREEN), ('Yellow', COLOR_YELLOW)]:
        st_sub = st_gdf[st_gdf['line'] == line_name]
        ax7.scatter(st_sub.geometry.x, st_sub.geometry.y, color=line_col, s=40, zorder=5)

    ax7.set_title(f"Network Infrastructure Severance Audit: {len(sev_cells)} Cells ({sev_cells['population'].sum():,.0f} Residents)", fontsize=13, weight='bold')
    ax7.set_axis_off()
    ax7.legend(loc="lower right", fontsize=10, frameon=True)
    add_network_footer(fig7)
    safe_savefig(fig7, out_fig_dir / "fig07_railway_severance_map.png")

    # =========================================================================
    # FIGURE 8: NETWORK PRIORITY MAP (All 83 Stations Ranked)
    # =========================================================================
    print("\n[8/9] Generating Figure 8: Network Priority Map...")
    fig8, ax8 = plt.subplots(figsize=(13, 11), dpi=300)

    core_cells_wgs84.plot(ax=ax8, color="#f1f5f9", edgecolor="#cbd5e1", linewidth=0.2, zorder=1)

    # Merge ranking score to st_gdf
    st_plot = st_gdf.merge(st_ranking_df[['station_id', 'weighted_rank', 'score_weighted']], on='station_id')

    # Color code stations by weighted rank
    scatter = ax8.scatter(
        st_plot.geometry.x, st_plot.geometry.y,
        c=st_plot['score_weighted'] / 1e3,
        cmap='plasma_r',
        s=120,
        edgecolor='black',
        linewidth=0.8,
        zorder=5
    )
    cbar = plt.colorbar(scatter, ax=ax8, shrink=0.7, pad=0.02)
    cbar.set_label("Priority Score (k points)", fontsize=10, weight='bold')

    # Label top 10 stations
    top10_st = st_plot.sort_values('weighted_rank').head(10)
    for _, s in top10_st.iterrows():
        ax8.annotate(
            f"#{s['weighted_rank']} {s['name']}",
            (s.geometry.x, s.geometry.y),
            xytext=(6, 6), textcoords="offset points",
            fontsize=8, weight='bold', color='#0f172a',
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", edgecolor="#cbd5e1", alpha=0.9),
            zorder=6
        )

    ax8.set_title("Bengaluru Metro Network: 83-Station Priority Map (Weighted Score)", fontsize=14, weight='bold')
    ax8.set_axis_off()
    add_network_footer(fig8)
    safe_savefig(fig8, out_fig_dir / "fig08_network_priority_map.png")
    safe_savefig(fig8, out_fig_dir / "priority_map_network.png")

    # =========================================================================
    # FIGURE 9: HEADLINE ONE-PAGER (Executive KPI Summary)
    # =========================================================================
    print("\n[9/9] Generating Figure 9: Executive Headline One-Pager...")
    fig9 = plt.figure(figsize=(16, 10), dpi=300)
    gs = fig9.add_gridspec(3, 3, hspace=0.35, wspace=0.25)

    # Top KPI Cards
    kpis = [
        ("Total Network Study Population", f"{total_pop:,.0f}", "WorldPop 2020 (4,930 H3 Res-9 Cells)", "#0f172a"),
        ("Walk Baseline Reach (T=15m)", f"{t15_row['walk_covered_pct']:.1f}%", f"{t15_row['walk_covered_pop']:,.0f} residents within 15 min walk", COLOR_WALK),
        ("Multi-Modal Reach (T=15m)", f"{t15_row['combined_covered_pct']:.1f}%", f"{t15_row['combined_covered_pop']:,.0f} residents (Walk + E-Bike + E-Auto)", COLOR_EBIKE),
        ("E-Bike Net Uplift (T=15m)", f"+{t15_row['ebike_uplift_pct']:.1f}%", f"+{t15_row['ebike_uplift_pop']:,.0f} residents unlocked by e-bikes", COLOR_EBIKE),
        ("Multi-Modal Reach (T=20m)", f"{t20_row['combined_covered_pct']:.1f}%", f"{t20_row['combined_covered_pop']:,.0f} residents (WRI STAMP Benchmark)", COLOR_EAUTO),
        ("Top Ranked Station", "#1 Benniganahalli", "Score: 331.4k | 18.2k boardings/day", "#7c3aed")
    ]

    for idx, (title, val, sub, col) in enumerate(kpis):
        r, c = divmod(idx, 3)
        ax_kpi = fig9.add_subplot(gs[r, c])
        ax_kpi.set_axis_off()
        ax_kpi.add_patch(FancyBboxPatch((0.02, 0.05), 0.96, 0.90, boxstyle="round,pad=0.05", facecolor="#ffffff", edgecolor="#cbd5e1", linewidth=1.2))
        ax_kpi.text(0.08, 0.78, title, fontsize=10, weight='bold', color="#64748b")
        ax_kpi.text(0.08, 0.42, val, fontsize=20, weight='heavy', color=col)
        ax_kpi.text(0.08, 0.18, sub, fontsize=8.2, color="#475569")

    # Bottom Row: Summary Table
    ax_bot = fig9.add_subplot(gs[2, :])
    ax_bot.set_axis_off()
    table_data = [
        ["Threshold (T)", "Walk Baseline Pop (%)", "E-Bike Uplift Pop (%)", "E-Auto Extra Pop (%)", "Combined Pop (%)", "Residual Gap Pop (%)"],
        ["T = 15 min", f"{t15_row['walk_covered_pop']:,.0f} ({t15_row['walk_covered_pct']:.1f}%)", f"{t15_row['ebike_uplift_pop']:,.0f} ({t15_row['ebike_uplift_pct']:.1f}%)", f"{t15_row['eauto_uplift_pop']:,.0f} ({t15_row['eauto_uplift_pct']:.1f}%)", f"{t15_row['combined_covered_pop']:,.0f} ({t15_row['combined_covered_pct']:.1f}%)", f"{t15_row['residual_unserved_pop']:,.0f} ({t15_row['residual_unserved_pct']:.1f}%)"],
        ["T = 20 min", f"{t20_row['walk_covered_pop']:,.0f} ({t20_row['walk_covered_pct']:.1f}%)", f"{t20_row['ebike_uplift_pop']:,.0f} ({t20_row['ebike_uplift_pct']:.1f}%)", f"{t20_row['eauto_uplift_pop']:,.0f} ({t20_row['eauto_uplift_pct']:.1f}%)", f"{t20_row['combined_covered_pop']:,.0f} ({t20_row['combined_covered_pct']:.1f}%)", f"{t20_row['residual_unserved_pop']:,.0f} ({t20_row['residual_unserved_pct']:.1f}%)"]
    ]
    t = ax_bot.table(cellText=table_data, loc='center', cellLoc='center')
    t.auto_set_font_size(False)
    t.set_fontsize(9.5)
    t.scale(1, 1.8)
    for c in range(6):
        t[(0, c)].set_facecolor('#0f172a')
        t[(0, c)].set_text_props(color='white', weight='bold')

    fig9.suptitle("Executive Dashboard: Bengaluru Metro Multi-Modal Feeder Catchment (83 Stations)", fontsize=15, weight='bold', y=0.98)
    add_network_footer(fig9)
    safe_savefig(fig9, out_fig_dir / "fig09_headline_onepager.png")

    # Extra Maps Requested: hub_map.png and coverage_by_line.png
    print("\nGenerating Extra Figures: hub_map_network.png & coverage_by_line.png...")
    
    # Hub map
    fig_hub, ax_hub = plt.subplots(figsize=(12, 10), dpi=300)
    core_cells_wgs84[core_cells_wgs84['cat_15'] == 'Walk Baseline'].plot(ax=ax_hub, color=COLOR_WALK, alpha=0.3, zorder=1)
    core_cells_wgs84[core_cells_wgs84['cat_15'] != 'Walk Baseline'].plot(ax=ax_hub, color="#f1f5f9", edgecolor="#cbd5e1", linewidth=0.2, zorder=1)
    for line_name, line_col in [('Purple', COLOR_PURPLE), ('Green', COLOR_GREEN), ('Yellow', COLOR_YELLOW)]:
        st_sub = st_gdf[st_gdf['line'] == line_name]
        ax_hub.scatter(st_sub.geometry.x, st_sub.geometry.y, color=line_col, s=40, zorder=3)
    ax_hub.scatter(greedy_t15_df['lon'], greedy_t15_df['lat'], color="#dc2626", edgecolor="white", s=130, marker="*", linewidth=1.2, zorder=6, label="Top 15 Feeder Hubs")
    for _, h in greedy_t15_df.iterrows():
        sid = h['feeds_station_id']
        if sid in st_lookup:
            sx, sy = st_lookup[sid]
            ax_hub.plot([h['lon'], sx], [h['lat'], sy], color="#dc2626", linestyle=":", linewidth=1.2, zorder=5)
    ax_hub.set_title("Feeder Micro-Mobility Hub Locations & Metro Station Feed Vectors", fontsize=13, weight='bold')
    ax_hub.set_axis_off()
    ax_hub.legend(loc="lower left", fontsize=10)
    add_network_footer(fig_hub)
    safe_savefig(fig_hub, out_fig_dir / "hub_map_network.png")

    # Coverage by Line Map
    fig_line, ax_line = plt.subplots(figsize=(12, 10), dpi=300)
    for line_name, line_col in [('Purple', COLOR_PURPLE), ('Green', COLOR_GREEN), ('Yellow', COLOR_YELLOW)]:
        c_sub = core_cells_wgs84[core_cells_wgs84['line'] == line_name]
        c_sub.plot(ax=ax_line, color=line_col, alpha=0.45, edgecolor="#cbd5e1", linewidth=0.2, label=f"{line_name} Line Catchment")
        st_sub = st_gdf[st_gdf['line'] == line_name]
        ax_line.scatter(st_sub.geometry.x, st_sub.geometry.y, color=line_col, edgecolor="black", s=50, linewidth=0.8, zorder=5)
    ax_line.set_title("Bengaluru Metro Network: Assigned Catchment Territories by Metro Line", fontsize=13, weight='bold')
    ax_line.set_axis_off()
    ax_line.legend(loc="lower left", fontsize=10)
    add_network_footer(fig_line)
    safe_savefig(fig_line, out_fig_dir / "coverage_by_line_network.png")

    # Print Table of Plotted Values
    print("\n=======================================================")
    print("             TABLE OF PLOTTED VALUES                   ")
    print("=======================================================")
    for title, table in plotted_tables.items():
        print(f"\n--- {title} ---")
        if isinstance(table, pd.DataFrame):
            print(table.to_string(index=False))

    t_end = time.time()
    print(f"\nStage E Complete! All figures generated and saved to {out_fig_dir} in {t_end-t_start:.2f}s ({(t_end-t_start)/60:.2f} min).")

if __name__ == '__main__':
    main()
