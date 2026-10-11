import geopandas as gpd
import osmnx as ox
import networkx as nx
import pandas as pd

cells = gpd.read_file('data/output/cells.gpkg')
G_bike = ox.load_graphml('data/interim/graph_bike_safe.graphml')
for _, _, _, d in G_bike.edges(keys=True, data=True):
    d['time_min'] = float(d['time_min'])
G_rev = G_bike.reverse(copy=True)

diff_cells = cells[(cells['walk_time_min'] <= 20) & (cells['ebike_time_min'] > 20)].copy()
print(f"Total cells with walk <= 20 and ebike > 20: {len(diff_cells)}")
print(f"Total pop: {diff_cells['population'].sum():.1f}")

st_pilot = gpd.read_file('data/interim/stations_selected.gpkg')

for idx, row in diff_cells.iterrows():
    cid = row['cell_id']
    pop = row['population']
    w_t = row['walk_time_min']
    b_t = row['ebike_time_min']
    st_w = row['nearest_station_walk']
    st_b = row['nearest_station_ebike']
    nb = int(row['node_bike'])
    nw = int(row['node_walk'])
    
    in_deg = G_bike.in_degree(nb) if nb in G_bike else -1
    out_deg = G_bike.out_degree(nb) if nb in G_bike else -1
    
    print(f"Cell {cid}: pop={pop:5.1f}, walk={w_t:5.2f}m (st={st_w}), ebike={b_t} (st={st_b}), nb={nb} (in={in_deg}, out={out_deg})")
