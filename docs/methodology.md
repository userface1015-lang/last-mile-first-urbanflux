# UrbanFluX - Methodology

### 1. Overview
UrbanFluX is an open-data decision-support tool designed to identify gaps in walking access to Bengaluru Metro stations and screen potential locations for e-bike feeder hubs.
The methodology combines network-based accessibility analysis, population-grid data, mode-specific travel-time scenarios, and greedy maximal-covering optimization.
The workflow has four main stages:
a. Construct network-based catchments around metro stations.
b. Estimate travel-time accessibility using Dijkstra’s algorithm.
c. Overlay accessibility results with population-grid data to estimate the population reached.
d. Use a greedy algorithm to select candidate feeder-hub locations that maximize additional population coverage.

The tool is intended for preliminary planning and scenario comparison. Its outputs are estimates based on open data and explicit assumptions, not predictions of actual ridership or guarantees of real-world accessibility.

### 2. Study Area and Data

2.1 Study Area
The pilot focuses on the Whitefield corridor of Bengaluru Metro. A 3 km buffer around the selected stations defines the main study area, with an additional 500 m margin used when preparing the transport networks.
Spatial operations are performed in a projected coordinate reference system, EPSG:32643, so that distances and buffers are measured in metres.
Results are labelled as belonging to the Whitefield 10-station corridor and should not be interpreted as city-wide findings.

2.2 Data Sources
The project uses the following open-data inputs:
* OpenStreetMap (OSM): Street and pedestrian networks used to estimate network-based travel times.
* WorldPop 2020: Population-grid estimates used to estimate the population associated with accessible areas.
* Bengaluru Metro station data: Station locations used as accessibility origins.
* Metro station-entry data: Reported station-entry figures used as a demand-priority weighting where comparable data are available.

### 3. Why Buffered-Edge Catchments?
   
3.1 Limitations of Euclidean Buffers
A Euclidean buffer creates a circular area around a metro station using a fixed straight-line radius. Although computationally simple, it does not represent the routes available to pedestrians.
A location may lie within the circle but remain difficult to reach because of disconnected streets, railway infrastructure, restricted links, or an incomplete pedestrian network.
For this reason, UrbanFluX does not use Euclidean buffers as its primary accessibility measure. They are used to define the study-area boundary rather than to determine which locations are reachable.

3.2 Limitations of Convex Hulls
A convex hull encloses a set of points within the smallest convex polygon containing them. When applied to reachable network points or edges, it can fill spaces between network segments that are not themselves reachable through the mapped network.
This can overestimate accessible land and population, particularly where the street network is fragmented or irregular.
A convex hull may be useful for some forms of spatial summarization, but it is not used as the primary catchment method in UrbanFlux.

3.3 Buffered-Edge Approach
UrbanFluX first identifies reachable portions of the mapped walking network. The reachable network edges are then buffered by a small distance to produce a polygonal approximation of the accessible area.
The implementation uses a 7 m buffer around reachable network edges.
This approach keeps the catchment closely associated with the mapped network while producing an area that can be intersected with population-grid cells.
The resulting polygons support spatial comparison and population estimation without assuming that every location inside a large circle or convex hull is equally accessible.

3.4 Limitations
Buffered-edge catchments are still approximations. Their accuracy depends on the completeness and connectivity of the mapped network, the selected buffer width, and the method used to assign population to catchment areas.
Missing footpaths, incorrect connections, or inaccurate station locations can lead to underestimation or overestimation of accessibility. The catchments should therefore be interpreted as estimates of potential access, not proof that every mapped location is safely or practically reachable.

### 4. Network Travel-Time Analysis Using Dijkstra’s Algorithm

4.1 Purpose
Dijkstra’s algorithm calculates shortest-path distances or costs through a graph with non-negative edge weights. UrbanFlux uses it to estimate minimum travel time along the mapped network rather than relying on straight-line distance.

