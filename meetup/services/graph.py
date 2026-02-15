"""
London tube/rail network graph service.

Builds a NetworkX weighted graph from static CSV data files.
Stations are nodes, connections are edges weighted by travel time in minutes.
Transfer edges connect different lines at interchange stations.

The graph is loaded once and cached in memory. It's small (~400 nodes, ~500 edges)
so this is essentially free.
"""
import csv
import os
import networkx as nx
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

# Module-level cache
_graph = None
_stations = None
_station_lookup = None


def _load_stations():
    """Load station data from CSV. Returns dict of station_id -> station info."""
    stations = {}
    csv_path = DATA_DIR / 'stations.csv'
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            station_id = int(row['station_id'])
            stations[station_id] = {
                'id': station_id,
                'name': row['name'],
                'lat': float(row['latitude']),
                'lon': float(row['longitude']),
                'zone': row['zone'],
            }
    return stations


def _load_connections():
    """Load connection data from CSV. Returns list of connection dicts."""
    connections = []
    csv_path = DATA_DIR / 'connections.csv'
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            connections.append({
                'station1_id': int(row['station1_id']),
                'station2_id': int(row['station2_id']),
                'line': row['line'],
                'time_minutes': float(row['time_minutes']),
            })
    return connections


def _load_interchanges():
    """Load interchange/transfer data from CSV. Returns list of transfer dicts."""
    interchanges = []
    csv_path = DATA_DIR / 'interchanges.csv'
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            interchanges.append({
                'station_name': row['station_name'],
                'from_line': row['from_line'],
                'to_line': row['to_line'],
                'transfer_time_minutes': float(row['transfer_time_minutes']),
            })
    return interchanges


def _build_graph(stations, connections, interchanges):
    """
    Build a NetworkX graph from station, connection, and interchange data.

    The graph uses composite node IDs of the form "station_id:line" to model
    the fact that being at a station on one line is different from being at
    the same station on another line (you need to transfer).

    Each station also gets a "hub" node (just "station_id") connected to all
    its line-specific nodes with transfer-time edges.
    """
    G = nx.Graph()

    # Track which lines serve each station
    station_lines = {}  # station_id -> set of line names

    for conn in connections:
        s1 = conn['station1_id']
        s2 = conn['station2_id']
        line = conn['line']
        time = conn['time_minutes']

        station_lines.setdefault(s1, set()).add(line)
        station_lines.setdefault(s2, set()).add(line)

        # Create line-specific node IDs
        node1 = f"{s1}:{line}"
        node2 = f"{s2}:{line}"

        if s1 in stations:
            G.add_node(node1, station_id=s1, line=line,
                       name=stations[s1]['name'],
                       lat=stations[s1]['lat'],
                       lon=stations[s1]['lon'])
        if s2 in stations:
            G.add_node(node2, station_id=s2, line=line,
                       name=stations[s2]['name'],
                       lat=stations[s2]['lat'],
                       lon=stations[s2]['lon'])

        G.add_edge(node1, node2, weight=time, line=line, edge_type='connection')

    # Build interchange name -> station_id lookup
    name_to_id = {}
    for sid, info in stations.items():
        name_to_id[info['name'].lower()] = sid

    # Add hub nodes and transfer edges
    # For each station served by multiple lines, create a hub node
    # and connect each line-specific node to the hub
    interchange_times = {}
    for ic in interchanges:
        key = (ic['station_name'].lower(), ic['from_line'], ic['to_line'])
        interchange_times[key] = ic['transfer_time_minutes']
        # Also store reverse
        key_rev = (ic['station_name'].lower(), ic['to_line'], ic['from_line'])
        interchange_times[key_rev] = ic['transfer_time_minutes']

    for station_id, lines in station_lines.items():
        if station_id not in stations:
            continue
        station_info = stations[station_id]
        station_name_lower = station_info['name'].lower()

        # Create hub node for this station
        hub_node = str(station_id)
        G.add_node(hub_node, station_id=station_id, line='hub',
                    name=station_info['name'],
                    lat=station_info['lat'],
                    lon=station_info['lon'],
                    is_hub=True)

        if len(lines) == 1:
            # Single line station - connect directly to hub with 0 weight
            line = next(iter(lines))
            line_node = f"{station_id}:{line}"
            G.add_edge(hub_node, line_node, weight=0, line='transfer',
                       edge_type='hub_link')
        else:
            # Multi-line station - connect each line node to hub with transfer time
            lines_list = sorted(lines)
            for line in lines_list:
                line_node = f"{station_id}:{line}"
                # Default transfer time
                default_transfer = 4.0

                # Try to find specific transfer time from interchanges data
                # Use the minimum transfer time to any other line at this station
                min_transfer = default_transfer
                for other_line in lines_list:
                    if other_line == line:
                        continue
                    key = (station_name_lower, line, other_line)
                    if key in interchange_times:
                        min_transfer = min(min_transfer,
                                           interchange_times[key] / 2.0)

                # Hub-to-line edge weight is half the transfer time
                # (full transfer = hub_to_line_A + hub_to_line_B)
                G.add_edge(hub_node, line_node, weight=min_transfer,
                           line='transfer', edge_type='hub_link')

    return G


def get_graph():
    """Get the cached network graph, building it if necessary."""
    global _graph, _stations
    if _graph is None:
        _stations = _load_stations()
        connections = _load_connections()
        interchanges = _load_interchanges()
        _graph = _build_graph(_stations, connections, interchanges)
    return _graph


def get_stations():
    """Get the cached station data dict."""
    global _stations
    if _stations is None:
        get_graph()  # This populates _stations as a side effect
    return _stations


def get_station_lookup():
    """Get a name -> station_id lookup dict."""
    global _station_lookup
    if _station_lookup is None:
        stations = get_stations()
        _station_lookup = {}
        for sid, info in stations.items():
            _station_lookup[info['name'].lower()] = sid
    return _station_lookup


def get_journey_time(graph, from_node, to_node):
    """
    Get shortest journey time between two nodes in the graph.
    Returns time in minutes, or None if no path exists.
    """
    try:
        return nx.shortest_path_length(graph, from_node, to_node, weight='weight')
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def get_journey_path(graph, from_node, to_node):
    """
    Get shortest path between two nodes. Returns list of node IDs.
    """
    try:
        return nx.shortest_path(graph, from_node, to_node, weight='weight')
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def get_lines_used(graph, path):
    """Extract the lines used in a journey path."""
    lines = set()
    for i in range(len(path) - 1):
        edge_data = graph.get_edge_data(path[i], path[i + 1])
        if edge_data and edge_data.get('line') not in ('transfer', 'walking'):
            lines.add(edge_data['line'])
    return lines


def reset_cache():
    """Reset the module cache. Useful for testing."""
    global _graph, _stations, _station_lookup
    _graph = None
    _stations = None
    _station_lookup = None
