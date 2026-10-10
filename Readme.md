# Last Mile First

## Team: UrbanFluX

## Project subtitle: An open-data tool to choose where Bengaluru’s next e-bike feeder zones go around Metro stations, and which stations need them first.

### SHIFT Sustainable e-Micromobility Hackathon · IIT (BHU) Varanasi · 10–11 October 2026

> We don’t just map accessibility gaps; we help decide where the next feeder hubs should go.

### 1. Problem
A Metro station can be geographically close to a resident yet still be inconvenient to reach on foot. Long or disconnected walking routes, limited first-/last-mile options, travel time, cost, and safety can make public transport less practical.

Last Mile First is an open-data screening and decision-support tool for identifying where potential shared e-bike feeder hubs could improve access to Bengaluru Metro stations.

The core question is:

> **If a city could establish only `k` e-bike feeder hubs, where should they be placed to bring the greatest number of currently underserved people within practical reach of a Metro station?**

The tool is intended to prioritize areas for further investigation. It is not a ridership forecast and does not claim that everyone who becomes reachable will use an e-bike or Metro.

### 2. Proposed users
• Transport planners and public agencies: identify accessibility gaps and compare possible feeder-zone allocations.
• Shared-mobility operators: screen candidate areas for further feasibility assessment.
• Residents: potential beneficiaries of more convenient connections to public transport.

### 3. Proposed methodology
a. Assemble spatial data. Use Bengaluru Metro station locations, OpenStreetMap (OSM) road/pedestrian networks, and gridded population data such as WorldPop. Check the coverage, date, licence, and completeness of each dataset.
b. Create a population grid. Represent the study area as population cells (a hexagonal grid is one option) and associate each cell with an estimated population.
c. Build a network-based walking baseline. Assign walking travel times to suitable network edges and calculate shortest travel times from population cells to Metro stations. This accounts for street-network paths rather than relying only on straight-line buffers.
d. Model a potential e-bike scenario. Use explicit assumed riding speeds and an unlock/parking-time overhead. Test alternative speeds and travel-time thresholds (for example, 10, 15, and 20 minutes) rather than treating one assumption as fact.
e. Estimate potential accessibility uplift. Compare the population reachable under the baseline and e-bike scenarios. Report the result as potential additional accessibility, not actual adoption or ridership.
f. Select candidate feeder hubs. Where time allows, use a greedy maximum-coverage optimizer to select up to k candidate locations that add the most newly served population, avoiding double-counting between selected hubs.
g. Visualize and compare scenarios. Provide an interactive map, a ranked set of accessibility gaps, and before/after coverage summaries.

Important modeling distinction

A simple walk-versus-e-bike comparison estimates the potential benefit of the faster mode; by itself, it does not model access to shared vehicles at specific hubs. The fuller hub-placement model should account for walking from a population cell to a candidate hub, unlock/parking overhead, and riding from that hub to a Metro station, subject to a reasonable walk-to-hub limit.

### 4. Planned outputs
• Map of the pilot area, Metro stations, population distribution, and walking-accessibility gaps.
• Estimated potential accessibility uplift under stated e-bike assumptions.
• Candidate feeder-hub locations selected for a user-defined k, where implemented.
• Before/after comparison of potentially covered population.
• A concise list of assumptions, limitations, and validation needs.

### 5. Data and references
Planned data sources (availability and licensing will be checked during implementation):
• Bengaluru Metro station locations: a verified station-coordinate dataset or a suitable open map source.
• OpenStreetMap: street and pedestrian network geometry and road attributes. https://www.openstreetmap.org/
• WorldPop: gridded population estimates. https://www.worldpop.org/
• GHSL / GHS-POP: alternative or supplementary gridded population data, subject to coverage and suitability checks. https://ghsl.jrc.ec.europa.eu/
• BMRCL ridership data: optional, if a suitable dataset is publicly accessible and its definitions and coverage can be verified.
• WRI India, Improving Metro Access in India: background evidence on last-mile access. https://wri-india.org/research/improving-metro-access-india

All datasets used in the final implementation should be credited with their exact source, access date, licence, and any processing performed.

### 6. Assumptions and limitations
• Population grids are estimates and may not represent exact residential locations or individual travel behavior.
• OSM network coverage and tags can be incomplete or outdated.
• Travel speeds, time thresholds, and unlock/parking overheads are assumptions unless supported by local measurements.
• Initial travel times may not include congestion, signals, waiting, weather, or all safety constraints.
• OSM road class alone is not a complete cycling-safety assessment.
• Candidate hubs are screening locations, not confirmed available or permitted sites.
• Potentially accessible population is not equivalent to predicted demand, ridership, or emissions reduction.
• Results should be validated against site availability, safe routes, operating costs, local commuter needs, and actual demand before deployment.

### 7. Scope and priorities for the hackathon
Core MVP
a. Build a working walking-accessibility baseline for a manageable Bengaluru pilot area.
b. Compare it with a clearly labelled potential e-bike scenario.
c. Show the accessibility gaps and a before/after population summary.

Next priority
d. Implement candidate-hub selection and a maximum-coverage optimizer.
e. Add an interactive interface for changing k and scenario assumptions.

Stretch goals
• Optional station-ridership weighting if reliable data is available.
• More detailed road-suitability screening.
• Comparisons across additional modes or cities.

If time is limited, prioritize one reproducible end-to-end demonstration over many incomplete features.


### 8. Tools and implementation
The final tools and libraries will be recorded here after they are actually used. Potential choices include Python, GeoPandas, OSMnx, NetworkX, Shapely, raster/vector data tools, and a lightweight interactive map framework. These are options, not a claim that the project already uses them.

### 9. AI assistance and authorship
• AI assistant: Claude - used for documentation drafting, and/or coding assistance as applicable.
• Human work: Team members are responsible for project planning, methodology discussion, reviewing, testing, understanding, and validating all code and results.

### 10. Reproducibility and running the project
Status: Implementation instructions will be completed once the code and dependencies are in place.

After implementation, add:

1. Required Python/runtime version.
2. Installation instructions and dependency file.
3. Data download/setup steps, including licences and expected file locations.
4. Exact command to run the application or analysis.
5. A small test or sample dataset, where permitted.
6. Known issues and expected outputs.

