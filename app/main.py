"""
app/main.py - Modern Executive Screening & Prioritization Dashboard
For Bengaluru Metro Feeder Zones (SHIFT 2026 Hackathon).
Evaluates the 10-station Whitefield pilot corridor and provides the scalable
framework for expansion to all 83 BMRCL metro stations across Bengaluru.
"""

from pathlib import Path
import json
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & MODERN STYLING SYSTEM
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Metro Feeder Zone Screening | Bengaluru 10-Station Pilot & 83-Station Vision",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Design System CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        border-radius: 16px;
        padding: 28px 34px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.025em;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #94a3b8;
        font-weight: 400;
        line-height: 1.5;
        max-width: 900px;
    }
    .hero-badge-container {
        display: flex;
        gap: 10px;
        margin-top: 14px;
        flex-wrap: wrap;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .badge-teal { background-color: rgba(42, 157, 143, 0.25); color: #5eead4; border: 1px solid rgba(42, 157, 143, 0.4); }
    .badge-blue { background-color: rgba(59, 130, 246, 0.25); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }
    .badge-amber { background-color: rgba(245, 158, 11, 0.25); color: #fde68a; border: 1px solid rgba(245, 158, 11, 0.4); }
    .badge-purple { background-color: rgba(139, 92, 246, 0.25); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.4); }

    /* Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.07);
        border-color: #cbd5e1;
    }
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }
    .metric-delta {
        font-size: 0.88rem;
        font-weight: 600;
        margin-top: 6px;
    }
    .delta-green { color: #059669; }
    .delta-blue { color: #2563eb; }
    .delta-amber { color: #d97706; }
    .delta-red { color: #dc2626; }

    /* Custom Callouts */
    .info-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #0284c7;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 1rem;
        color: #334155;
    }
    .alert-card {
        background-color: #fffbeb;
        border: 1px solid #fef3c7;
        border-left: 5px solid #f59e0b;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 1rem;
        color: #92400e;
    }
    .success-card {
        background-color: #f0fdf4;
        border: 1px solid #dcfce7;
        border-left: 5px solid #10b981;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 1rem;
        color: #166534;
    }
    
    /* Footer */
    .app-footer {
        margin-top: 3.5rem;
        padding: 24px 0;
        border-top: 1px solid #e2e8f0;
        font-size: 0.85rem;
        color: #64748b;
        text-align: center;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATA LOADING & CACHING (100% SELF-CONTAINED FROM data/output)
# -----------------------------------------------------------------------------
DATA_DIR = Path("data/output")
INTERIM_DIR = Path("data/interim")
NETWORK_DIR = Path("data/output_network")
FIGURES_DIR = Path("docs/figures")


@st.cache_data
def load_all_dashboard_data():
    """Load and cache all precomputed pipeline outputs for instantaneous UI response."""
    cells_df = pd.read_csv(DATA_DIR / "cells.csv")
    cells_gdf = gpd.read_file(DATA_DIR / "cells.gpkg")
    
    # Load stations (from data/output if present, fallback to data/interim)
    st_sel_path = DATA_DIR / "stations_selected.gpkg" if (DATA_DIR / "stations_selected.gpkg").exists() else INTERIM_DIR / "stations_selected.gpkg"
    st_all_path = DATA_DIR / "stations_all.gpkg" if (DATA_DIR / "stations_all.gpkg").exists() else INTERIM_DIR / "stations_all.gpkg"
    
    stations_selected = gpd.read_file(st_sel_path).to_crs("EPSG:4326")
    stations_all = gpd.read_file(st_all_path).to_crs("EPSG:4326")
    
    # 83 City-wide stations & network cells
    stations_83_df = pd.read_csv(NETWORK_DIR / "stations_83_network.csv")
    cells_network_df = pd.read_csv(NETWORK_DIR / "cells_network.csv")
    
    # Candidate sites & selected sites (with coordinates merged)
    candidate_sites_gdf = gpd.read_file(DATA_DIR / "candidate_sites.gpkg").to_crs("EPSG:4326")
    selected_sites_df = pd.read_csv(DATA_DIR / "selected_sites.csv")
    selected_sites_df = selected_sites_df.merge(candidate_sites_gdf[["site_id", "lat", "lon"]], on="site_id", how="left")
    
    if (DATA_DIR / "selected_sites_T20.csv").exists():
        selected_sites_t20_df = pd.read_csv(DATA_DIR / "selected_sites_T20.csv")
        selected_sites_t20_df = selected_sites_t20_df.merge(candidate_sites_gdf[["site_id", "lat", "lon"]], on="site_id", how="left")
    else:
        selected_sites_t20_df = selected_sites_df
        
    ranking_df = pd.read_csv(DATA_DIR / "station_ranking.csv")
    speed_matrix_df = pd.read_csv(DATA_DIR / "speed_sensitivity_matrix.csv")
    overhead_matrix_df = pd.read_csv(DATA_DIR / "overhead_sensitivity_matrix.csv")
    
    with open(DATA_DIR / "catchment_metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)
        
    # Tag 83 stations by corridor
    pilot_names = [
        "Whitefield (Kadugodi)", "Hopefarm Channasandra", "Kadugodi Tree Park",
        "Pattandur Agrahara", "Sathya Sai Hospital", "Nallurahalli",
        "Kundalahalli", "Seetharampalya", "Hoodi", "Garudacharpalya"
    ]
    context_names = ["Singayyanapalya", "Krishnarajapura"]
    
    def tag_corridor(name):
        if name in pilot_names:
            return "Whitefield Pilot (10 Stations)"
        elif name in context_names:
            return "Western Context Absorber (2 Stations)"
        return "Bengaluru Metro Network (71 Stations)"
        
    stations_83_df["corridor_group"] = stations_83_df["name"].apply(tag_corridor)

    return {
        "cells_df": cells_df,
        "cells_gdf": cells_gdf,
        "stations_selected": stations_selected,
        "stations_all": stations_all,
        "stations_83_df": stations_83_df,
        "cells_network_df": cells_network_df,
        "selected_sites_df": selected_sites_df,
        "selected_sites_t20_df": selected_sites_t20_df,
        "candidate_sites_gdf": candidate_sites_gdf,
        "ranking_df": ranking_df,
        "speed_matrix_df": speed_matrix_df,
        "overhead_matrix_df": overhead_matrix_df,
        "metrics": metrics
    }

data = load_all_dashboard_data()

cells_gdf = data["cells_gdf"]
stations_selected = data["stations_selected"]
stations_all = data["stations_all"]
ranking_df = data["ranking_df"]
selected_sites_df = data["selected_sites_df"]
selected_sites_t20_df = data["selected_sites_t20_df"]
candidate_sites_gdf = data["candidate_sites_gdf"]
stations_83_df = data["stations_83_df"]
cells_network_df = data["cells_network_df"]

# Strict corridor population filter
corr_cells = cells_gdf[cells_gdf["is_corridor_assigned"] == True].copy()
TOTAL_CORR_POP = 453687.0
TOTAL_CORR_CELLS = 572

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & PARAMETER CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Namma_Metro_logo.svg/330px-Namma_Metro_logo.svg.png", width=75)
st.sidebar.markdown("### 🚇 Metro Feeder Screening")
st.sidebar.caption("Bengaluru Sustainable e-Micromobility Planning | SHIFT 2026")

time_budget = st.sidebar.radio(
    "⏱️ Travel Time Budget (T):",
    ["T = 15 min (Standard Pedestrian)", "T = 20 min (WRI STAMP Benchmark)"],
    index=0,
    help="15 min represents standard transit walking threshold. 20 min reflects empirical commuters' willingness-to-travel threshold from the WRI India STAMP study."
)
is_t20 = "20" in time_budget
T_VAL = 20.0 if is_t20 else 15.0

st.sidebar.markdown("---")
nav_choice = st.sidebar.radio(
    "📌 Navigation Menu",
    [
        "1. Executive Overview (Pilot)",
        "2. Multi-Modal Access Map",
        "3. Station Deep Dive (10 Stations)",
        "4. Feeder Hub Siting Planner",
        "5. Station Prioritization Matrix",
        "6. Infrastructure & Severance Audits",
        "7. Scale Vision: 83-Station Network",
        "8. Presentation Figures Gallery",
        "9. Data Downloads & Methodology"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="font-size: 0.82rem; line-height: 1.5; color: #475569; background: #ffffff; padding: 12px 14px; border-radius: 8px; border: 1px solid #e2e8f0;">
    <strong>Corridor Baseline Snapshot:</strong><br>
    • <strong>Core Population:</strong> 453,687 (572 cells)<br>
    • <strong>Pilot Stations:</strong> 10 continuous<br>
    • <strong>Context Absorbers:</strong> 2 stations<br>
    • <strong>Walk Speed:</strong> 4.5 km/h (0m overhead)<br>
    • <strong>E-Bike Speed:</strong> 13.5 km/h (+5m overhead)<br>
    • <strong>Active Threshold:</strong> T = {T_VAL:.0f} min
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# SCREEN 1: EXECUTIVE OVERVIEW
# ==============================================================================
if nav_choice == "1. Executive Overview (Pilot)":
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">🚇 Metro Feeder Zone Screening Dashboard</div>
        <div class="hero-subtitle">
            Evaluating multi-modal accessibility, road-class safety filtering, and spatial equity optimization 
            for the <strong>Whitefield 10-Station Metro Corridor</strong> before city-wide rollout across all 83 BMRCL stations.
        </div>
        <div class="hero-badge-container">
            <span class="hero-badge badge-teal">WorldPop 2020: 453,687 Pop</span>
            <span class="hero-badge badge-blue">H3 Res-9 Grid: 572 Hexagons</span>
            <span class="hero-badge badge-amber">BMRCL RTI August 2025</span>
            <span class="hero-badge badge-purple">Budget: T = {T_VAL:.0f} min</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Compute dynamic figures based on T_VAL
    w_mask = corr_cells["walk_time_min"] <= T_VAL
    b_mask = corr_cells["ebike_time_min"] <= T_VAL
    up_mask = b_mask & (~w_mask)
    comb_active_mask = w_mask | b_mask
    a_mask = corr_cells["eauto_time_min"] <= T_VAL
    a_up_mask = a_mask & (~comb_active_mask)
    union_mask = comb_active_mask | a_mask
    unserved_mask = ~union_mask

    walk_pop = corr_cells[w_mask]["population"].sum()
    ebike_up_pop = corr_cells[up_mask]["population"].sum()
    active_pop = corr_cells[comb_active_mask]["population"].sum()
    eauto_extra_pop = corr_cells[a_up_mask]["population"].sum()
    union_pop = corr_cells[union_mask]["population"].sum()
    unserved_pop = corr_cells[unserved_mask]["population"].sum()

    # Top KPI Metrics Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🚶 Walk Baseline (4.5 km/h)</div>
            <div class="metric-value">{walk_pop:,.0f}</div>
            <div class="metric-delta delta-green">+{walk_pop / TOTAL_CORR_POP * 100:.1f}% of corridor</div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">{int(w_mask.sum())} H3 hexagonal cells</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🚲 E-Bike Doorstep Uplift</div>
            <div class="metric-value">+{ebike_up_pop:,.0f}</div>
            <div class="metric-delta delta-blue">+{ebike_up_pop / TOTAL_CORR_POP * 100:.1f}% newly unlocked</div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">+{int(up_mask.sum())} incremental cells</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">⚡ Active Micro-Mobility</div>
            <div class="metric-value">{active_pop:,.0f}</div>
            <div class="metric-delta delta-green">{active_pop / TOTAL_CORR_POP * 100:.1f}% total active reach</div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">Walk OR E-Bike ({int(comb_active_mask.sum())} cells)</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🛑 Residual Unserved Gap</div>
            <div class="metric-value">{unserved_pop:,.0f}</div>
            <div class="metric-delta delta-red">{unserved_pop / TOTAL_CORR_POP * 100:.1f}% unserved (&gt; {T_VAL:.0f}m)</div>
            <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">{int(unserved_mask.sum())} unserved cells</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Population Breakdown & Policy Takeaways
    col_chart, col_takeaways = st.columns([1.3, 1])

    with col_chart:
        fig_bar = go.Figure()
        categories = ["Residual Unserved", "E-Auto Extra (Upper Bound)", "E-Bike Doorstep Uplift", "Walk Baseline"]
        values = [unserved_pop, eauto_extra_pop, ebike_up_pop, walk_pop]
        colors = ["#94A3B8", "#F59E0B", "#3B82F6", "#10B981"]
        percentages = [f"{v / TOTAL_CORR_POP * 100:.1f}%" for v in values]

        fig_bar.add_trace(go.Bar(
            y=categories,
            x=values,
            orientation="h",
            marker=dict(color=colors, line=dict(color="#ffffff", width=1.5)),
            text=[f"{v:,.0f} ({p})" for v, p in zip(values, percentages)],
            textposition="auto",
            hoverinfo="x+y+text"
        ))
        
        fig_bar.update_layout(
            title=f"<b>Corridor Population Partition (T = {T_VAL:.0f} min Budget | Base = 453,687)</b>",
            xaxis_title="Residents (WorldPop 2020)",
            height=340,
            margin=dict(l=20, r=20, t=50, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#e2e8f0")
        )
        st.plotly_chart(fig_bar, width="stretch")

    with col_takeaways:
        st.markdown("### 🔍 Key Engineering Takeaways")
        if not is_t20:
            st.markdown("""
            <div class="alert-card">
                <strong>Pedestrian Baseline is Severely Constrained:</strong><br>
                Only <strong>14.6%</strong> (66,417 residents) live within a 15-minute walk of a station. Over 85% cannot physically walk to the metro.
            </div>
            <div class="success-card">
                <strong>E-Micromobility Doubles Station Reach:</strong><br>
                Deploying road-class filtered e-bikes unlocks <strong>+69,215 additional residents (+15.3% uplift)</strong>, lifting active reach to <strong>29.9%</strong>.
            </div>
            <div class="info-card">
                <strong>The 53% Last-Mile Deficit:</strong><br>
                240,547 residents remain disconnected across modes, proving why strategic neighborhood feeder hubs are urgent.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="success-card">
                <strong>Surging E-Bike Elasticity at T = 20 min:</strong><br>
                Commuters willing to spend 20 minutes unlock <strong>+141,578 e-bike residents (+31.2% uplift)</strong>, surging active reach past <strong>54.5% (247,029 residents)</strong>.
            </div>
            <div class="info-card">
                <strong>Multi-Modal Saturation (83.1% Union):</strong><br>
                At 20 minutes, walk + bike + e-auto covers 376,973 residents, shrinking the unserved deficit to just <strong>16.9%</strong>.
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### 📊 Multi-Modal Reconciliation Table")
    summary_table = pd.DataFrame({
        "Catchment Layer": [
            "Walking Baseline (4.5 km/h)",
            "E-Bike Doorstep Uplift (13.5 km/h + 5m overhead)",
            "Combined Active Reach (Walk ∪ E-Bike)",
            "E-Auto Extra Reach (Unfiltered Drive Upper Bound)",
            "Multi-Modal Union (Walk ∪ E-Bike ∪ E-Auto)",
            "Residual Unserved Gap (> T min)"
        ],
        "Residents Covered": [
            f"{walk_pop:,.0f}",
            f"+{ebike_up_pop:,.0f}",
            f"{active_pop:,.0f}",
            f"+{eauto_extra_pop:,.0f}",
            f"{union_pop:,.0f}",
            f"{unserved_pop:,.0f}"
        ],
        "Share of Corridor": [
            f"{walk_pop / TOTAL_CORR_POP * 100:.2f}%",
            f"+{ebike_up_pop / TOTAL_CORR_POP * 100:.2f}%",
            f"{active_pop / TOTAL_CORR_POP * 100:.2f}%",
            f"+{eauto_extra_pop / TOTAL_CORR_POP * 100:.2f}%",
            f"{union_pop / TOTAL_CORR_POP * 100:.2f}%",
            f"{unserved_pop / TOTAL_CORR_POP * 100:.2f}%"
        ],
        "H3 Res-9 Cells": [
            f"{int(w_mask.sum())}",
            f"+{int(up_mask.sum())}",
            f"{int(comb_active_mask.sum())}",
            f"+{int(a_up_mask.sum())}",
            f"{int(union_mask.sum())}",
            f"{int(unserved_mask.sum())}"
        ]
    })
    st.dataframe(summary_table, width="stretch", hide_index=True)


# ==============================================================================
# SCREEN 2: MULTI-MODAL ACCESS MAP
# ==============================================================================
elif nav_choice == "2. Multi-Modal Access Map":
    st.title("🗺️ Interactive Multi-Modal Catchment Map")
    st.markdown(f"High-resolution H3 hexagonal spatial catchments across the Whitefield corridor at **T = {T_VAL:.0f} minutes**.")

    col_ctrl, col_map = st.columns([1, 3.2])
    
    with col_ctrl:
        layer_mode = st.radio(
            "Layer Display Mode:",
            [
                "Combined Active Reach (Walk ∪ E-Bike)",
                "Walking Baseline Catchment",
                "E-Bike Catchment Only",
                "E-Bike Uplift Zone Only",
                "Full Multi-Modal Union (Walk + Bike + Auto)",
                "Unserved Gap Only"
            ]
        )
        
        st.markdown("**Map Overlays:**")
        show_pilot_stations = st.checkbox("Show 10 Pilot Stations", value=True)
        show_context_stations = st.checkbox("Show 2 Context Absorbers (KR Puram & Singayyanapalya)", value=True)
        show_top_hubs = st.checkbox("Show Top 5 Placed Feeder Hubs", value=True)
        show_candidates = st.checkbox("Show Candidate Feeder Hub Sites (881 Street Corners)", value=False)
        
        st.markdown("---")
        st.markdown("**Map Legend:**")
        st.markdown("🟢 **Green:** Walk Catchment")
        st.markdown("🔵 **Blue:** E-Bike Uplift / Catchment")
        st.markdown("🟠 **Orange:** E-Auto Extra Reach")
        st.markdown("⚪ **Grey:** Residual Unserved")
        st.markdown("🔴 **Red Dot:** Pilot Metro Station")
        st.markdown("🟡 **Gold Triangle:** Western Context Station")
        st.markdown("🌟 **Gold Ring / Dot:** Top Placed Feeder Hubs (k=5)")
        st.markdown("🟣 **Purple Dot:** Candidate Street Feeder Sites (881 Sites)")

    with col_map:
        center_lat = stations_selected.geometry.y.mean()
        center_lon = stations_selected.geometry.x.mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles="OpenStreetMap"
        )
        
        # Color function
        w_mask = corr_cells["walk_time_min"] <= T_VAL
        b_mask = corr_cells["ebike_time_min"] <= T_VAL
        up_mask = b_mask & (~w_mask)
        a_mask = corr_cells["eauto_time_min"] <= T_VAL
        a_up_mask = a_mask & (~(w_mask | b_mask))

        def style_fn(feature):
            props = feature["properties"]
            w_time = props.get("walk_time_min", 999.0)
            b_time = props.get("ebike_time_min", 999.0)
            a_time = props.get("eauto_time_min", 999.0)
            
            is_w = w_time <= T_VAL
            is_b = b_time <= T_VAL
            is_up = is_b and not is_w
            is_a_up = (a_time <= T_VAL) and not (is_w or is_b)
            
            if layer_mode == "Combined Active Reach (Walk ∪ E-Bike)":
                if is_w:
                    return {"fillColor": "#10B981", "color": "#047857", "weight": 0.8, "fillOpacity": 0.7}
                elif is_up:
                    return {"fillColor": "#3B82F6", "color": "#1D4ED8", "weight": 0.8, "fillOpacity": 0.65}
                return {"fillColor": "#E2E8F0", "color": "#CBD5E1", "weight": 0.4, "fillOpacity": 0.2}
            elif layer_mode == "Walking Baseline Catchment":
                if is_w:
                    return {"fillColor": "#10B981", "color": "#047857", "weight": 1.0, "fillOpacity": 0.75}
                return {"fillColor": "#E2E8F0", "color": "#CBD5E1", "weight": 0.4, "fillOpacity": 0.2}
            elif layer_mode == "E-Bike Catchment Only":
                if is_b:
                    return {"fillColor": "#3B82F6", "color": "#1D4ED8", "weight": 1.0, "fillOpacity": 0.75}
                return {"fillColor": "#E2E8F0", "color": "#CBD5E1", "weight": 0.4, "fillOpacity": 0.2}
            elif layer_mode == "E-Bike Uplift Zone Only":
                if is_up:
                    return {"fillColor": "#F59E0B", "color": "#B45309", "weight": 1.0, "fillOpacity": 0.8}
                return {"fillColor": "#E2E8F0", "color": "#CBD5E1", "weight": 0.4, "fillOpacity": 0.2}
            elif layer_mode == "Full Multi-Modal Union (Walk + Bike + Auto)":
                if is_w:
                    return {"fillColor": "#10B981", "color": "#047857", "weight": 0.8, "fillOpacity": 0.7}
                elif is_up:
                    return {"fillColor": "#3B82F6", "color": "#1D4ED8", "weight": 0.8, "fillOpacity": 0.65}
                elif is_a_up:
                    return {"fillColor": "#F59E0B", "color": "#B45309", "weight": 0.8, "fillOpacity": 0.65}
                return {"fillColor": "#E2E8F0", "color": "#CBD5E1", "weight": 0.4, "fillOpacity": 0.2}
            else:
                if not (is_w or is_b or is_a_up):
                    return {"fillColor": "#94A3B8", "color": "#64748B", "weight": 0.8, "fillOpacity": 0.7}
                return {"fillColor": "#F1F5F9", "color": "#E2E8F0", "weight": 0.3, "fillOpacity": 0.15}

        # Add GeoJSON layer
        folium.GeoJson(
            corr_cells.__geo_interface__,
            style_function=style_fn,
            tooltip=folium.GeoJsonTooltip(
                fields=["cell_id", "population", "walk_time_min", "ebike_time_min", "eauto_time_min", "nearest_station_walk"],
                aliases=["Cell ID:", "Population:", "Walk Time (min):", "E-Bike Time (min):", "E-Auto Time (min):", "Nearest Station:"],
                localize=True
            )
        ).add_to(m)

        # Add Stations
        if show_pilot_stations:
            for _, r in stations_selected.iterrows():
                folium.CircleMarker(
                    location=[r.geometry.y, r.geometry.x],
                    radius=7,
                    color="#FFFFFF",
                    weight=1.5,
                    fill=True,
                    fill_color="#DC2626",
                    fill_opacity=0.95,
                    tooltip=f"Pilot Station: {r['name']}"
                ).add_to(m)

        if show_context_stations:
            ctx_st = stations_all[stations_all["name"].isin(["Singayyanapalya", "Krishnarajapura"])]
            for _, r in ctx_st.iterrows():
                folium.RegularPolygonMarker(
                    location=[r.geometry.y, r.geometry.x],
                    number_of_sides=3,
                    radius=8,
                    color="#000000",
                    weight=1.5,
                    fill=True,
                    fill_color="#F59E0B",
                    fill_opacity=0.95,
                    tooltip=f"Boundary Context Absorber: {r['name']}"
                ).add_to(m)

        # Add Candidate Feeder Sites (881 street corners) if toggled
        if show_candidates:
            folium.GeoJson(
                candidate_sites_gdf.__geo_interface__,
                name="Candidate Feeder Sites",
                marker=folium.CircleMarker(
                    radius=3.5,
                    color="#6D28D9",
                    weight=1,
                    fill=True,
                    fill_color="#8B5CF6",
                    fill_opacity=0.75
                ),
                tooltip=folium.GeoJsonTooltip(
                    fields=["site_id", "nearest_station", "ride_time_to_station_min"],
                    aliases=["Candidate Site ID:", "Nearest Station:", "Ride Time to Station (min):"],
                    localize=True
                )
            ).add_to(m)

        # Add Top 5 Placed Feeder Hubs if toggled
        if show_top_hubs:
            top_hubs = (selected_sites_t20_df if is_t20 else selected_sites_df).head(5)
            for _, h in top_hubs.iterrows():
                if pd.notna(h.get("lat")) and pd.notna(h.get("lon")):
                    # 5-minute walk buffer (~375m)
                    folium.Circle(
                        location=[h["lat"], h["lon"]],
                        radius=375,
                        color="#D97706",
                        weight=1.5,
                        fill=True,
                        fill_color="#FBBF24",
                        fill_opacity=0.15,
                        dash_array="4, 4"
                    ).add_to(m)
                    # Outer ring
                    folium.CircleMarker(
                        location=[h["lat"], h["lon"]],
                        radius=10,
                        color="#D97706",
                        weight=2,
                        fill=True,
                        fill_color="#FBBF24",
                        fill_opacity=0.4
                    ).add_to(m)
                    # Inner solid hub icon
                    folium.CircleMarker(
                        location=[h["lat"], h["lon"]],
                        radius=5,
                        color="#78350F",
                        weight=2,
                        fill=True,
                        fill_color="#F59E0B",
                        fill_opacity=0.95,
                        tooltip=f"★ Selected Feeder Hub #{int(h['order'])}: {h['site_id']}<br>Marginal Gain: +{h['marginal_gain']:,.0f} unserved residents"
                    ).add_to(m)

        st_folium(m, width="stretch", height=600)


# ==============================================================================
# SCREEN 3: STATION DEEP DIVE (10 STATIONS)
# ==============================================================================
elif nav_choice == "3. Station Deep Dive (10 Stations)":
    st.title("🚉 Station-by-Station Deep Dive Explorer")
    st.markdown("Inspect catchment demographics, ridership utilization, and infrastructure barriers for each of the 10 pilot stations.")

    station_names = ranking_df["name"].tolist()
    sel_station = st.selectbox("Select Station to Inspect:", station_names, index=1)
    
    st_meta = ranking_df[ranking_df["name"] == sel_station].iloc[0]
    st_cells = corr_cells[corr_cells["nearest_station_walk"] == st_meta["station_id"]].copy()

    # Station KPI metrics
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Corridor Rank (Score)", f"#{int(st_meta['rank'])} of 10", f"Score: {st_meta['priority_score']:,.1f}")
    with k2:
        st.metric("Unserved Walk Need", f"{st_meta['walk_uncovered_need']:,.0f} people", help="Residents in station territory living > 15 min walk away.")
    with k3:
        st.metric("Avg Daily Boardings", f"{st_meta['avg_daily_ridership']:,.0f} entries/day", help="Official BMRCL August 2025 entry/exit data.")
    with k4:
        st.metric("Territory Total Population", f"{st_cells['population'].sum():,.0f} people", f"{len(st_cells)} H3 cells")

    st.markdown("---")

    c_left, c_right = st.columns([1.2, 1])

    with c_left:
        # Station population breakdown
        w_st_pop = st_cells[st_cells["walk_time_min"] <= 15.0]["population"].sum()
        b_st_pop = st_cells[(st_cells["ebike_time_min"] <= 15.0) & (st_cells["walk_time_min"] > 15.0)]["population"].sum()
        a_st_pop = st_cells[(st_cells["eauto_time_min"] <= 15.0) & (st_cells["walk_time_min"] > 15.0) & (st_cells["ebike_time_min"] > 15.0)]["population"].sum()
        u_st_pop = st_cells[(st_cells["walk_time_min"] > 15.0) & (st_cells["ebike_time_min"] > 15.0) & (st_cells["eauto_time_min"] > 15.0)]["population"].sum()

        fig_st = go.Figure(data=[go.Pie(
            labels=["Walk Covered", "E-Bike Uplift", "E-Auto Extra", "Unserved Deficit"],
            values=[w_st_pop, b_st_pop, a_st_pop, u_st_pop],
            hole=0.45,
            marker=dict(colors=["#10B981", "#3B82F6", "#F59E0B", "#94A3B8"])
        )])
        fig_st.update_layout(title=f"15-Minute Catchment Partition: {sel_station}", height=340)
        st.plotly_chart(fig_st, width="stretch")

    with c_right:
        st.markdown(f"### 📋 Station Profile: {sel_station}")
        
        # Station specific insight notes
        if "Hopefarm" in sel_station:
            st.markdown("""
            <div class="alert-card">
                <strong>⚠️ The Hopefarm Paradox:</strong><br>
                • <strong>2nd Highest Unserved Need in Corridor</strong> (73,821 residents stranded beyond 15-min walk).<br>
                • <strong>Lowest Daily Boardings</strong> (2,536/day vs. corridor average of 7,817/day).<br>
                • <strong>Root Cause:</strong> Severe traffic gridlock at Hopefarm junction and absent pedestrian footpaths suppress demand. 
                Ridership-weighted scoring drops Hopefarm to #7, highlighting the equity risk of ignoring suppressed demand.
            </div>
            """, unsafe_allow_html=True)
        elif "Whitefield" in sel_station:
            st.markdown("""
            <div class="alert-card">
                <strong>⚠️ Railway Severance Hotspot:</strong><br>
                • <strong>Terminus Station</strong> with 8,464 daily boardings.<br>
                • <strong>South Western Railway Mainline Barrier:</strong> 10 cells (8,517 residents) to the north are cut off from bicycles. 
                Pedestrians can cross via stair footbridge (16.5 min), but e-bikes face a 3.75 km detour through railway underpasses (22.9 min).
            </div>
            """, unsafe_allow_html=True)
        elif "Pattandur" in sel_station:
            st.markdown("""
            <div class="success-card">
                <strong>⭐ Top E-Bike Yield Station:</strong><br>
                • Delivers the largest e-bike uplift on the entire corridor: <strong>+17,547 residents</strong>!<br>
                • High ridership: 10,028 boardings/day.<br>
                • Prime candidate for high-capacity feeder bike-share docking hub.
            </div>
            """, unsafe_allow_html=True)
        elif "Kundalahalli" in sel_station or "Sathya Sai" in sel_station:
            st.markdown("""
            <div class="success-card">
                <strong>✅ Saturated Tech Corridor:</strong><br>
                • Stations spaced barely 1.0 km apart along ITPL Main Road.<br>
                • Catchments overlap completely: virtually <strong>0 unserved residents</strong> within station territory.<br>
                • Does not require additional neighborhood feeder hubs.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            • <strong>Unserved Territory Population:</strong> {st_meta['walk_uncovered_need']:,.0f} residents.<br>
            • <strong>Daily Station Boardings:</strong> {st_meta['avg_daily_ridership']:,.0f} entries/day.<br>
            • <strong>Weighted Priority Rank:</strong> #{int(st_meta['rank'])} out of 10 pilot stations.
            """, unsafe_allow_html=True)

    st.markdown("### Territory Hexagonal Cells")
    st.dataframe(
        st_cells[["cell_id", "population", "walk_time_min", "ebike_time_min", "eauto_time_min", "walk_covered", "ebike_uplift"]]
        .rename(columns={
            "cell_id": "H3 Cell ID",
            "population": "Residents",
            "walk_time_min": "Walk Time (min)",
            "ebike_time_min": "E-Bike Time (min)",
            "eauto_time_min": "E-Auto Time (min)",
            "walk_covered": "Walk Covered?",
            "ebike_uplift": "E-Bike Uplift?"
        }),
        width="stretch",
        hide_index=True
    )


# ==============================================================================
# SCREEN 4: FEEDER HUB SITING PLANNER (OPTIMIZER)
# ==============================================================================
elif nav_choice == "4. Feeder Hub Siting Planner":
    st.title("🎯 Feeder Hub Siting Planner (Max-Coverage Optimizer)")
    st.markdown(
        "Submodular greedy maximum-coverage optimization placing $k$ neighborhood feeder hubs "
        "at optimal street corners to maximize newly covered unserved residents."
    )

    col_ctrl, col_chart = st.columns([1, 2.2])

    active_hub_df = selected_sites_t20_df if is_t20 else selected_sites_df

    with col_ctrl:
        k_val = st.slider("Select Number of Feeder Hubs (k):", min_value=1, max_value=15, value=5)
        subset_hubs = active_hub_df[active_hub_df["k"] <= k_val]
        latest_hub = subset_hubs.iloc[-1]

        st.metric(
            label=f"Feeder Hubs Placed (k = {k_val})",
            value=f"{latest_hub['cumulative_feeder_pop']:,.0f} people",
            delta=f"+{latest_hub['cumulative_feeder_pop'] / TOTAL_CORR_POP * 100:.2f}% corridor reach"
        )
        st.metric(
            label="Total Access (Walk + Feeder Hubs)",
            value=f"{latest_hub['coverage_after']:,.0f} people",
            delta=f"from {latest_hub['coverage_before']:,.0f} baseline"
        )

        st.markdown("""
        <div class="info-card">
            <strong>Honest Engineering Ceiling:</strong><br>
            Placing street-corner hubs with a 5-minute walk catchment reaches up to 10,616 residents with 5 hubs. 
            However, <strong>324,057 unserved residents</strong> live in suburban layouts with no candidate site within a 5-min walk. 
            This proves why <strong>doorstep micromobility</strong> is mandatory.
        </div>
        """, unsafe_allow_html=True)

    with col_chart:
        fig_curve = px.line(
            active_hub_df,
            x="k",
            y="cumulative_feeder_pop",
            markers=True,
            title="Cumulative Marginal Gain Curve (Diminishing Returns)",
            labels={"k": "Number of Feeder Hubs (k)", "cumulative_feeder_pop": "Newly Reached Residents"}
        )
        fig_curve.add_hline(
            y=63214.2 if not is_t20 else 80525.7,
            line_dash="dash",
            line_color="#EF4444",
            annotation_text="Coverable Population Ceiling"
        )
        fig_curve.add_vline(x=k_val, line_dash="dot", line_color="#10B981", annotation_text=f"Selected k = {k_val}")
        fig_curve.update_layout(height=380, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_curve, width="stretch")

    st.markdown("### Top Selected Feeder Hubs Priority Sequence")
    st.dataframe(
        subset_hubs[["order", "site_id", "marginal_gain", "cumulative_feeder_pop", "coverage_after", "lat", "lon"]]
        .rename(columns={
            "order": "Priority Order (k)",
            "site_id": "Hub Site ID",
            "marginal_gain": "Marginal Gain (Residents)",
            "cumulative_feeder_pop": "Cumulative Feeder Pop",
            "coverage_after": "Combined Coverage",
            "lat": "Latitude",
            "lon": "Longitude"
        }),
        width="stretch",
        hide_index=True
    )


# ==============================================================================
# SCREEN 5: STATION PRIORITIZATION MATRIX
# ==============================================================================
elif nav_choice == "5. Station Prioritization Matrix":
    st.title("🏆 Station Prioritization & Policy Matrix")
    st.markdown(
        r"Compare station investment rankings under two distinct objectives: "
        r"**Pure Equity Need** (Unserved Population) vs. **Revenue-Weighted Priority** ($\text{Need} \times \sqrt{\text{Ridership}}$)."
    )

    c_slope, c_table = st.columns([1.2, 1])

    with c_slope:
        # Build slope chart comparison
        slope_df = ranking_df.copy()
        slope_df["need_rank"] = slope_df["walk_uncovered_need"].rank(ascending=False).astype(int)
        slope_df["weighted_rank"] = slope_df["rank"].astype(int)

        fig_slope = go.Figure()
        for _, row in slope_df.iterrows():
            is_hopefarm = "Hopefarm" in row["name"]
            color = "#DC2626" if is_hopefarm else "#94A3B8"
            width = 3.5 if is_hopefarm else 1.5
            
            fig_slope.add_trace(go.Scatter(
                x=["Pure Unserved Need Rank", "Ridership-Weighted Rank"],
                y=[row["need_rank"], row["weighted_rank"]],
                mode="lines+markers+text",
                line=dict(color=color, width=width),
                marker=dict(size=8, color=color),
                text=[f"#{row['need_rank']} {row['name']}", f"#{row['weighted_rank']} {row['name']}"],
                textposition=["middle left", "middle right"],
                showlegend=False
            ))
            
        fig_slope.update_layout(
            title="Station Policy Rank Shift (Need vs. Weighted)",
            yaxis=dict(autorange="reversed", title="Rank (1 = Highest Priority)", dtick=1),
            xaxis=dict(range=[-0.4, 1.4]),
            height=500
        )
        st.plotly_chart(fig_slope, width="stretch")

    with c_table:
        st.markdown("### 📊 Policy Prioritization Table")
        st.dataframe(
            ranking_df[["rank", "name", "walk_uncovered_need", "avg_daily_ridership", "priority_score"]]
            .rename(columns={
                "rank": "Weighted Rank",
                "name": "Station",
                "walk_uncovered_need": "Unserved Need",
                "avg_daily_ridership": "Daily Boardings",
                "priority_score": "Priority Score"
            }),
            width="stretch",
            hide_index=True
        )

        st.markdown("""
        <div class="info-card">
            <strong>Key Governance Insight:</strong><br>
            • <strong>Seetharampalya</strong> ranks #1 across both metrics: massive hinterland (79.3k unserved) and strong ridership (8.4k/day).<br>
            • <strong>Hopefarm Channasandra</strong> collapses 5 spots from #2 to #7 due to suppressed demand. 
            Our tool provides transparency so transport authorities can safeguard transit equity.
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# SCREEN 6: INFRASTRUCTURE & SEVERANCE AUDITS
# ==============================================================================
elif nav_choice == "6. Infrastructure & Severance Audits":
    st.title("🔍 Infrastructure & Spatial Network Audits")
    st.markdown("Micro-geographic network audits exposing physical severance and boundary cordon absorption.")

    tab_rail, tab_boundary = st.tabs(["🚆 Railway Footbridge Severance Audit", "🛡️ Western Boundary Cordon Audit"])

    with tab_rail:
        st.subheader("Physical Barrier: South Western Railway Mainline")
        st.markdown(r"""
        Zooming into the territory north of **Whitefield (Kadugodi) Station**:
        - **10 H3 hexagonal cells (8,516.8 residents)** are walk-covered in $\le 20$ min, but **FAIL to be covered by e-bike in 20 min**.
        - **The Physical Cause:** Pedestrians use a direct stair footbridge over the tracks ($1,179\text{ m}$ / $16.5\text{ min}$). 
        E-bikes and cargo bikes cannot climb stairs and must detour $3.75\text{ km}$ ($22.9\text{ min}$) around railway underpasses.
        """)

        col_sev1, col_sev2 = st.columns(2)
        with col_sev1:
            st.metric("Severance Territory", "10 H3 Cells", "8,517 Residents")
        with col_sev2:
            st.metric("Top Cell Route Penalty", "3,751 m vs 1,179 m", "3.2× Longer Detour")

        st.markdown("""
        <div class="info-card">
            <strong>Policy Action for Civil Engineers:</strong><br>
            Retrofitting railway footbridges with <strong>bicycle wheeling ramps</strong> or elevators immediately unlocks 
            active micro-mobility access for 8,500+ residents without building new vehicular flyovers.
        </div>
        """, unsafe_allow_html=True)

    with tab_boundary:
        st.subheader("Boundary Cordon Audit: Singayyanapalya & KR Puram")
        st.markdown("""
        - **108 Peripheral H3 Cells (108,348 residents)** along the western edge are geometrically closer to **Singayyanapalya** (`CTX_01`) or **Krishnarajapura** (`CTX_02`).
        - **The Boundary Edge Problem:** If evaluating 10 stations in isolation, these 108 cells falsely attach to **Garudacharpalya**, 
        artificially inflating its catchment by **+326%** (from 33k to 141k residents!).
        - **The Algorithmic Solution:** By modeling the 2 western context stations as load absorbers, 108,348 residents are correctly reassigned, 
        preserving 100% mathematical integrity for the pilot.
        """)

        b1, b2, b3 = st.columns(3)
        with b1:
            st.metric("Western Context Cells", "108 Cells", "108,348 Residents")
        with b2:
            st.metric("Absorbed by Singayyanapalya", "15 Cells", "15,770 Residents")
        with b3:
            st.metric("Absorbed by KR Puram", "93 Cells", "92,578 Residents")


# ==============================================================================
# SCREEN 7: SCALE VISION: 83-STATION BENGALURU NETWORK
# ==============================================================================
elif nav_choice == "7. Scale Vision: 83-Station Network":
    st.title("🌐 Scaling Vision: City-Wide 83-Station Rollout")
    st.markdown(
        "Demonstrating algorithmic transferability from the **Whitefield 10-Station Pilot** "
        "to the entire **83-Station BMRCL Namma Metro Network** across Bengaluru."
    )

    st.markdown("""
    <div class="success-card">
        <strong>From Pilot to City-Wide System:</strong> The exact pipeline validated on the Whitefield corridor has been pre-computed 
        and tested on all 83 operational stations across the Purple and Green Lines, processing 5,726 H3 Res-9 cells covering 4.71 million residents.
    </div>
    """, unsafe_allow_html=True)

    # City-wide Network Metrics
    n1, n2, n3, n4 = st.columns(4)
    with n1:
        st.metric("Total Metro Stations", "83 Stations", "Purple & Green Lines")
    with n2:
        st.metric("City-Wide Population in Buffer", "4,711,546 residents", "WorldPop 2020")
    with n3:
        st.metric("H3 Res-9 Grid Resolution", "5,726 Hexagons", "~100 m cell radius")
    with n4:
        st.metric("Algorithmic Complexity", "O(k · |C|)", "Scales sub-linearly")

    st.markdown("---")

    col_map83, col_roadmap = st.columns([1.5, 1])

    with col_map83:
        st.subheader("🗺️ 83-Station City-Wide Network Map")
        fig_83 = px.scatter_mapbox(
            stations_83_df,
            lat="lat",
            lon="lon",
            hover_name="name",
            color="corridor_group",
            color_discrete_map={
                "Whitefield Pilot (10 Stations)": "#DC2626",
                "Western Context Absorber (2 Stations)": "#F59E0B",
                "Bengaluru Metro Network (71 Stations)": "#2563EB"
            },
            zoom=10.2,
            height=500
        )
        fig_83.update_layout(
            mapbox_style="carto-positron",
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.02, bgcolor="rgba(255,255,255,0.85)")
        )
        st.plotly_chart(fig_83, width="stretch")

    with col_roadmap:
        st.subheader("🚀 3-Phase City-Wide Rollout Plan")
        st.markdown("""
        **Phase 1: High-Tech Eastern Corridor (Completed Pilot)**
        - 10 Stations | Whitefield ITPL Corridor
        - High-density tech campuses, extreme arterial congestion
        - Baseline walk reach: 14.6% $\\rightarrow$ Active reach: 29.9%
        
        **Phase 2: High-Density Employment Corridors (Next 25 Stations)**
        - Outer Ring Road (Silk Board to KR Puram) & Electronics City
        - Targeted hub placement at high-ridership interchange stations
        
        **Phase 3: Full Network Integration (All 83 Stations)**
        - Complete Purple & Green Lines
        - Unified micro-mobility integration across BMRCL, BMTC feeder buses, and shared EV fleets
        """)

    st.subheader("📋 83-Station Network Master Directory")
    st.dataframe(
        stations_83_df[["station_id", "name", "corridor_group", "lat", "lon"]].head(25),
        width="stretch",
        hide_index=True
    )
    st.caption("Showing first 25 stations. Complete 83-station dataset exported in data/output_network/stations_83_network.csv.")


# ==============================================================================
# SCREEN 8: PRESENTATION FIGURES GALLERY
# ==============================================================================
elif nav_choice == "8. Presentation Figures Gallery":
    st.title("🖼️ Publication Figures Gallery (SHIFT 2026)")
    st.markdown("All 9 presentation figures generated at **300 DPI** using colorblind-safe palettes and zero layout overlap.")

    figure_options = [
        ("Figure 1: Multi-Modal Catchment Accessibility Map (T=15 vs T=20)", "fig01_access_map_T15_T20.png"),
        ("Figure 2: Corridor Population Breakdown Stacked Bars", "fig02_coverage_bars_T15_T20.png"),
        ("Figure 3: Per-Station Catchment Breakdown (T=15 min)", "fig03_station_stacked_bars_T15.png"),
        ("Figure 4: Parametric Sensitivity Matrix (Speed vs. Overhead)", "fig04_sensitivity_heatmaps.png"),
        ("Figure 5: Physical Feeder Hub Siting & Max-Coverage Curve", "fig05_hub_siting_map_and_curve.png"),
        ("Figure 6: Station Prioritization Divergence Slope Chart", "fig06_station_priority_slope.png"),
        ("Figure 7: Physical Infrastructure Severance Audit (Railway)", "fig07_railway_severance_map.png"),
        ("Figure 8: Western Boundary Cordon Audit (Load Absorption)", "fig08_western_boundary_map.png"),
        ("Figure 9: Executive Dashboard KPI Cards (Headline One-Pager)", "fig09_headline_onepager.png")
    ]

    sel_fig_label = st.selectbox("Select Figure to View in High Resolution:", [f[0] for f in figure_options])
    sel_fig_file = next(f[1] for f in figure_options if f[0] == sel_fig_label)
    fig_path = FIGURES_DIR / sel_fig_file

    if fig_path.exists():
        st.image(str(fig_path), caption=sel_fig_label, width="stretch")
        with open(fig_path, "rb") as f:
            st.download_button(
                label=f"⬇️ Download {sel_fig_file} (300 DPI PNG)",
                data=f.read(),
                file_name=sel_fig_file,
                mime="image/png"
            )
    else:
        st.warning(f"Figure file {sel_fig_file} not found in docs/figures/.")


# ==============================================================================
# SCREEN 9: DATA DOWNLOADS & METHODOLOGY
# ==============================================================================
elif nav_choice == "9. Data Downloads & Methodology":
    st.title("📥 Data Downloads, Reproducibility & Methodology")
    st.markdown("Download raw datasets, GeoPackages, and review data citations.")

    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        st.subheader("📊 Tabular Results (CSV & JSON)")
        
        with open(DATA_DIR / "station_ranking.csv", "rb") as f:
            st.download_button("⬇️ Download Station Rankings (CSV)", f.read(), "station_ranking.csv", "text/csv")
            
        with open(DATA_DIR / "selected_sites.csv", "rb") as f:
            st.download_button("⬇️ Download Selected Feeder Hubs (CSV)", f.read(), "selected_sites.csv", "text/csv")

        with open(DATA_DIR / "catchment_metrics.json", "rb") as f:
            st.download_button("⬇️ Download Catchment Metrics (JSON)", f.read(), "catchment_metrics.json", "application/json")

    with col_dl2:
        st.subheader("🗺️ GIS Spatial Layers (GeoPackage)")
        
        qgis_master = DATA_DIR / "catchments_qgis.gpkg"
        if qgis_master.exists():
            with open(qgis_master, "rb") as f:
                st.download_button("⬇️ Download Master QGIS Catchments (GPKG)", f.read(), "catchments_qgis.gpkg", "application/geopackage+sqlite3")

        with open(DATA_DIR / "cells.csv", "rb") as f:
            st.download_button("⬇️ Download 572 H3 Res-9 Cells Attributes (CSV)", f.read(), "cells.csv", "text/csv")

    st.markdown("---")
    st.subheader("📚 Methodology & Sources")
    st.markdown("""
    • <strong>Road Networks:</strong> OpenStreetMap extracted via OSMnx (ODbL). Safe e-bike graph excludes motorways, trunks, and high-speed primary roads.<br>
    • <strong>Population:</strong> WorldPop 2020 100m Constrained India raster (CC BY 4.0), aggregated via rasterstats zonal statistics onto H3 Resolution-9 hexagons.<br>
    • <strong>Ridership Data:</strong> Official BMRCL August 2025 station-wise entry/exit disclosures via OpenCity (CC BY-NC-SA 4.0).<br>
    • <strong>Optimization:</strong> Submodular Greedy Maximum Coverage Optimizer achieving $(1 - 1/e) \\approx 63.2\\%$ approximation ratio.<br>
    • <strong>Evidence Base:</strong> Calibrated against the WRI India & Toyota Mobility Foundation study (<em>Improving Metro Access in India: Evidence from Three Cities</em>).
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# GLOBAL FOOTER
# -----------------------------------------------------------------------------
st.markdown("""
<div class="app-footer">
    <strong>Bengaluru Metro Feeder Zone Screening Tool</strong> | SHIFT 2026 Hackathon<br>
    Whitefield 10-Station Pilot & 83-Station City-Wide Rollout Framework<br>
    Data Sources: WorldPop 2020, OpenStreetMap contributors, BMRCL RTI August 2025 disclosures.
</div>
""", unsafe_allow_html=True)
