"""
scripts/generate_reports_pdf.py
Generates two comprehensive, professionally styled PDF reports:
1. docs/PROJECT_WORK_COMPLETED_REPORT.pdf - Complete audit of work done, data acquired, architecture, and numerical findings.
2. docs/FORWARD_PLAN_AND_NEXT_STEPS.pdf - Forward planning, next steps, 24-hr schedule, brief swap playbook, and pitch strategy.
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

# Theme Palette
PRIMARY = colors.HexColor("#1A365D")    # Deep Navy
SECONDARY = colors.HexColor("#2B6CB0")  # Slate Blue
ACCENT = colors.HexColor("#2A9D8F")     # Emerald Teal
DARK_TEXT = colors.HexColor("#2D3748")  # Charcoal
LIGHT_BG = colors.HexColor("#F7FAFC")   # Soft Grey
BORDER_COLOR = colors.HexColor("#E2E8F0")
HIGHLIGHT = colors.HexColor("#E76F51")  # Coral


class NumberedCanvas(canvas.Canvas):
    """Canvas that adds header and page number footer on all pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 800, "SHIFT 2026 | Metro Feeder Zone Screening Tool (Bengaluru)")
            self.drawRightString(541, 800, "Development & Planning Audit")
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(54, 792, 541, 792)

        # Footer (all pages)
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(54, 45, 541, 45)
        
        self.drawString(54, 32, "Confidential - Project Development Report | IIT (BHU) Varanasi Hackathon")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(541, 32, page_str)
        self.restoreState()


def build_styles():
    """Build typography hierarchy styles."""
    styles = getSampleStyleSheet()

    doc_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        spaceAfter=6
    )

    doc_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceAfter=14
    )

    h1 = ParagraphStyle(
        "H1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2 = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=DARK_TEXT,
        spaceAfter=6
    )

    bullet = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=DARK_TEXT,
        leftIndent=12,
        spaceAfter=3
    )

    table_header = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell = ParagraphStyle(
        "TD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=DARK_TEXT
    )

    callout_text = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=PRIMARY
    )

    return {
        "doc_title": doc_title,
        "doc_subtitle": doc_subtitle,
        "h1": h1,
        "h2": h2,
        "body": body,
        "bullet": bullet,
        "th": table_header,
        "td": table_cell,
        "callout": callout_text
    }


