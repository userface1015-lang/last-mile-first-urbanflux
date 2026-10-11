<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
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
