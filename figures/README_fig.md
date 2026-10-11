# UrbanFluX - Figure Guide and Interpretation for the Pilot Analysis

The figures support three questions:
1. How does the estimated population reachable by different feeder modes change with the travel-time budget?
2. Which stations and locations appear to have the largest remaining accessibility gaps?
3. Where could a limited number of physical feeder hubs be placed to improve access?

Scope: These are pilot-corridor results, not citywide findings. The maps and estimates depend on the available open datasets, network connectivity, and model assumptions.

### Figure 1 - Multimodal Network Catchments at 15 and 20 Minutes
File: fig01_access_map_T15_T20.png
What it shows
This figure compares estimated access across the pilot corridor under two travel-time budgets: 15 minutes and 20 minutes. The spatial panels distinguish the walking catchment, additional potential reach from e-bikes, additional reach attributed to e-autos, and the remaining uncovered area or population.
The analysis uses network-based travel times rather than assuming that every location inside a circular radius is equally accessible. This matters because actual routes follow the mapped street network, whose connectivity and layout can differ substantially from straight-line distance.

How to interpret it
* Walking coverage provides the baseline against which additional feeder-mode reach is assessed.
* E-bike uplift represents locations or residents potentially reached by e-bike but not already covered by the walking baseline, under the model’s assumptions.
* E-auto extra reach represents additional coverage attributed to e-autos beyond the walking and e-bike coverage, as defined in the analysis.
* Residual gap highlights locations that remain outside the modeled coverage.

Compare the two panels to see where a longer travel-time budget expands coverage and where substantial gaps persist.

Why it matters
The figure makes the accessibility problem spatially visible. It helps identify areas where feeder modes may complement walking and where further investigation or intervention could be warranted.

⸻

### Figure 2 - Population Coverage Breakdown at 15 and 20 Minutes
File: fig02_coverage_bars_T15_T20.png

What it shows
This figure summarizes estimated population coverage using stacked bars. Instead of showing where access changes, it emphasizes how many residents fall into each coverage category under the two travel-time budgets.
The categories distinguish the walking baseline, additional reach attributed to e-bikes, additional reach attributed to e-autos, and the residual underserved population.

How to interpret it
Read each bar as a breakdown of the population within the specified analysis area. The segment sizes indicate the population associated with each category. The percentage labels, where provided, express the corresponding share of the stated denominator.

The comparison helps answer:
* How much coverage is already provided by walking?
* How much additional reach is associated with e-bikes under the modeled assumptions?
* How much additional reach is associated with e-autos?
* How much population remains outside the modeled coverage?

Why it matters
A map communicates geography, but a population breakdown communicates scale. This figure helps judges understand the potential magnitude of the accessibility gap without having to estimate it visually from the map.

⸻

### Figure 3 - Station-Level Coverage and Remaining Gaps
File: fig03_station_stacked_bars_T15.png

What it shows
This figure breaks down modeled population coverage by station across the ten stations in the Whitefield pilot corridor. The stacked bars distinguish the coverage categories used in the analysis and make differences between station catchments easier to compare.

How to interpret it
Look at both the portions of each bar associated with modeled coverage and the portion representing the residual gap.
* A larger walking segment indicates more population reached within the modeled walking threshold.
* A larger e-bike uplift segment indicates more additional population potentially reached by e-bike beyond walking.
* A larger e-auto segment indicates additional reach attributed to e-autos.
* A large residual segment indicates that a substantial population remains outside the modeled coverage.

Stations with large residual gaps deserve investigation, but a large gap alone does not establish that a feeder service would be commercially viable or that a particular hub location is optimal.

Why it matters
Corridor-wide totals can conceal substantial differences between stations. This figure helps narrow the analysis from a general accessibility problem to station-specific planning questions.

Planning implication
Use this figure alongside the station-priority ranking. The coverage breakdown describes the modeled accessibility situation; the ranking applies the project’s chosen prioritization rule.

⸻

### Figure 4 - Sensitivity to E-Bike Speed and Access Overhead

File: fig04_sensitivity_heatmaps.png

What it shows
These heatmaps examine how estimated e-bike doorstep uplift changes under different assumptions about effective e-bike travel speed and the time spent accessing, unlocking, and parking a vehicle.
The panels show results for the 15-minute and 20-minute travel-time budgets. The highlighted baseline cell identifies the reference assumptions used for comparison.

How to interpret it
Each cell represents a scenario, not a separate observed outcome.
* Moving across the speed axis shows how the estimate changes when assumed riding speed changes.
* Moving along the overhead axis shows how the estimate changes when the non-riding time allowance changes.
* Higher values indicate greater modeled e-bike uplift under that particular combination of assumptions.

The matrix helps distinguish results that remain relatively stable across scenarios from results that depend strongly on optimistic assumptions.

Why it matters
Travel speeds and access overheads are uncertain inputs. A sensitivity analysis makes this uncertainty visible instead of presenting one modeled estimate as though it were exact.

⸻

### Figure 5 - Candidate Feeder Hub Locations and Coverage Gains

File: fig05_hub_siting_map_and_curve.png