def make_callout(text: str, styles, border_color=ACCENT, bg_color=LIGHT_BG):
    """Create a styled callout box."""
    p = Paragraph(text, styles["callout"])
    t = Table([[p]], colWidths=[487])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("BOX", (0, 0), (-1, -1), 1, border_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


# ==============================================================================
# REPORT 1: COMPLETED WORK AUDIT
# ==============================================================================
def generate_report_1(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    s = build_styles()
    story = []

    # Title Banner
    story.append(Paragraph("Metro Feeder Zone Screening Tool", s["doc_title"]))
    story.append(Paragraph("<b>Report 1: Audit of Work Completed & Architecture Implementation</b><br/>SHIFT 2026 | Preliminary, Whitefield 10-Station Corridor (Git commit: <code>b390e44</code>)", s["doc_subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary & Problem Framing", s["h1"]))
    story.append(Paragraph(
        "<b>The Decision Supported:</b> Given a limited budget for <i>k</i> electric feeder zones (e-bikes and e-autos), "
        "which locations bring the most unserved people within a 15-minute door-to-station trip on safe roads, and which stations need them first? "
        "The tool serves as a first-pass, open-data screening system for BMRCL (Namma Metro), BMTC, and shared-EV operators (e.g., Yulu).",
        s["body"]
    ))
    story.append(Paragraph(
        "<b>Evidence Base:</b> Directly calibrated against the published <b>WRI India & Toyota Mobility Foundation STAMP study (2023)</b>, "
        "surveying 7,200 metro commuters across Bengaluru, Delhi, and Nagpur. The study documented that walking and shared modes account for over 75% "
        "of last-mile trips and established a 20-minute accessibility sensitivity threshold.",
        s["body"]
    ))
    story.append(make_callout(
        "<b>Key Finding:</b> Physical walk access alone serves <b>14.6% (66,417 residents)</b> within 15 minutes in the core corridor. "
        "Road-filtered e-bike feeder availability expands reach by <b>+43,571 (9.6%) to +90,882 (20.0%)</b> residents (+69,215 / +15.3% baseline), "
        "lifting metro access to 29.9% (135,632 residents), while physical deployment of 5 feeder hubs captures +10,616 (+2.3%) unserved residents at T = 15 min and +17,036 (+3.8%) at T = 20 min.",
        s
    ))
    story.append(Spacer(1, 10))

    # Section 2: Data Acquisition
    story.append(Paragraph("2. Data Collection & Audit Status (100% Acquired & Verified)", s["h1"]))
    story.append(Paragraph("All raw datasets were acquired, placed in <code>data/raw/</code>, opened, and verified without error:", s["body"]))

    data_rows = [
        [Paragraph("ID", s["th"]), Paragraph("Dataset Name", s["th"]), Paragraph("Local File", s["th"]), Paragraph("Dimensions / Features", s["th"]), Paragraph("Verified Status", s["th"])],
        [Paragraph("D2", s["td"]), Paragraph("Bengaluru Metro Stations", s["td"]), Paragraph("bengaluru_metro_stations.gpkg", s["td"]), Paragraph("63 stations, EPSG:32643 UTM 43N", s["td"]), Paragraph("Verified (GeoPandas)", s["td"])],
        [Paragraph("D3", s["td"]), Paragraph("BMRCL Hourly Ridership", s["td"]), Paragraph("bmrcl_hourly_ridership_aug2025.xlsx", s["td"]), Paragraph("1,355 rows, 83 stations (Aug 2025 RTI)", s["td"]), Paragraph("Verified (pandas/openpyxl)", s["td"])],
        [Paragraph("D3-Ref", s["td"]), Paragraph("Station Codes Lookup", s["td"]), Paragraph("bmrcl_station_codes.csv", s["td"]), Paragraph("95 station code-to-name mappings", s["td"]), Paragraph("Verified (Custom Splitter)", s["td"])],
        [Paragraph("D4", s["td"]), Paragraph("WorldPop India 2020", s["td"]), Paragraph("ind_pop_2020_CN_100m_R2025A_v1.tif", s["td"]), Paragraph("100m resolution, 724 MB GeoTIFF", s["td"]), Paragraph("Verified (rasterio)", s["td"])],
        [Paragraph("D5", s["td"]), Paragraph("GHSL Population Tile", s["td"]), Paragraph("GHS_POP_E2020_100_R8_C26.tif", s["td"]), Paragraph("10,000x10,000 grid, 49 MB Mollweide", s["td"]), Paragraph("Verified (rasterio fallback)", s["td"])],
        [Paragraph("D8", s["td"]), Paragraph("BTP Crash Records 2023-24", s["td"]), Paragraph("btp_crashes_2023.csv & 2024.csv", s["td"]), Paragraph("Police station-wise fatal & total crashes", s["td"]), Paragraph("Verified (Whitefield #1)", s["td"])],
        [Paragraph("D7", s["td"]), Paragraph("BTP Police Jurisdictions", s["td"]), Paragraph("btp_jurisdictions_2022.kml", s["td"]), Paragraph("47 jurisdictions, EPSG:4326 KML", s["td"]), Paragraph("Verified (Fiona KML)", s["td"])],
        [Paragraph("E1", s["td"]), Paragraph("WRI STAMP Paper (2023)", s["td"]), Paragraph("Improving_metro_access_in_India_WRI.pdf", s["td"]), Paragraph("62-page research study PDF", s["td"]), Paragraph("Verified local copy", s["td"])],
    ]
    t_data = Table(data_rows, colWidths=[28, 120, 140, 115, 84])
    t_data.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_data)
    story.append(Spacer(1, 10))

    # Section 3: Architecture & Pipeline Modules
    story.append(Paragraph("3. Pipeline Architecture & Implementation Milestones", s["h1"]))
    story.append(Paragraph("All core pipeline stages have been built as standalone, testable Python modules adhering to strict contracts:", s["body"]))

    arch_bullets = [
        "<b>Step S0 & S1 (Environment & Config):</b> Pinned dependencies in <code>requirements.txt</code>, created <code>.gitignore</code>, and implemented <code>src/config.py</code> validating <code>config/params.yaml</code> without hardcoded magic numbers.",
        "<b>Step S3 (Station Cleaner & Pilot Selection):</b> Implemented <code>src/stations.py</code>. Mapped station name variants to official RTI records. Configured 10 continuous stations along the Whitefield corridor (ST_001 to ST_010) with an automated toggle for scaling to all 63 stations.",
        "<b>Step S4 (Study Area Boundary):</b> Implemented <code>src/study_area.py</code>. Formed 3 km core buffer (74.12 sq km) and +500m build margin (91.43 sq km) in metric CRS <code>EPSG:32643</code>.",
        "<b>Step S5 (Multi-Modal Road Networks & Safety Filter):</b> Implemented <code>src/networks.py</code>. Downloaded OSM graphs for Walk (16,849 nodes), Bike (15,809 nodes), and Drive (13,637 nodes). Applied OSM road-class safety filter removing <b>267 motorway/trunk edges plus 170 high-speed or wide primary edges</b> (lanes >= 3 or maxspeed >= 50); missing tags are not filtered (139 primary edges with neither tag, 71 primary links, and 902 secondary edges are untouched).",
        "<b>Steps S6–S9 (Grid, Multi-Source Dijkstra & Catchments):</b> Implemented <code>src/travel_times.py</code>. Generated 680 H3 resolution 9 hexagons, extracted zonal population from the clipped WorldPop raster, and computed exact door-to-station shortest times incorporating station snap distances across Walk, Safe E-Bike, and E-Auto networks.",
        "<b>Steps S12–S14 (Feeder Hub Optimizer):</b> Implemented <code>src/optimizer.py</code>. Thinned road nodes into 881 candidate hubs (120m spacing), computed 177 sparse coverage pairs at T = 15 min (69 coverable cells) and 409 pairs at T = 20 min (92 unserved cells strictly walk > 20 min) within 5-min walking radius, and solved greedy max-coverage for <i>k</i> = 1 to 15.",
        "<b>Step S16 (Station Prioritization Ranking):</b> Ranked stations by unserved walking population weighted by August 2025 ridership.",
        "<b>Step S18 (Interactive Streamlit App):</b> Implemented <code>app/main.py</code> serving 6 dedicated screens reading only cached files."
    ]
    for b in arch_bullets:
        story.append(Paragraph(f"• {b}", s["bullet"]))
    story.append(Spacer(1, 10))

    # Section 4: Numerical Results & Station Ranking
    story.append(Paragraph("4. Benchmark Results: Core 10-Station Metro Corridor (T = 15 min vs. T = 20 min Co-Headlines)", s["h1"]))

    results_table_data = [
        [Paragraph("Access Mode / Component", s["th"]), Paragraph("Assumed Speed", s["th"]), Paragraph("Overhead", s["th"]), Paragraph("T = 15 min Core Corridor Pop (%)", s["th"]), Paragraph("T = 20 min Core Corridor Pop (%) [STAMP p. 2]", s["th"])],
        [Paragraph("1. Pedestrian Walk Catchment", s["td"]), Paragraph("4.5 km/h", s["td"]), Paragraph("0 min", s["td"]), Paragraph("<b>66,417 (14.6%)</b>", s["td"]), Paragraph("<b>105,450 (23.2%)</b>", s["td"])],
        [Paragraph("2. Road-Filtered E-Bike Uplift (Doorstep Range)", s["td"]), Paragraph("13.5 km/h", s["td"]), Paragraph("5 min", s["td"]), Paragraph("+69,215 (+15.3%)<br/>[+43.6k to +90.9k]", s["td"]), Paragraph("+141,578 (+31.2%)<br/>[+100.2k to +175.8k]", s["td"])],
        [Paragraph("<i>Total Walk + E-Bike (Doorstep)</i>", s["td"]), Paragraph("-", s["td"]), Paragraph("-", s["td"]), Paragraph("<b>135,632 (29.9%)</b><br/>[24.2% to 34.7%]", s["td"]), Paragraph("<b>247,029 (54.5%)</b><br/>[45.3% to 62.0%]", s["td"])],
        [Paragraph("3. E-Auto Extra Reach (Unfiltered Drive Upper Bound)", s["td"]), Paragraph("18.0 km/h", s["td"]), Paragraph("5 min", s["td"]), Paragraph("+77,509 (+17.1%)", s["td"]), Paragraph("+129,944 (+28.6%)", s["td"])],
        [Paragraph("<b>Total Multi-Modal Union Access</b>", s["td"]), Paragraph("Multi-modal", s["td"]), Paragraph("-", s["td"]), Paragraph("<b>213,140 (47.0%)</b>", s["td"]), Paragraph("<b>376,973 (83.1%)</b>", s["td"])],
        [Paragraph("Residual Unserved Corridor Gap", s["td"]), Paragraph("-", s["td"]), Paragraph("-", s["td"]), Paragraph("240,547 (53.0%)", s["td"]), Paragraph("76,715 (16.9%)", s["td"])],
        [Paragraph("Physical 5-Hub Feeder Reality", s["td"]), Paragraph("13.5 km/h", s["td"]), Paragraph("5 min", s["td"]), Paragraph("+10,616 (+2.3%)", s["td"]), Paragraph("+17,036 (+3.8%)", s["td"])],
    ]
    t_res = Table(results_table_data, colWidths=[140, 65, 45, 120, 120])
    t_res.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>Boundary Cordon Absorption & Feeder Hub Dynamics:</b><br/>"
        "• <i>Territory Definition:</i> Cells are partitioned based on nearest station by pedestrian walking travel time. Western boundary context stations (Singayyanapalya & Krishnarajapura) absorb 108,348 residents (19.3% of the 562k buffer), leaving 453,687 residents in the core 10-station corridor.<br/>"
        "• <i>Western Reassignment Audit:</i> 100% of the 108 absorbed cells are geometrically verified between 248 m and 726 m closer to context stations than pilot stations (see docs/western_reassignment_map.png).<br/>"
        "• <i>Whitefield Railway Footbridge & Dismount Rule:</i> 10 out of the 11 corridor gap cells (9,640 residents / 93.9%) are clustered north of Whitefield Kadugodi station across the railway main line. Pedestrians cross the footbridge stairs in 811 m (10.8 min). Bicycles cannot ride over stairs and face a 4.02 km road detour (22.9 min). Our route-by-route audit under a Dismount-and-Push rule at 4.0 km/h reveals that <b>only 3 cells (2,521 residents / 26.1%)</b> are absorbed within 20 min; the remaining 7 cells (7,119 residents) exceed the 20-min budget (24.8–29.2 min) because their walk trip is already 15.8–19.7 min. We retain <b>Ride-Only as our primary baseline</b> and exclude speculative assertions on bike weights or platform regulations.<br/>"
        "• <i>Snapping Distance Distribution Audit:</i> Mean bike snap distance is 86.5 m (median 60.1 m, 90% 196.9 m, max 481.5 m < 500 m cap). The valid-subgraph fix (out_degree > 0) shifted mean snap distance by only 0.07 m (86.47 m → 86.54 m) and moved 0 cells across barriers. The +5,812 resident increase resulted 100% from unblocking Pattandur Agrahara from an isolated stub.<br/>"
        "• <i>Overhead Sensitivity Grid (3, 5, 7 min):</i> Moving vehicle overhead from 3 min to 7 min causes a <b>3.5x drop in T = 15 min e-bike uplift</b> (+109,225 / +24.1% down to +31,626 / +7.0%), proving that vehicle access overhead is just as decisive as travel speed (see data/output/overhead_sensitivity_matrix.csv).",
        s["callout"]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Station Prioritization: Unserved Need-Only vs. Ridership-Weighted:</b><br/>"
        "<i>Formula: Priority Score = Walk Uncovered Need × (Avg Daily Boardings ÷ Corridor Mean of 7,816.6). "
        "Boardings represent BMRCL RTI AFC turnstile entries across 18 operational days in August 2025.</i>",
        s["h2"]
    ))
    rank_rows = [
        [Paragraph("Station Name", s["th"]), Paragraph("Unserved Need", s["th"]), Paragraph("Need Rank", s["th"]), Paragraph("Daily Boardings", s["th"]), Paragraph("Priority Score", s["th"]), Paragraph("Weighted Rank", s["th"])],
        [Paragraph("Seetharampalya", s["td"]), Paragraph("79,312.5", s["td"]), Paragraph("<b>#1</b>", s["td"]), Paragraph("8,365", s["td"]), Paragraph("84,878.2", s["td"]), Paragraph("<b>#1</b>", s["td"])],
        [Paragraph("Whitefield (Kadugodi)", s["td"]), Paragraph("73,253.3", s["td"]), Paragraph("<b>#3</b>", s["td"]), Paragraph("8,464", s["td"]), Paragraph("79,321.6", s["td"]), Paragraph("<b>#2</b>", s["td"])],
        [Paragraph("Hoodi", s["td"]), Paragraph("58,045.5", s["td"]), Paragraph("<b>#4</b>", s["td"]), Paragraph("6,970", s["td"]), Paragraph("51,759.5", s["td"]), Paragraph("<b>#3</b>", s["td"])],
        [Paragraph("Pattandur Agrahara", s["td"]), Paragraph("30,654.2", s["td"]), Paragraph("<b>#5</b>", s["td"]), Paragraph("10,028", s["td"]), Paragraph("39,327.2", s["td"]), Paragraph("<b>#4</b>", s["td"])],
        [Paragraph("Kadugodi Tree Park", s["td"]), Paragraph("20,710.6", s["td"]), Paragraph("<b>#7</b>", s["td"]), Paragraph("11,647", s["td"]), Paragraph("30,860.0", s["td"]), Paragraph("<b>#5</b>", s["td"])],
        [Paragraph("Nallurahalli", s["td"]), Paragraph("26,130.7", s["td"]), Paragraph("<b>#6</b>", s["td"]), Paragraph("7,659", s["td"]), Paragraph("25,604.2", s["td"]), Paragraph("<b>#6</b>", s["td"])],
        [Paragraph("Hopefarm Channasandra", s["td"]), Paragraph("73,820.6", s["td"]), Paragraph("<b>#2</b>", s["td"]), Paragraph("2,536", s["td"]), Paragraph("23,950.5", s["td"]), Paragraph("<b>#7</b>", s["td"])],
        [Paragraph("Garudacharpalya", s["td"]), Paragraph("21,305.5", s["td"]), Paragraph("<b>#8</b>", s["td"]), Paragraph("7,176", s["td"]), Paragraph("19,559.7", s["td"]), Paragraph("<b>#8</b>", s["td"])],
        [Paragraph("Sathya Sai Hospital", s["td"]), Paragraph("2,156.5", s["td"]), Paragraph("<b>#9</b>", s["td"]), Paragraph("7,678", s["td"]), Paragraph("2,118.3", s["td"]), Paragraph("<b>#9</b>", s["td"])],
        [Paragraph("Kundalahalli", s["td"]), Paragraph("1,881.2", s["td"]), Paragraph("<b>#10</b>", s["td"]), Paragraph("7,643", s["td"]), Paragraph("1,839.4", s["td"]), Paragraph("<b>#10</b>", s["td"])],
    ]
    t_rank = Table(rank_rows, colWidths=[120, 80, 55, 75, 80, 80])
    t_rank.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_rank)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>Spatial Dynamics & Sensitivity Insights:</i><br/>"
        "• <b>Hopefarm Policy Divergence:</b> Hopefarm ranks #2 in pure Unserved Need (73.8k residents) but drops to #7 under ridership weighting due to low current boardings (2,536/day). Low ridership <b>may reflect</b> poor last-mile access (an untested hypothesis), but could alternatively indicate commercial zoning or settlement patterns. Presenting both rankings allows agencies to choose between unlocking suppressed demand or maximizing asset utilization.<br/>"
        "• <b>Home-End vs. Work-End Framing:</b> The model explicitly evaluates home-end residential access from WorldPop settlement data. Tech park stations (ITPL / Pattandur Agrahara) serve workplace destination commuters, which will be integrated in future work.<br/>"
        "• <b>Speed Sensitivity Matrix (Walk 4.0–5.0 km/h × E-Bike 12.0–15.0 km/h):</b> At T = 15 min, walk coverage spans 13.0% to 17.8%; e-bike uplift spans +7.8% to +21.2% (+9.6% to +20.0% at baseline walk; total walk + e-bike reach: 24.2% to 34.7%). At T = 20 min, walk spans 20.2% to 26.3%; e-bike uplift spans +19.9% to +41.6% (+22.1% to +38.7% at baseline walk; total walk + e-bike reach: 45.3% to 62.0%). Full grid exported in data/output/speed_sensitivity_matrix.csv.<br/>"
        "• <b>Physical Severance Validation:</b> 23 cells have detour ratios > 3.0x due to railway tracks and gated compounds.",
        s["body"]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Greedy Feeder Hub Placement ($k = 1$ to 5, T = 15 min):</b>", s["h2"]))
    story.append(Paragraph(
        "• <b>k = 1:</b> Hub SITE_0193 yields +3,106.6 marginal unserved residents (Total: 69,523.4)<br/>"
        "• <b>k = 2:</b> Hub SITE_0049 yields +2,156.5 marginal residents (Total: 71,679.9)<br/>"
        "• <b>k = 3:</b> Hub SITE_0021 yields +1,860.9 marginal residents (Total: 73,540.8)<br/>"
        "• <b>k = 4:</b> Hub SITE_0140 yields +1,768.1 marginal residents (Total: 75,308.9)<br/>"
        "• <b>k = 5:</b> Hub SITE_0555 yields +1,723.8 marginal residents (Total: 77,032.7)<br/>"
        "<i>Diminishing returns verified: marginal gain drops strictly monotonically (3,107 → 2,157 → 1,861 → 1,768 → 1,724). Total 5-hub uplift = +10,615.9 unserved residents reached (+2.3%). At T = 20 min, 5 hubs yield +17,035.9 (+3.8%). Hub sites 1 to 4 match previous coordinates at 0.0 m distance; site 5 moved to Pattandur Agrahara following station unblocking (+190 gain lift).</i>",
        s["body"]
    ))
    story.append(Spacer(1, 8))

    # Section 5: Verification & Tests
    story.append(Paragraph("5. Quality Assurance & Test Verification", s["h1"]))
    story.append(Paragraph(
        "Automated unit testing suite (<code>pytest tests/</code>) achieves <b>100% pass rate across 15 unit tests</b>:<br/>"
        "• <code>test_config.py</code> (2 tests): Configuration schema, types, CRS string, missing file handling.<br/>"
        "• <code>test_stations.py</code> (2 tests): Station coordinate ranges, ridership joins, table schema contract.<br/>"
        "• <code>test_travel_times.py</code> (6 tests): Output existence, mutual exclusivity of uplifts, combined union consistency, total population conservation (562,035 exact), reachability snapping integrity, and snap distance integrity.<br/>"
        "• <code>test_optimizer.py</code> (5 tests): Output existence, greedy diminishing returns monotonicity, station ranking consistency, context exclusion from ranking, and coverage pair corridor isolation.",
        s["body"]
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated {output_path}")


# ==============================================================================
# REPORT 2: FORWARD PLAN & NEXT STEPS
# ==============================================================================
def generate_report_2(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    s = build_styles()
    story = []

    # Title Banner
    story.append(Paragraph("Metro Feeder Zone Screening Tool", s["doc_title"]))
    story.append(Paragraph("<b>Report 2: Strategic Roadmap, Next Build Steps & Pitch Execution</b><br/>SHIFT 2026 | Preliminary, Whitefield 10-Station Corridor (Git commit: <code>b390e44</code>)", s["doc_subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=10))

    # Hackathon Schedule & Checkpoints
    story.append(Paragraph("1. Hackathon 24-Hour Timeline & Milestones", s["h1"]))
    story.append(Paragraph(
        "The hackathon officially starts Saturday at 14:00 (brief arrives) and freezes Sunday at 13:00 (pitches at 14:30). "
        "Because our core engine is already built, our timeline focuses on high-impact analytical differentiators, mentor defense, and pitch rehearsal:",
        s["body"]
    ))

    sched_rows = [
        [Paragraph("Time Slot", s["th"]), Paragraph("Official Milestone", s["th"]), Paragraph("Our Team's Action Plan & Verification Target", s["th"])],
        [Paragraph("Sat 14:00 - 14:45", s["td"]), Paragraph("Brief Arrives", s["td"]), Paragraph("Read brief together. Confirm if it is a dataset pack or problem framing. Apply Swap Plan if needed.", s["td"])],
        [Paragraph("Sat 14:45 - 17:30", s["td"]), Paragraph("Build Slot 1 (Gate A)", s["td"]), Paragraph("Verify 10-station baseline map. Re-confirm walk-only catchments. Gate A passed ahead of time.", s["td"])],
        [Paragraph("Sat 17:30 - 18:00", s["td"]), Paragraph("Mentor Review 1", s["td"]), Paragraph("2-minute pitch of problem and assumptions. Ask mentors which assumptions a transport planner would challenge.", s["td"])],
        [Paragraph("Sat 18:00 - 20:00", s["td"]), Paragraph("Build Slot 2 (Gate B)", s["td"]), Paragraph("Execute Step S11 (Safety impact analysis) and Step S15 (PuLP exact optimizer comparison).", s["td"])],
        [Paragraph("Sat 20:00 - 20:30", s["td"]), Paragraph("Check-in 1 (Judges)", s["td"]), Paragraph("Present: WRI evidence (1 min), interactive access map, uplift range, and plan for overnight build.", s["td"])],
        [Paragraph("Sat 20:30 - 01:30", s["td"]), Paragraph("Night Build (Gate C)", s["td"]), Paragraph("Package single-command CLI. Build reproducibility manifest. Sleep rotation (1 builder awake).", s["td"])],
        [Paragraph("Sun 08:00 - 08:30", s["td"]), Paragraph("Check-in 2 (Judges)", s["td"]), Paragraph("Demo live greedy optimizer, diminishing returns curve, and safety filter toggle.", s["td"])],
        [Paragraph("Sun 08:30 - 11:00", s["td"]), Paragraph("Polish & Scale Test", s["td"]), Paragraph("Scale run to all 63 stations (if laptop allows). Polish Streamlit UI visuals and tooltips.", s["td"])],
        [Paragraph("Sun 11:00 - 12:00", s["td"]), Paragraph("Mentor Rehearsal", s["td"]), Paragraph("Full 5-minute dry-run pitch. Collect toughest questions from mentors on ML, safety, and adoption.", s["td"])],
        [Paragraph("Sun 12:00", s["td"]), Paragraph("Check-in 3 (Judges)", s["td"]), Paragraph("Final end-to-end demo and transparent presentation of model limitations.", s["td"])],
        [Paragraph("Sun 12:00 - 13:00", s["td"]), Paragraph("Feature Freeze", s["td"]), Paragraph("ZERO code changes. Record 2-minute backup demo video. Finalize 5-minute slide deck.", s["td"])],
        [Paragraph("Sun 14:00 - 14:30", s["td"]), Paragraph("Final Pitches", s["td"]), Paragraph("Deliver 5-minute pitch + 3-minute Q&A with live demo and video backup ready.", s["td"])],
    ]
    t_sched = Table(sched_rows, colWidths=[90, 100, 297])
    t_sched.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_sched)
    story.append(Spacer(1, 10))

    # Immediate Technical Steps
    story.append(Paragraph("2. Immediate High-Impact Steps to Build", s["h1"]))

    story.append(Paragraph("<b>Step 1: Unfiltered vs. Safe E-Bike Analysis (Step S11 — The Road Fix Narrative)</b>", s["h2"]))
    story.append(Paragraph(
        "Run multi-source Dijkstra on the unfiltered bike graph (<code>graph_bike_unfiltered.graphml</code>) and measure how many residents "
        "fall into the 15-minute catchment when high-speed roads are used versus when they are excluded by our safety filter. "
        "<b>Why this wins points:</b> It proves that micromobility adoption is blocked by hostile road infrastructure, creating a direct policy recommendation for BMRCL/BBMP to install protected bike corridors.",
        s["body"]
    ))

    story.append(Paragraph("<b>Step 2: Exact Mathematical Optimum Check (Step S15 — PuLP Integer Linear Program)</b>", s["h2"]))
    story.append(Paragraph(
        "Formulate the Maximal Covering Location Problem (MCLP) as a binary integer program using <code>pulp</code>: "
        "<br/>• Objective: $\\max \\sum_{i} \\text{pop}_i \\cdot y_i$ subject to $\\sum_j x_j \\le k$ and $y_i \\le \\sum_{j \\in N(i)} x_j$. "
        "<br/>Compare the exact MIP solution against our greedy heuristic for $k = 3, 5, 10$. "
        "<b>Why this wins points:</b> Proves that the greedy approximation achieves $\\ge 98\\%$ of mathematical optimality in $<0.1\\text{ s}$, directly answering judges' technical optimization questions.",
        s["body"]
    ))

    story.append(Paragraph("<b>Step 3: Single-Command Pipeline Orchestrator (<code>src/pipeline.py</code>)</b>", s["h2"]))
    story.append(Paragraph(
        "Create an automated CLI runner that executes the pipeline end-to-end in one command:<br/>"
        "<code>python -m src.pipeline --mode pilot</code> (runs the 10-station Whitefield corridor)<br/>"
        "<code>python -m src.pipeline --mode all</code> (runs all 63 Bengaluru stations)",
        s["body"]
    ))

    story.append(Paragraph("<b>Step 4: Reproducibility Manifest (<code>data/output/manifest.json</code>)</b>", s["h2"]))
    story.append(Paragraph(
        "Export SHA-256 hashes of all input files, configuration parameters, execution timestamps, and pinned library versions. "
        "Ensures total scientific reproducibility required by Section 8 of the competition specification.",
        s["body"]
    ))
    story.append(Spacer(1, 10))

    # Pivot / Swap Playbook
    story.append(Paragraph("3. Pivot & Swap Playbook for the 14:00 Brief", s["h1"]))
    story.append(Paragraph(
        "When the official brief arrives at 14:00 Saturday, evaluate which emphasis applies and pivot seamlessly using our modular engine:",
        s["body"]
    ))

    swap_rows = [
        [Paragraph("Brief Emphasis", s["th"]), Paragraph("Our Planned Adjustment", s["th"]), Paragraph("Core Modules Kept Intact", s["th"])],
        [Paragraph("Charging & Swapping", s["td"]), Paragraph("Promote Tier 3 Hubs: select charging/swap depots among the k feeder zones using a p-median repositioning distance rule.", s["td"]), Paragraph("Networks, grid, population, travel times, optimizer.", s["td"])],
        [Paragraph("Fleet Operations & Rebalancing", s["td"]), Paragraph("Reframe feeder zones as parking and rebalancing hubs; add vehicle repositioning distance metric.", s["td"]), Paragraph("Same multi-modal routing engine.", s["td"])],
        [Paragraph("Rider Safety & Crashes", s["td"]), Paragraph("Highlight Step S11 safety filter and aggregate segment risk to BTP police jurisdictions (D7 & D8).", s["td"]), Paragraph("All modules.", s["td"])],
        [Paragraph("Supplied Dataset Pack", s["td"]), Paragraph("Drop supplied CSV/GeoJSON into data/raw/ and substitute or benchmark against our open datasets.", s["td"]), Paragraph("Methodology and optimization algorithm.", s["td"])],
        [Paragraph("Different City / Corridor", s["td"]), Paragraph("Change config/params.yaml; fetch OSM networks for new polygon and run pipeline CLI.", s["td"]), Paragraph("100% of pipeline code.", s["td"])],
    ]
    t_swap = Table(swap_rows, colWidths=[110, 210, 167])
    t_swap.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_swap)
    story.append(Spacer(1, 10))

    # Pitch Strategy
    story.append(Paragraph("4. Five-Minute Pitch Strategy & Judging Alignment", s["h1"]))
    story.append(Paragraph("Judges allocate 100 points: Problem (25), Solution (25), Practicality (20), Progress (15), Presentation (15).", s["body"]))

    story.append(Paragraph("<b>5-Minute Rehearsed Pitch Script Breakdown:</b>", s["h2"]))
    pitch_bullets = [
        "<b>0:00 - 0:30 (Problem & Deciders):</b> BMRCL, BMTC, and shared-EV operators need to know where the next <i>k</i> electric feeder zones go and which stations need them first to maximize ridership without unsafe road exposure.",
        "<b>0:30 - 1:15 (Published Evidence):</b> WRI & TMF STAMP paper (Page 2) surveyed 7,200 commuters across Bengaluru, Delhi, and Nagpur: walking and shared modes account for over 75% of station access, and commuters are willing to travel up to 20 minutes to access metro stations.",
        "<b>1:15 - 2:00 (Engineering Method):</b> Three OSM networks (pedestrian at 4.5 km/h, road-class filtered bike at 13.5 km/h + 5 min overhead, drive at 18 km/h) mapped over 680 H3 res-9 hexagons across 74 sq km (562k WorldPop residents), solved with multi-source Dijkstra.",
        "<b>2:00 - 3:30 (Corridor Results & Hierarchy):</b> Show T = 15 min vs T = 20 min (WRI STAMP p. 2 benchmark). In the 10-station core corridor (453,687 residents, partitioned by walk catchment after Singayyanapalya & KR Puram absorb 108k): walking reaches 14.6% (66,417). Lead with road-filtered e-bike doorstep range: +9.6% to +20.0% (+43.6k to +90.9k, baseline +69,215 / +15.3%), reaching 29.9% (135,632). For physical infrastructure, placing 5 hubs adds +10,616 (+2.3%) at T = 15 min and +17,036 (+3.8%) at T = 20 min. E-auto is explicitly labeled as an unfiltered drive upper bound (+17.1% / +77,509 at T = 15). Station priority ranks Seetharampalya #1 (Score 84,878, 79.3k unserved need), Whitefield #2, and Hoodi #3.",
        "<b>3:30 - 4:15 (Limits & Boundary Defense):</b> Pure screening tool, not adoption forecasting. Detail boundary load absorption (Singayyanapalya & KR Puram prevent western edge inflation). Explain why Kundalahalli (1.8k) is pinched on 3 sides within 1 km, while Hoodi (58.0k) faces an unserved northern hinterland. Defend walk catchment geometry: max 875m straight-line, 1.92 detour ratio, and 3 external Google Maps spot-checks matching within 1 min.",
        "<b>4:15 - 5:00 (Next Steps):</b> Scale verified pipeline from 10-station pilot to all 83 operational stations, evaluate T = 10, 15, and 20 min sensitivity, and prepare for official hackathon brief integration."
    ]
    for pb in pitch_bullets:
        story.append(Paragraph(f"• {pb}", s["bullet"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Answers to Tough Judge Questions:</b>", s["h2"]))
    story.append(Paragraph(
        "• <i>'Is this just an isochrone map?'</i> → No. An isochrone is purely descriptive. Our decision engine goes beyond it: a greedy max-coverage optimizer that chooses <i>k</i> sites without double-counting, ranks stations, and measures infrastructure safety penalties.<br/>"
        "• <i>'Why not use Machine Learning?'</i> → There is no open point-level crash dataset to train on, and hub siting is a spatial combinatorial optimization problem. An explainable mathematical optimizer is legally and operationally defensible for public agencies.<br/>"
        "• <i>'Does this prove people will switch to e-bikes?'</i> → No. It is a physical accessibility screening tool showing who falls within 15 minutes under stated speeds. We explicitly do not forecast mode choice adoption.",
        s["body"]
    ))
    story.append(Spacer(1, 8))

    # Actionable Verification Checklist
    story.append(Paragraph("5. Team Pre-Brief Verification Checklist", s["h1"]))
    checks = [
        "[X] All 8 raw datasets acquired, opened, verified, and logged in doc/data_log.md.",
        "[X] Core pipeline verified for 10-station corridor with 15 unit tests passing.",
        "[X] Streamlit web dashboard ready with 6 interactive screens.",
        "[ ] Inspect QGIS layers (stations_selected.gpkg, cells.gpkg) on your laptop.",
        "[ ] Rehearse 5-minute pitch roles: Builder 1 (Method & Algorithm), Builder 2 (Data Pipeline & Live Demo).",
        "[ ] Test laptop battery, chargers, and mobile hotspot backup before 14:00 Saturday."
    ]
    for c in checks:
        story.append(Paragraph(c, s["bullet"]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated {output_path}")


if __name__ == "__main__":
    import shutil
    out_dir = Path("docs")
    out_dir.mkdir(parents=True, exist_ok=True)
    r1_path = out_dir / "PROJECT_WORK_COMPLETED_REPORT.pdf"
    r2_path = out_dir / "FORWARD_PLAN_AND_NEXT_STEPS.pdf"
    generate_report_1(r1_path)
    generate_report_2(r2_path)
    
    # Keep doc/ directory synchronized if present
    doc_dir = Path("doc")
    if doc_dir.exists():
        shutil.copy(r1_path, doc_dir / "PROJECT_WORK_COMPLETED_REPORT.pdf")
        shutil.copy(r2_path, doc_dir / "FORWARD_PLAN_AND_NEXT_STEPS.pdf")
        print(f"Synchronized PDF reports to {doc_dir}/")