4.2 Network Representation
The transport network is represented as a graph:
* Nodes represent network locations such as intersections.
* Edges represent connected street or path segments.
* Edge weights represent estimated travel time along each segment.

For an edge of length (L) metres and an assumed speed (v) kilometres per hour, the travel time in minutes is:

$$t = \left(\frac{L}{1000v}\right) \times 60$$

The weights are assigned using the speed assumptions selected for each travel mode.

4.3 Multi-Source Shortest Paths
Rather than calculating a separate shortest-path search for every population cell, the implementation uses a multi-source shortest-path approach from the metro stations.
The network is processed using reversed edges where required by the implementation, allowing travel-time estimates to be calculated efficiently from multiple station origins.
The resulting network travel times are used to determine which network locations fall within the chosen accessibility threshold.

4.4 Travel Modes and Assumptions
The pilot evaluates three scenarios:
* Walking: Assumed speed of 4.5 km/h.
* E-bike: Assumed speed of 13.5 km/h, with a sensitivity range of 12–15 km/h and a 5-minute unlock/parking overhead.
* E-auto: Assumed speed of 18 km/h with a 5-minute waiting-time overhead.
  
The primary threshold is 15 minutes, with 10-minute and 20-minute thresholds used for sensitivity analysis.
The e-bike network applies a coarse road-class filter that excludes motorway and trunk road segments. This is a network-filtering rule, not a validated road-safety assessment. The e-auto scenario uses the mapped driving network without that filter.
These speed and overhead values are modelling assumptions, not locally calibrated measurements.

4.5 Combining Accessibility Scenarios
Walking, e-bike, and e-auto catchments are evaluated separately.
For combined coverage, a population-grid cell is considered covered if it falls within the catchment of at least one included mode. Where relevant, the minimum estimated travel time across the available modes is used to represent the quickest modelled option.
The analysis distinguishes between:
* Population covered by walking.
* Additional population covered by e-bike beyond walking coverage.
* Additional population covered by e-auto beyond both walking and e-bike coverage.
* Population remaining outside the combined catchments.

E-bike uplift is therefore a comparison against the walking baseline, not a forecast of how many people will actually use an e-bike.

### 5. Population Coverage Estimation

5.1 Population Grid
The study uses WorldPop 2020 population data, aggregated to H3 resolution 9 hexagonal cells.
The grid provides a consistent spatial unit for comparing accessibility across the study area. Population estimates are associated with the cells and then analysed against the accessibility catchments.

5.2 Coverage Calculation
The population associated with cells classified as covered is aggregated to estimate the number of people within each modelled catchment.
For a given scenario:
$$P_{\text{missed}} = \sum_{i \in C} P_i$$

where:
* (C) is the set of cells classified as covered.
* (P_i) is the population estimate assigned to cell (i).

Additional coverage is calculated by counting only population not already included in the baseline scenario.
For example:

$$P_{\text{uplift}} = P_{\text{walk+e-bike}} - P_{\text{walk}}$$


This difference should be calculated using consistent cell-level coverage sets to avoid double-counting population.

5.3 Interpreting the Results
The population figures are spatial estimates based on gridded population data. They do not establish the number of commuters, current metro users, or people willing to adopt feeder services.
WorldPop and GHSL population estimates differed substantially in preliminary checks. The reason for the discrepancy has not been established, so population totals should be interpreted with that unresolved data limitation in mind.

### 6. Feeder-Hub Selection Using a Greedy Algorithm

6.1 Optimization Objective
Mapping accessibility gaps identifies where potential improvements may be needed. The next step is to determine where a limited number of feeder hubs could provide the greatest additional coverage.
UrbanFluX uses a greedy maximal-covering approach to select candidate hub locations.
The objective is to maximize the additional underserved population brought within the modelled reach of selected hubs, subject to a fixed number of hubs (k).

