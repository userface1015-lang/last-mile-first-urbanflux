# Results - Whitefield 10-Station Pilot

Project: UrbanFluX - Last Mile First: Metro Feeder Zone Screening Tool
Study area: Whitefield 10-station corridor, Bengaluru
Status: Pilot results; selected outputs require final run verification

> **Scope note:** These results describe the Whitefield 10-station pilot and its defined study-area buffer. They are not Bengaluru-wide estimates. Values below were shared from a previous analysis run and should be reconciled against one final, reproducible run before being treated as final.

## 1. Overview
The pilot compares estimated population accessibility under walking, e-bike and e-auto scenarios using network-based travel-time catchments. It also examines station-level accessibility gaps and explores candidate feeder-hub placement.
This is a screening exercise. It estimates potential geographic coverage under stated assumptions; it does not directly measure actual trips, future ridership, mode adoption, safety, or operational feasibility.

## 2. Study area and population base
The pilot includes these ten stations:
1. Whitefield (Kadugodi)
2. Hopefarm Channasandra
3. Kadugodi Tree Park
4. Pattandur Agrahara
5. Sathya Sai Hospital
6. Nallurahalli
7. Kundalahalli
8. Seetharampalya
9. Hoodi
10. Garudacharpalya

Nearby context stations are used where needed to reduce artificial truncation of catchments near the pilot boundary, but are excluded from the ten-station priority ranking.

|Analysis area          |Estimated population|
|-----------------------|-------------------:|
|Core corridor territory|453,687             |
|3 km study-area buffer |562,035             |

Population estimates are based on the WorldPop 2020 gridded dataset aggregated to the analysis grid. These are gridded estimates, not observed counts of prospective Metro users.

## 3. Population coverage by mode

### 3.1 Fifteen-minute threshold — study-area buffer
Previously reported estimates:

|Scenario                           |Estimated population covered|Share of buffer population|
|-----------------------------------|---------------------------:|-------------------------:|
|Walking                            |83,839                      |14.9%                     |
|Walking + e-bike                   |170,694                     |30.4%                     |
|Walking + e-bike + e-auto (union)  |268,567                     |47.8%                     |
|Residual outside the combined union|293,469                     |52.2%                     |

The e-bike scenario was reported to add 86,855 people beyond walking coverage, and e-auto to add a further 97,873 beyond the walking-plus-e-bike union.
Interpretation: Under the model assumptions, adding alternative feeder modes increases estimated population coverage within the selected travel-time threshold. This is scenario-based, not observed demand or coverage guaranteed by a limited number of deployed hubs.

### 3.2 Twenty-minute threshold — study-area buffer
Previously reported estimates for walking and e-bike:

|Scenario                               |Estimated population covered|Share of buffer population|
|---------------------------------------|---------------------------:|-------------------------:|
|Walking                                |133,670                     |23.8%                     |
|Walking + e-bike                       |303,973                     |54.1%                     |
|Residual outside walking + e-bike union|258,063                     |45.9%                     |

The e-bike scenario was reported to add 170,303 people beyond walking coverage.
Comparison caution: These figures show the walking-plus-e-bike union at 20 minutes. They should not be compared directly with the 15-minute all-mode union, which also includes e-auto. For a like-for-like comparison, regenerate both thresholds with the same modes and denominator.

### 3.3 Fifteen-minute threshold — core corridor territory
A separate set of previously reported figures uses the core corridor population of 453,687 rather than the larger study-area buffer.

|Scenario                           |Estimated population covered|Share of core corridor population|
|-----------------------------------|---------------------------:|--------------------------------:|
|Walking                            |69,489                      |15.3%                            |
|Walking + e-bike                   |138,547                     |30.5%                            |
|Walking + e-bike + e-auto (union)  |226,640                     |50.0%                            |
|Residual outside the combined union|227,048                     |50.0%                            |

The reported e-bike uplift over walking was 69,058 people; e-auto added a further 88,092 beyond the walking-plus-e-bike union.

## 4. Station priority ranking
The previous ten-station ranking used walking-uncovered population combined with a relative station-entry weight. It is a prioritisation heuristic, not a direct estimate of unmet trips.

|Rank|Station              |Previously reported priority value|
|---:|---------------------|---------------------------------:|
|1   |Seetharampalya       |83,691                            |
|2   |Whitefield (Kadugodi)|78,312                            |
|3   |Hoodi                |51,760                            |
|4   |Pattandur Agrahara   |39,327                            |
|5   |Kadugodi Tree Park   |30,860                            |
|6   |Nallurahalli         |25,604                            |
|7   |Hopefarm Channasandra|23,951                            |
|8   |Garudacharpalya      |18,613                            |
|9   |Sathya Sai Hospital  |2,118                             |
|10  |Kundalahalli         |1,839                             |


## 5. Feeder-hub siting
The prototype uses a greedy maximal-coverage approach to select candidate hub locations for a specified hub budget, k. The hub-constrained scenario includes walking to a hub and the assumed unlock/parking overhead.
Previously reported results for five hubs:

|Travel-time threshold|Reported additional coverage|Reported coverage pairs|
|---------------------|---------------------------:|----------------------:|
|15 minutes           |10,426                      |161                    |
|20 minutes           |17,208                      |509                    |

The theoretical doorstep e-bike uplift assumes a vehicle is available at the origin. It is an upper-bound scenario, not the coverage achievable from a limited set of hubs.

## 6. Sensitivity and interpretation
The pilot includes sensitivity visualisations for travel-time thresholds and e-bike assumptions. Working assumptions include walking at 4.5 km/h, e-bike travel at 13.5 km/h (sensitivity range 12–15 km/h), and e-auto travel at 18 km/h, with the stated access/parking or waiting overheads.
Interpret sensitivity results as model responses to assumed inputs, not calibration against observed journeys.

## 7. Key observations
Based on the pilot outputs currently available:
1. Network-based accessibility reveals spatial gaps that simple circular buffers do not represent accurately.
2. Alternative-mode scenarios increase modelled coverage under the chosen speed and overhead assumptions.
3. Station rankings depend on the prioritisation formula. Need-only and ridership-weighted rankings should be compared.
4. Doorstep uplift and hub-constrained coverage are different metrics. A large theoretical uplift does not establish that a small hub network can deliver the same coverage.
5. Boundary handling matters. Nearby context stations and network continuity can affect which station is credited with coverage.
6. Data completeness is a limitation. Missing footpaths or network connections in OpenStreetMap may underestimate walking accessibility and inflate apparent gains from other modes.

## 8. Limitations
• This is a ten-station pilot, not a city-wide Bengaluru result.
• WorldPop cells provide population estimates, not observed Metro demand.
• OSM pedestrian and road networks may be incomplete or incorrectly connected.
• Speeds, thresholds and overheads are assumptions, not locally calibrated travel-time measurements.
• The road-class filter is a coarse network filter, not a street-level safety assessment.
• Station-entry counts are not equivalent to feeder demand or willingness to use e-bikes.
• The analysis focuses on access to Metro from the home end and does not model the complete journey or destination-end last mile.
• Hub candidates require ground validation for space, access, parking, charging, permissions, cost and operating feasibility.
• Modelled accessibility does not establish ridership growth, emissions reductions or financial viability.
