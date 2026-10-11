"""
generate_qgis_styles.py - Generates QGIS 3 QML style files matching the GeoPackages
so QGIS automatically applies colorblind-safe styling when layers are dragged in.
"""

from pathlib import Path

def get_polygon_qml(color_hex: str, border_hex: str, opacity: float = 0.7, outline_width: float = 0.6, fill_style: str = "solid") -> str:
    # Convert hex to rgb
    r = int(color_hex[1:3], 16)
    g = int(color_hex[3:5], 16)
    b = int(color_hex[5:7], 16)
    alpha = int(opacity * 255)

    br = int(border_hex[1:3], 16)
    bg = int(border_hex[3:5], 16)
    bb = int(border_hex[5:7], 16)

    fill_line = f'<prop k="color" v="{r},{g},{b},{alpha}"/>'
    if fill_style == "no":
        fill_line = '<prop k="style" v="no"/>'

    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology" version="3.28.0">
  <renderer-v2 type="singleSymbol" symbollevels="0">
    <symbols>
      <symbol type="fill" name="0" alpha="1.0" clip_to_extent="1">
        <layer class="SimpleFill" locked="0" enabled="1">
          {fill_line}
          <prop k="outline_color" v="{br},{bg},{bb},255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="{outline_width}"/>
          <prop k="outline_width_unit" v="MM"/>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
</qgis>
"""

def get_station_qml() -> str:
    return """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" version="3.28.0">
  <renderer-v2 type="categorizedSymbol" attr="station_type" symbollevels="0">
    <categories>
      <category symbol="0" value="Pilot Station (Core)" label="Pilot Station (10 Stations)"/>
      <category symbol="1" value="Context Station (Boundary Absorber)" label="Context Station (2 Stations)"/>
    </categories>
    <symbols>
      <symbol type="marker" name="0" alpha="1.0" clip_to_extent="1">
        <layer class="SimpleMarker" locked="0" enabled="1">
          <prop k="color" v="217,4,41,255"/>
          <prop k="name" v="circle"/>
          <prop k="size" v="4.5"/>
          <prop k="size_unit" v="MM"/>
          <prop k="outline_color" v="255,255,255,255"/>
          <prop k="outline_width" v="0.8"/>
        </layer>
      </symbol>
      <symbol type="marker" name="1" alpha="1.0" clip_to_extent="1">
        <layer class="SimpleMarker" locked="0" enabled="1">
          <prop k="color" v="255,183,3,255"/>
          <prop k="name" v="triangle"/>
          <prop k="size" v="4.5"/>
          <prop k="size_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_width" v="0.8"/>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fontWordSpacing="0" textColor="0,0,0,255" fontSize="9" fontLetterSpacing="0" namedStyle="Bold" fontWeight="75" fontFamily="Arial">
        <text-buffer bufferSize="1.2" bufferColor="255,255,255,255" bufferDraw="1"/>
      </text-style>
      <rule key="name">
        <expression>"name"</expression>
      </rule>
    </settings>
  </labeling>
</qgis>
"""

def main():
    qgis_dir = Path("data/output/qgis_layers")
    
    # 1. Walk Catchment (15 min) -> Teal
    (qgis_dir / "walk_catchment_15min.qml").write_text(get_polygon_qml("#2A9D8F", "#1B4D3E", opacity=0.7), encoding="utf-8")
    
    # 2. E-Bike Catchment (15 min) -> Blue
    (qgis_dir / "ebike_catchment_15min.qml").write_text(get_polygon_qml("#457B9D", "#1D3557", opacity=0.7), encoding="utf-8")
    
    # 3. E-Bike Uplift (15 min) -> Coral/Amber
    (qgis_dir / "ebike_uplift_15min.qml").write_text(get_polygon_qml("#E76F51", "#C44536", opacity=0.75), encoding="utf-8")
    
    # 4. Combined Active (15 min) -> Deep Cyan
    (qgis_dir / "combined_active_15min.qml").write_text(get_polygon_qml("#1D3557", "#0D1B2A", opacity=0.65), encoding="utf-8")
    
    # 5. Unserved Gap (15 min) -> Soft Grey
    (qgis_dir / "unserved_gap_15min.qml").write_text(get_polygon_qml("#E0E0E0", "#9E9E9E", opacity=0.35), encoding="utf-8")

    # 6. Walk Boundary Outline (15 min) -> Thick Teal Outline, Hollow
    (qgis_dir / "walk_boundary_15min.qml").write_text(get_polygon_qml("#2A9D8F", "#1B4D3E", opacity=0.0, outline_width=1.0, fill_style="no"), encoding="utf-8")

    # 7. E-Bike Boundary Outline (15 min) -> Thick Blue Outline, Hollow
    (qgis_dir / "ebike_boundary_15min.qml").write_text(get_polygon_qml("#457B9D", "#1D3557", opacity=0.0, outline_width=1.0, fill_style="no"), encoding="utf-8")

    # 8. T = 20 min Catchments
    (qgis_dir / "walk_catchment_20min.qml").write_text(get_polygon_qml("#52B788", "#2D6A4F", opacity=0.65), encoding="utf-8")
    (qgis_dir / "ebike_catchment_20min.qml").write_text(get_polygon_qml("#7209B7", "#3A0CA3", opacity=0.65), encoding="utf-8")
    (qgis_dir / "ebike_uplift_20min.qml").write_text(get_polygon_qml("#F72585", "#B5179E", opacity=0.7), encoding="utf-8")
    (qgis_dir / "combined_active_20min.qml").write_text(get_polygon_qml("#4361EE", "#3F37C9", opacity=0.65), encoding="utf-8")

    # 9. Metro Stations -> Custom categorized symbols + bold labels with halo
    (qgis_dir / "metro_stations.qml").write_text(get_station_qml(), encoding="utf-8")
    
    print(f"Generated QGIS QML style files in {qgis_dir.resolve()}!")

if __name__ == "__main__":
    main()
