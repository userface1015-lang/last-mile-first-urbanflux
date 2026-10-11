# QGIS Visualization Guide: Walk & E-Bike Catchments
## Whitefield 10-Station Metro Pilot Corridor

This guide explains how to visualize separate and combined catchments for **Walking Pedestrians**, **E-Bikes**, and **E-Bike Uplift** in **QGIS (Version 3.x)**.

---

## Option 1: One-Click Drag-and-Drop (Pre-Styled & Pre-Filtered) — Recommended

All catchments have been pre-filtered and bundled with automated QGIS style files (`.qml`).  
Folder location: [`data/output/qgis_layers/`](file:///e:/Project/data/output/qgis_layers)

Simply open QGIS and drag any of these `.gpkg` files directly into the map window:

| Layer File | What It Displays | Pre-Configured Styling |
| :--- | :--- | :--- |
| [`walk_catchment_15min.gpkg`](file:///e:/Project/data/output/qgis_layers/walk_catchment_15min.gpkg) | 73 walkable cells ($\le 15\text{ min}$, 66,417 pop) | **Teal** (`#2A9D8F`), 70% opacity |
| [`ebike_catchment_15min.gpkg`](file:///e:/Project/data/output/qgis_layers/ebike_catchment_15min.gpkg) | 132 e-bike cells ($\le 15\text{ min}$, 120,865 pop) | **Blue** (`#457B9D`), 70% opacity |
| [`ebike_uplift_15min.gpkg`](file:///e:/Project/data/output/qgis_layers/ebike_uplift_15min.gpkg) | 75 incremental e-bike cells beyond walk (+69,215 pop) | **Coral / Amber** (`#E76F51`), 75% opacity |
| [`combined_active_15min.gpkg`](file:///e:/Project/data/output/qgis_layers/combined_active_15min.gpkg) | 148 active cells (Walk OR E-Bike, 135,632 pop) | **Deep Navy** (`#1D3557`), 65% opacity |
| [`walk_boundary_15min.gpkg`](file:///e:/Project/data/output/qgis_layers/walk_boundary_15min.gpkg) | Dissolved single outer perimeter for walkability | Transparent fill, 1.0mm Teal outline |
| [`ebike_boundary_15min.gpkg`](file:///e:/Project/data/output/qgis_layers/ebike_boundary_15min.gpkg) | Dissolved single outer perimeter for e-bikes | Transparent fill, 1.0mm Blue outline |
| [`metro_stations.gpkg`](file:///e:/Project/data/output/qgis_layers/metro_stations.gpkg) | 10 pilot stations + 2 context stations | Red circle & Gold triangle markers with bold labels |

*Note: Because matching `.qml` files sit alongside each `.gpkg`, QGIS automatically applies the color palettes and labels upon drag-and-drop.*

---

## Option 2: Master Multi-Layer GeoPackage

A single master file containing all 13 layers is available at:  
[`data/output/catchments_qgis.gpkg`](file:///e:/Project/data/output/catchments_qgis.gpkg)

1. Drag [`data/output/catchments_qgis.gpkg`](file:///e:/Project/data/output/catchments_qgis.gpkg) into QGIS.
2. A pop-up dialog **"Select Items to Add"** will appear listing all 13 layers:
   - `walk_catchment_15min`
   - `ebike_catchment_15min`
   - `ebike_uplift_15min`
   - `walk_boundary_15min`
   - `ebike_boundary_15min`
   - `metro_stations`
3. Select the layers you want to inspect and click **"Add Layers"**.
4. In the QGIS **Layers** panel on the left, check or uncheck layers to toggle between walkability and e-bikes.

---

## Option 3: Working with the Original `data/output/cells.gpkg`

If you are loading the raw dataset [`data/output/cells.gpkg`](file:///e:/Project/data/output/cells.gpkg):

### Method A: Duplicate & Feature Filter
1. Drag [`data/output/cells.gpkg`](file:///e:/Project/data/output/cells.gpkg) into QGIS.
2. In the Layers panel, right-click `cells` $\rightarrow$ **Duplicate Layer**.
3. Rename the first layer to `Walk Catchment (15 min)`:
   - Right-click $\rightarrow$ **Filter...** (or press `Ctrl + F`).
   - Enter expression:
     ```sql
     "walk_covered" = true AND "is_corridor_assigned" = true
     ```
   - Click **OK**.
4. Rename the second layer to `E-Bike Catchment (15 min)`:
   - Right-click $\rightarrow$ **Filter...**
   - Enter expression:
     ```sql
     "ebike_covered" = true AND "is_corridor_assigned" = true
     ```
   - Click **OK**.
5. Repeat for `E-Bike Uplift`:
   - Filter expression:
     ```sql
     "ebike_uplift" = true AND "is_corridor_assigned" = true
     ```

### Method B: Rule-Based Symbology (Single Layer)
1. Double-click the `cells` layer to open **Layer Properties** $\rightarrow$ **Symbology**.
2. Change the top dropdown from *Single Symbol* to **Rule-based**.
3. Add three rules:
   - **Rule 1 (Walk)**: Label: `Walk Catchment` | Filter: `"walk_covered" = true AND "is_corridor_assigned" = true` | Color: `#2A9D8F` (Teal)
   - **Rule 2 (E-Bike Uplift)**: Label: `E-Bike Uplift` | Filter: `"ebike_uplift" = true AND "is_corridor_assigned" = true` | Color: `#457B9D` (Blue)
   - **Rule 3 (Unserved)**: Label: `Unserved` | Filter: `"walk_covered" = false AND "ebike_covered" = false AND "is_corridor_assigned" = true` | Color: `#E0E0E0` (Grey)
4. Click **Apply** and **OK**.

---

## Adding an OpenStreetMap Basemap in QGIS
To see roads, buildings, and metro lines underneath:
1. In the QGIS **Browser Panel** (usually top-left), expand **XYZ Tiles**.
2. Double-click **OpenStreetMap**.
3. In the **Layers Panel**, drag the `OpenStreetMap` layer to the very bottom.