6.2 Candidate Locations
Candidate hub locations are generated along the mapped network. In the current pilot configuration, the candidate set contains approximately 596 network locations, spaced at roughly 120 m intervals.
The model accounts for walking access to a hub and an additional access overhead. The pilot uses a walking access limit of up to 5 minutes to reach a hub, together with a 5-minute overhead in the feeder-trip calculation.
These assumptions constrain the area each candidate hub can serve and should be stated alongside the results.

6.3 Greedy Selection Procedure
The algorithm follows these steps:
1. Identify population cells not covered by the baseline walking-access scenario.
2. Determine which underserved cells can be served by each candidate hub under the modelled travel-time and access constraints.
3. Calculate the additional population each candidate could cover that is not already covered by previously selected hubs.
4. Select the candidate providing the largest marginal population gain.
5. Update the set of covered cells and recalculate marginal gains for the remaining candidates.
6. Repeat until (k) hubs have been selected or no candidate adds further coverage.

This procedure produces a ranked sequence of hub selections for different values of (k), allowing scenarios with different numbers of hubs to be compared.

6.4 Why Greedy Optimization?
A greedy approach is computationally practical when many candidate locations must be evaluated. It prioritizes the largest immediate additional coverage at each iteration and avoids exhaustive enumeration of every possible combination of hub locations.
However, a greedy solution is not necessarily the globally optimal placement. Its quality depends on the candidate set, coverage rules, and objective function.

6.5 Interpreting Hub Results
The optimization estimates the additional population that could be brought within the modelled reach of selected hubs. It does not establish that the hubs are commercially viable or ready for deployment.
The model does not automatically account for land availability, installation and operating costs, charging infrastructure, permissions, actual e-bike availability, or validated safety conditions unless these are explicitly included as constraints or inputs.

### 7. Station-Priority Screening
In addition to selecting hub locations, UrbanFluX ranks metro stations to help identify where further feeder-access investigation may be most useful.
The priority score combines the estimated walking-uncovered population associated with a station and a relative station-entry weighting based on average daily boardings.
The boarding weight is calculated relative to the mean average daily boardings across stations in the analysis. Where comparable ridership data are unavailable, a neutral weight is used and the station should be flagged.
This weighting is a planning heuristic: it gives greater priority to stations with both an estimated accessibility gap and higher observed station entries. It is not a calibrated measure of unmet demand.
Station-level rankings should be accompanied by a need-only ranking so that high-need locations are not obscured by the ridership weighting.

### 8. Key Assumptions and Limitations
The results should be interpreted in light of the following limitations:
* Geographic scope: The current pilot focuses on the Whitefield 10-station corridor and is not a city-wide ranking.
* Open-data dependence: Results depend on the completeness and quality of mapped networks, station locations, and population grids.
* Travel-time assumptions: Mode speeds and access overheads are assumed rather than locally calibrated.
* Home-end access: The analysis primarily estimates access from residential population areas towards metro stations. It does not fully model access at the destination or workplace end of a trip.
* No timetable-based routing: The model does not integrate scheduled bus or metro connections.
* No adoption forecast: Estimated coverage uplift does not predict actual e-bike use, ridership, or behavioural change.
* Safety limitations: The road-class filter is a coarse exclusion rule and should not be described as a safety guarantee.
* Hub feasibility: The optimization does not by itself establish operational, financial, or regulatory feasibility.
* Population uncertainty: Differences between population datasets remain unresolved and can materially affect absolute population estimates.

### 9. Intended Use and Future Work
UrbanFluX is designed as an initial screening tool to help planners compare accessibility scenarios and identify candidate areas for further study.
Potential next steps include:
* Expanding the analysis from the pilot corridor to all relevant Bengaluru Metro stations.
* Validating network connectivity and walking routes through field checks.
* Testing sensitivity to walking speeds, network assumptions, and catchment parameters.
* Incorporating more detailed road-risk, charging, and infrastructure data.
* Evaluating hub feasibility using cost, land availability, and operational constraints.
* Improving the representation of access at both ends of a public-transport trip.

The tool should support, rather than replace, local validation and transport-planning judgement.