What it shows
This figure combines a spatial view of candidate feeder hub placements with a curve showing how modeled population coverage changes as the number of selected hubs, (k), increases.
The optimization searches candidate locations to cover additional residents within the model’s hub-access assumptions. It therefore addresses a different question from the doorstep scenario: not simply where e-bikes could extend reach, but where a limited number of physical hubs could be placed.

How to interpret it
Map panel: The numbered or highlighted locations indicate selected candidate hubs. Their placement illustrates how the optimizer distributes a limited set of hubs across the modeled corridor.
Coverage curve: The horizontal axis represents the number of hubs selected. The vertical axis represents the modeled population reached. The marginal gain from adding a hub can be assessed by comparing consecutive points.
If successive additions produce smaller gains, the curve exhibits diminishing marginal returns: each additional hub adds less new coverage than earlier hubs.

Why it matters
A planning authority or operator may have a limited budget and be unable to place hubs everywhere. The optimizer provides a way to compare deployment sizes and candidate locations rather than relying solely on visual inspection.

⸻

### Figure 6 - Station Prioritization: Unmet Need vs. Ridership-Weighted Score
File: fig06_station_priority_slope.png

What it shows
This figure compares two station rankings:
* Need-only ranking: prioritizes stations according to the modeled population with unmet walking-access need.
* Ridership-weighted ranking: combines the unmet-need measure with the station’s average daily boarding measure, according to the project’s prioritization formula.

The lines connect stations across the two rankings, showing which stations retain their relative position and which move when ridership is incorporated.

How to interpret it
A station that ranks highly under both approaches may have a strong combination of unmet modeled access need and existing station use.
A station that ranks highly on unmet need but moves down in the weighted ranking illustrates a policy trade-off: prioritizing the size of the accessibility gap does not necessarily produce the same ordering as prioritizing a gap weighted by existing transit use.
Conversely, a station that rises under the weighted score may have a relatively strong ridership contribution to its final priority.

Why it matters
There is no universally correct station ranking without a policy objective. A need-only ranking emphasizes accessibility deficits, while a ridership-weighted ranking also considers existing transit utilization.
Showing both helps decision-makers see the consequences of the chosen prioritization rule rather than treating one score as an objective truth.

⸻

### Figure 7 - Railway Severance and Potential Access Barriers
File: fig07_railway_severance_map.png

What it shows
This map examines a selected location near the South Western Railway corridor where railway infrastructure may constrain movement between nearby areas. It highlights the relationship between modeled population cells, railway infrastructure, and a mapped pedestrian crossing or bridge.

How to interpret it
The figure contrasts the modeled travel implications of different crossing or route options. It illustrates why a short straight-line distance to a Metro station does not necessarily imply an equally short or convenient network journey.
It also raises a distinction between pedestrian access and access suitable for wheeled feeder modes. A route that can be traversed by pedestrians may not necessarily be practical for bicycles or other wheeled modes.

Why it matters
Network-based accessibility depends on more than distance. Infrastructure barriers and the availability of usable crossings can affect whether a modeled feeder connection is practical.

⸻

### Figure 8 - Western Boundary Effects and Context-Station Assignment
File: fig08_western_boundary_map.png

What it shows
This figure investigates how population cells near the western edge of the pilot analysis area are assigned between the pilot stations and nearby context stations, including stations outside the pilot ranking.
It addresses a spatial-boundary problem: cells near the edge of a study area may be closer or better connected to a station outside the selected pilot group.

How to interpret it
The highlighted cells show where modeled territory may be absorbed by nearby context stations rather than by the pilot stations. This can affect station-level population totals and comparisons.
Without context stations, the analysis could misleadingly attribute population or accessibility gaps to a pilot station simply because a nearby alternative station was omitted from the assignment process.

Why it matters
A corridor is an analytical boundary, not necessarily a boundary in people’s travel choices. Including context stations can help reduce misleading edge effects when interpreting station-level results.

⸻

Reading the Figures Together
The figures form a planning workflow:
1. Figures 1–2: establish the spatial pattern and population scale of modeled multimodal access.
2. Figure 3: compare the access situation across individual pilot stations.
3. Figure 4: test how sensitive the e-bike estimate is to uncertain assumptions.
4. Figure 5: examine how a limited number of physical hubs could be placed.
5. Figure 6: compare alternative station-prioritization objectives.
6. Figures 7–8: investigate infrastructure barriers and spatial-boundary effects that may influence interpretation.

Together, they support a screening tool for deciding where further investigation and pilot planning may be most useful. They do not replace field audits, operational feasibility checks, demand estimation, or detailed deployment planning.

General Limitations
* The analysis covers the Whitefield 10-station pilot corridor, not all of Bengaluru.
* Results depend on the completeness and accuracy of the mapped walking and road networks.
* Travel speeds, access overheads, catchment thresholds, and optimization settings are assumptions that influence results.
* Doorstep e-bike uplift should not be confused with the coverage achievable from a limited set of physical hubs.
* Modeled population coverage does not establish actual ridership, willingness to pay, service demand, or commercial viability.
* Railway-barrier and boundary findings are candidates for further validation, not confirmed on-ground findings.
* All numerical results presented in the main project README should be regenerated from a consistent, documented run of the analysis.
