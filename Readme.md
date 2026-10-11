# Last Mile First: Urban Micro-Mobility Feeder Intelligence

**An Open-Data Decision Support Framework for Sustainable e-Micromobility Planning in Bengaluru**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bengaluru-metro-feeder.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-informational.svg)](https://www.python.org/)
[![H3 Resolution 9](https://img.shields.io/badge/Spatial%20Grid-H3%20Res--9%20(~100m)-teal.svg)](https://h3geo.org/)

**Developed by Team UrbanFluX**  
*SHIFT Sustainable e-Micromobility Hackathon · Indian Institute of Technology (BHU), Varanasi*  
*10–11 October 2026*

---

### 🌐 Live Production Application
Explore the complete interactive spatial screening tool live in your browser:  
👉 **[https://bengaluru-metro-feeder.streamlit.app](https://bengaluru-metro-feeder.streamlit.app)**

---

## 1. Executive Vision & Problem Statement

Rapid transit investments in Indian megacities frequently encounter the **"first-and-last-mile chasm"**: high-capacity mass rapid transit lines run directly through densifying suburbs, yet stations remain inaccessible to the vast majority of residents living merely 1 to 3 kilometres away. In Bengaluru, where rapid suburban expansion has outpaced pedestrian sidewalk networks and secondary arterial connectivity, a commuter living 1.5 kilometres from a Namma Metro station faces disjointed footpaths, unmanaged intersections, and prohibitive auto-rickshaw fares—driving them right back to private two-wheelers and personal automobiles.

**Last Mile First** transforms raw open geospatial and ridership data into an actionable, mathematically sound screening framework. Rather than producing generic heatmaps or theoretical accessibility buffers, our engine answers the decisive capital-allocation question facing transport authorities and shared-mobility operators:

> **"If a transit authority or shared-mobility operator has capital to deploy exactly $k$ neighborhood e-bike feeder hubs, precisely where should they be anchored to liberate the largest number of currently stranded residents, and which stations warrant priority intervention?"**

Starting from a rigorous **10-station pilot** along East Bengaluru's critical Whitefield corridor, our framework models multi-modal impedance across pedestrian paths, protected e-bike networks, and feeder transit, before projecting algorithmic transferability to the entire **83-station BMRCL network**.

---

## 2. Empirical Findings: The Whitefield Corridor Pilot

We evaluated the 10-station contiguous pilot corridor spanning the eastern reach of Namma Metro's Purple Line—from **Garudacharpalya** through **Whitefield (Kadugodi)**—encompassing a continuous catchment territory of **453,687 residents** discretized across **572 H3 Resolution-9 hexagonal cells** (cell radius $\approx 100\text{ m}$).

```
[KR Puram] ── [Singayyanapalya] ── [Garudacharpalya] ── ... ── [Pattandur Agrahara] ── [Whitefield (Kadugodi)]
  └────── Western Context ─────┘    └────────────────── 10-Station Pilot Study ──────────────────┘
        (Load Absorbers)
```

### Key Quantitative Findings (at Travel Budget $T = 15\text{ min}$)

| Metric / Dimension | Walking Baseline (4.5 km/h) | Shared E-Bike (13.5 km/h + 5m) | Combined Active Reach | E-Auto Upper Bound (18 km/h + 6m) | Residual Unserved Gap |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Reachable Population** | **66,417** | **129,631** | **129,631** | 217,435 | **236,252** |
| **Corridor Share (%)** | **14.6%** | **28.6%** | **28.6%** | 47.9% | **52.1%** |
| **Incremental Uplift** | Baseline | **+63,214 (+14.0%)** | **+63,214 (+14.0%)** | +87,804 (+19.4%) | — |
| **Hexagonal H3 Cells** | 87 cells | 165 cells | 165 cells | 275 cells | **297 cells** |

*Note: At $T = 20\text{ minutes}$ (the commuter willingness-to-travel benchmark established by WRI India’s STAMP disclosures), active mobility reach expands to **171,114 residents (37.7%)**, demonstrating the dramatic sensitivity of suburban access to small travel-budget increments.*

### Core Takeaways from the Data
1. **The Pedestrian Ceiling is Paralyzing:** Only **14.6%** of corridor residents live within a 15-minute walk of a station. Relying solely on pedestrian access guarantees that over **85% of residents remain structurally excluded** from rapid transit.
2. **E-Micromobility Nearly Doubles Catchment:** Shared electric micro-mobility unlocks **+63,214 additional residents** within the identical 15-minute budget—an instantaneous **95.2% expansion** over walking alone.
3. **The Persistent Spatial Deficit:** Even with on-demand motorized e-autos, over **52% (236,252 residents)** remain stranded beyond 15 minutes, highlighting why physical, neighborhood-level feeder infrastructure must be prioritized.

---

## 3. Mathematical Methodology & Algorithmic Formulation

```
┌─────────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────────┐
│   Spatial Discretization│    │ Multi-Modal Impedance    │    │ Submodular Optimization  │
│   • H3 Resolution-9     ├───►│ • OSMnx Street Networks  ├───►│ • Greedy Max-Coverage    │
│   • WorldPop Constrained│    │ • Mode-Specific Overheads│    │ • (1 - 1/e) Guarantee    │
└─────────────────────────┘    └──────────────────────────┘    └──────────────────────────┘
```

### 3.1 Spatial Discretization & Population Mapping
The study envelope is tessellated into Uber **H3 Resolution-9 hexagonal cells** (average hexagon area $\approx 0.1\text{ km}^2$, edge length $\approx 174\text{ m}$). Population is assigned to each cell $c \in \mathcal{C}$ using the **WorldPop 2020 100m Constrained India dataset**, aggregated via zonal statistics to eliminate spatial edge-distortion.

### 3.2 Network Impedance & Road-Class Safety Filtering
Rather than relying on naive Euclidean buffers, travel times are calculated along routable street graphs extracted from OpenStreetMap via **OSMnx**:
* **Pedestrian Network ($\mathcal{G}_{\text{walk}}$):** Routable across all navigable paths, residential alleys, footways, and living streets. Operating speed: $v_{\text{walk}} = 4.5\text{ km/h}$; overhead: $t_{\text{walk}}^{\text{overhead}} = 0\text{ min}$.
* **Safe E-Bike Network ($\mathcal{G}_{\text{bike}}$):** Rigorously road-class filtered to **exclude expressways, motorways, trunk corridors, and high-speed primary roads** lacking bicycle right-of-way. Operating speed: $v_{\text{bike}} = 13.5\text{ km/h}$; fixed vehicle unlocking, battery check, and parking overhead: $t_{\text{bike}}^{\text{overhead}} = 5.0\text{ min}$.
* **E-Auto Network ($\mathcal{G}_{\text{auto}}$):** Unconstrained vehicular road network. Operating speed: $v_{\text{auto}} = 18.0\text{ km/h}$; ride-hailing dispatch and boarding latency: $t_{\text{auto}}^{\text{overhead}} = 6.0\text{ min}$.

For any cell centroid $c$ and station $s$:
$$t_{\text{mode}}(c, s) = t_{\text{mode}}^{\text{overhead}} + \frac{d_{\mathcal{G}_{\text{mode}}}(c, s)}{v_{\text{mode}}}$$

### 3.3 Feeder Hub Siting via Submodular Greedy Maximum-Coverage
To place $k$ feeder hubs among $M = 881$ candidate street-corner intersections $\mathcal{S}$, we formulate the problem as a discrete **Maximum Coverage Facility Location Problem**. Let $U \subseteq \mathcal{C}$ be the set of unserved population cells ($t_{\text{walk}}(c) > T$). A candidate site $j \in \mathcal{S}$ covers cell $c$ if $d_{\text{walk}}(c, j) \le d_{\text{max}}^{\text{access}}$ (where $d_{\text{max}}^{\text{access}} = 375\text{ m}$, equivalent to a 5-minute access walk) and the ride time from $j$ to the nearest station meets the budget.

$$\max_{S \subseteq \mathcal{S}, \, |S| \le k} f(S) = \sum_{c \in \bigcup_{j \in S} \text{Cov}(j) \cap U} \text{Pop}(c)$$

Because the objective function $f(S)$ is **monotone submodular** (exhibiting diminishing marginal returns), our greedy optimization algorithm iteratively selects:
$$j^* = \arg\max_{j \in \mathcal{S} \setminus S} \left[ f(S \cup \{j\}) - f(S) \right]$$
This guarantees a theoretical approximation factor of:
$$\alpha \ge 1 - \frac{1}{e} \approx 63.21\%$$
of the global optimum, delivering real-time execution in sub-second response times.

---

## 4. Micro-Geographic Field Discoveries & Policy Audits

Our computational audits uncovered three spatial realities that conventional aggregate planning overlooks:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 THREE CRITICAL AUDITS                   │
                  └─────────────────────────────────────────────────────────┘
                                /              |              \
                               /               |               \
                              ▼                ▼                ▼
                     [HOPEFARM PARADOX]  [RAILWAY SEVERANCE]  [BOUNDARY CORDON]
                     Suppressed Demand   Footbridge Barrier   Boundary Sinks
                     vs Ridership Bias   North of Whitefield  Prevent +326% Error
```

### 1. The Hopefarm Paradox (Equity vs. Suppressed Demand)
* **The Symptom:** **Hopefarm Channasandra** exhibits the **2nd highest unserved need** in the entire corridor (**73,821 residents** living outside a 15-minute walk), yet records the **lowest daily boardings** of all pilot stations (**2,536 passengers/day**, versus a corridor mean of 7,817/day).
* **The Root Cause:** Severe intersection bottlenecking and absent pedestrian pathways physically suppress transit usage.
* **The Policy Warning:** If planners weight feeder hub deployment purely by current station ridership ($\text{Need} \times \sqrt{\text{Ridership}}$), Hopefarm plummets from **#2 down to #7**. Our dual-ranking matrix explicitly surfaces this divergence, safeguarding transport equity from self-reinforcing ridership penalties.

### 2. South Western Railway Severance Audit (Whitefield Terminus)
* **The Barrier:** North of **Whitefield (Kadugodi) Station**, the South Western Railway mainline creates a severe physical barrier.
* **The Finding:** Exactly **10 H3 hexagonal cells (8,517 residents)** can reach the station on foot via an existing pedestrian stair footbridge ($1,179\text{ m}$ / $16.5\text{ min}$), but **fail to be reached by bicycle within 20 minutes** ($3,751\text{ m}$ / $22.9\text{ min}$) because bikes cannot climb stairs and must detour $3.75\text{ km}$ through congested vehicular underpasses.
* **The Engineering Remedy:** Retrofitting the existing railway footbridge with **low-cost bicycle wheeling ramps** immediately restores multi-modal accessibility for over 8,500 residents at a fraction of the cost of new flyovers.

### 3. Western Boundary Cordon Audit (Singayyanapalya & KR Puram)
* **The Pitfall:** Modeling a 10-station pilot in isolation causes boundary distortion. **108 peripheral cells (108,348 residents)** along the western edge are geometrically closer to **Singayyanapalya** (`CTX_01`) or **Krishnarajapura** (`CTX_02`).
* **The Correction:** Without modeling these two western stations as "load absorbers", these 108,348 residents falsely attach to **Garudacharpalya**, artificially inflating its catchment by **+326%** (from 33k to 141k residents). Introducing explicit boundary absorbers preserved 100% mathematical integrity across all corridor allocations.

---

## 5. Scaling Vision: The 83-Station City-Wide Network

While demonstrated in deep detail on the Whitefield pilot, our framework is architected for city-wide transferability across the entire operational **83-Station BMRCL Namma Metro Network** (Purple and Green Lines):

* **Spatial Coverage:** **5,726 H3 Resolution-9 hexagons** evaluated city-wide.
* **Population Impact:** **4,711,546 residents** within the urban station buffer analyzed.
* **Phased Rollout Strategy:**
  * **Phase 1 (Immediate Pilot):** 10 Whitefield corridor stations (IT/industrial tech corridor).
  * **Phase 2 (Dense Urban Core):** 28 interchange and commercial core stations (Majestic, MG Road, Indiranagar, Jayanagar).
  * **Phase 3 (Suburban Periphery):** 45 terminal and outer corridor stations (Kengeri, Silk Institute, Nagasandra, Challaghatta).

---

## 6. Interactive Web Dashboard Overview

The project includes an enterprise-grade Streamlit application structured into 9 purpose-built screens:

```
├── 1. Executive Overview          ── Corridor KPI cards, population partition bar chart, core metrics
├── 2. Multi-Modal Access Map      ── Reactive Folium map with layer filters & candidate site overlays
├── 3. Station Deep Dive           ── Granular catchment diagnostics, pie breakdown, Hopefarm notes
├── 4. Feeder Hub Siting Planner   ── Dynamic k-slider, diminishing return curves, selected hub coordinates
├── 5. Station Prioritization      ── Policy slope chart (Pure Need vs. Ridership-Weighted Score)
├── 6. Infrastructure Audits       ── Railway severance zoom-in & western boundary load absorption
├── 7. 83-Station Scale Vision     ── City-wide BMRCL network map & 3-phase rollout roadmap
├── 8. Presentation Gallery        ── 9 publication-grade 300 DPI analytical figures with download options
└── 9. Data Downloads & Sources    ── One-click raw CSV, JSON, and master GeoPackage exports
```

---

## 7. Repository Structure

```
├── Readme.md                          <- Project documentation and scientific report
├── requirements.txt                   <- Pinned production Python dependencies
├── packages.txt                       <- OS-level dependencies for geospatial libraries (GDAL/GEOS)
├── app/
│   └── main.py                        <- 9-screen production Streamlit web application
├── src/
│   ├── config.py                      <- Corridor parameters, speeds, overheads, and CRS constants
│   ├── networks.py                    <- OSMnx graph acquisition, road-class filtering, & caching
│   ├── travel_times.py                <- Shortest-path Dijkstra calculations across modes
│   ├── optimizer.py                   <- Submodular greedy maximum-coverage facility solver
│   ├── stations.py                    <- BMRCL coordinate parsing and corridor subset filtering
│   └── study_area.py                  <- H3 spatial tessellation and WorldPop zonal integration
├── scripts/
│   ├── run_diagnostic_audit.py        <- Comprehensive sanity check and corridor validation
│   ├── generate_presentation_figures.py <- Headless matplotlib generator for 9 publication figures
│   ├── export_qgis_layers.py          <- Formats geopackages and QML styles for GIS work
│   └── verify_all_project_math.py     <- Mathematical verification and consistency assertions
├── data/
│   ├── output/                        <- Precomputed CSVs, Parquet files, and GeoPackages
│   │   ├── cells.csv                  <- 572 H3 Res-9 cells with multi-modal travel times
│   │   ├── candidate_sites.gpkg       <- 881 candidate street-corner feeder locations
│   │   ├── selected_sites.csv         <- Prioritized greedy hub sequence (k=1 to 15)
│   │   ├── station_ranking.csv        <- Dual-metric priority rankings for all pilot stations
│   │   ├── stations_83_network.csv    <- City-wide 83-station coordinates and line tags
│   │   └── catchments_qgis.gpkg       <- Multi-layer GeoPackage for desktop GIS analysis
│   └── qgis_layers/                   <- 12 cartographically styled .qml GIS layers
├── docs/
│   ├── figures/                       <- 9 high-resolution presentation figures (300 DPI)
│   ├── methodology.md                 <- Extended technical documentation and equations
│   └── data-sources.md                <- Comprehensive provenance and licensing register
└── tests/                             <- Pytest automated verification suite
```

---

## 8. Installation & Reproduction Guide

### Prerequisites
* Python 3.11 or higher
* Recommended: Virtual environment (`venv` or `conda`)

### Step 1: Clone the Repository
```bash
git clone https://github.com/avikachauhan246/shift-2026-K7UYFL.git
cd shift-2026-K7UYFL
```

### Step 2: Set Up Virtual Environment & Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run the Test & Verification Suite
Verify mathematical consistency and pipeline assertions:
```bash
pytest tests/ -v
python scripts/verify_all_project_math.py
```

### Step 4: Launch the Interactive Dashboard Locally
```bash
streamlit run app/main.py
```
Open your browser at `http://localhost:8501`.

---

## 9. Data Sources, Governance & Licensing

Every dataset utilized in this project is strictly open-access, verifiable, and attributed:

| Dataset | Provider / Source | License | Application in Project |
| :--- | :--- | :--- | :--- |
| **Gridded Population (100m)** | [WorldPop 2020](https://www.worldpop.org/) Constrained India | CC BY 4.0 | Residential population density per H3 cell |
| **Street & Pedestrian Graph** | [OpenStreetMap Contributors](https://www.openstreetmap.org/) | ODbL 1.0 | Routable pedestrian and safe e-bike network graphs |
| **Namma Metro Station Coordinates** | BMRCL Open Data / OpenCity.in | Open Access | Station coordinates, platform access nodes, lines |
| **Station Ridership Disclosures** | BMRCL RTI Disclosures (August 2025) | CC BY-NC-SA 4.0 | Daily boardings, station utilization, weighting |
| **Commuter Thresholds & Evidence** | WRI India & Toyota Mobility Foundation | Academic / Open Access | Calibrated $T=15$ and $T=20$ minute travel budgets |

---

## 10. Research Citation & Team UrbanFluX

If you build upon or reference this methodology in academic, urban planning, or civic research, please cite:

```bibtex
@misc{urbanflux2026lastmile,
  title={Last Mile First: An Open-Data Decision Support Framework for Sustainable e-Micromobility Planning in Bengaluru},
  author={Chauhan, Avika and Team UrbanFluX},
  year={2026},
  howpublished={SHIFT Sustainable e-Micromobility Hackathon, IIT (BHU) Varanasi},
  url={https://github.com/avikachauhan246/shift-2026-K7UYFL}
}
```

*Crafted with commitment to sustainable urban mobility and open science by **Team UrbanFluX**.*
