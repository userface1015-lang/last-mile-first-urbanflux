# UrbanFluX - Data Sources

### 1. Metro Station Locations
* Dataset: Bengaluru Metro Stations
* File: data/bengaluru_metro_stations.gpkg
* Format: GeoPackage (128 KB)
* Verified status: 63 operational stations recorded in EPSG:32643 (UTM Zone 43N).
* Purpose: Defines metro station locations for spatial analysis and accessibility modelling.

### 2. Metro Ridership Data
* Dataset: BMRCL Station-wise Hourly Ridership
* File: data/bmrc1_hourly_ridership_aug2025.xlsx
* Format: Excel (245 KB)
* Verified status: 1,355 rows covering 83 stations, with hourly slots and daily totals for August 2025.
* Purpose: Supports calculation of average daily station entries and station-priority screening.
* Related dataset: data/raw/bmrc1_station_codes.csv provides 95 station code-to-name mappings.
* Data-quality note: Four station-code mapping rows contain unquoted commas, handled using a custom line splitter.

### 3. GHSL Population Data
* Dataset: GHSL GHS-POP 2020 Population Raster
* File: data/ghsl_tile/GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R8_C26.tif
* Format: GeoTIFF (49 MB)
* Verified status: 10,000 × 10,000 cells at 100 m resolution. The recorded spatial bounds cover the metro stations with an additional buffer.
* Purpose: Population-grid input and fallback for accessibility coverage estimation.

### 4. WorldPop Population Data
* Dataset: WorldPop India 2020 Constrained Population Raster
* File: data/worldpop/ind_pop_2020_CN_100m_R2025A_v1.tif
* Format: GeoTIFF (approximately 759 MB)
* Recorded status: The inventory screenshot reported approximately 112 MB downloaded out of 759 MB, with the download running in the background at that time.
* Purpose: Intended for population-based accessibility estimation.

### 5. Traffic Police Road-Crash Data
* Dataset: BTP Road Crashes, 2023 and 2024
* Files:
    * data/btp_crashes_2023.csv
    * data/btp_crashes_2024.csv
* Format: CSV files (approximately 2.6 KB and 2.3 KB)
* Verified status: Police-station-wise fatal and total crash counts were recorded in the inventory. The 2023 data reports 43 fatal crashes associated with Whitefield, the highest count in Bengaluru in that dataset.
* Potential use: Further road-risk analysis for feeder planning.

### 6. Traffic Police Jurisdictions
* Dataset: Traffic Police Jurisdictions
* File: data/btp_jurisdictions_2022.kml
* Format: KML (815 KB)
* Verified status: 47 police jurisdictions recorded in EPSG:4326.
* Processing note: The inventory indicates that the file opens with GeoPandas.
* Potential use: Linking aggregated crash records to geographic police jurisdictions.

### 7. Research Reference
* Publication: WRI India and Toyota Mobility Foundation, STAMP Working Paper (2023).
* File: data/documents/Improving_India_Metro_access_i_WRI.pdf
* Format: PDF (1.35 MB)
* Recorded details: The inventory identifies a 62-page study of 7,200 metro users and reports that shared modes account for more than 75% of last-mile access, with a 20-minute access threshold.
* Purpose: Provides contextual motivation for studying metro access and feeder-mode accessibility.

### 8. External Sources
* OpenStreetMap
* WorldPop
* Global Human Settlement Layer (GHSL)
* WRI India
