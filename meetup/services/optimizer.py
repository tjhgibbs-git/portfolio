"""
Meetup spot optimizer.

Selects candidate meeting stations and scores them by different criteria:
- Fairness: minimise the longest individual journey (nobody gets a terrible trip)
- Efficiency: minimise total group journey time
- Quick arrival: same as fairness, outbound only
- Easy trip home: minimise the longest individual return journey

Uses the local NetworkX graph for all journey time calculations.
"""
import math
import networkx as nx
from .graph import get_graph, get_stations, get_journey_time, get_journey_path, get_lines_used
from .walking import find_nearest_stations, haversine_distance

# How far from the centroid to search for candidate stations (km)
CANDIDATE_RADIUS_KM = 8.0

# Maximum number of results to return
MAX_RESULTS = 5


def _compute_centroid(locations):
    """Compute geographic centroid of a list of (lat, lon) tuples."""
    if not locations:
        return (0, 0)
    avg_lat = sum(loc[0] for loc in locations) / len(locations)
    avg_lon = sum(loc[1] for loc in locations) / len(locations)
    return (avg_lat, avg_lon)


def _get_candidate_stations(origins, radius_km=CANDIDATE_RADIUS_KM):
    """
    Select candidate meeting stations based on proximity to group centroid
    and within the convex hull of origins.

    Returns list of station_id values.
    """
    stations = get_stations()
    centroid = _compute_centroid(origins)

    candidates = set()

    # Stations within radius of centroid
    for sid, info in stations.items():
        dist = haversine_distance(centroid[0], centroid[1],
                                  info['lat'], info['lon'])
        if dist <= radius_km:
            candidates.add(sid)

    # Also include stations near each origin (within 3km)
    for lat, lon in origins:
        for sid, info in stations.items():
            dist = haversine_distance(lat, lon, info['lat'], info['lon'])
            if dist <= 3.0:
                candidates.add(sid)

    return list(candidates)


def _connect_person_to_graph(graph, person_id, lat, lon):
    """
    Add a virtual person node to the graph, connected to their nearest stations
    via walking-time edges.

    Returns the virtual node ID.
    """
    virtual_node = f"person_{person_id}"
    nearest = find_nearest_stations(lat, lon)

    graph.add_node(virtual_node, name=f"Person {person_id}",
                   lat=lat, lon=lon, is_virtual=True)

    for station_id, info, dist_km, walk_minutes in nearest:
        # Connect to the station's hub node
        hub_node = str(station_id)
        if hub_node in graph:
            graph.add_edge(virtual_node, hub_node,
                           weight=walk_minutes, line='walking',
                           edge_type='walking')

    return virtual_node


def _remove_virtual_nodes(graph):
    """Remove all virtual person nodes from the graph."""
    virtual_nodes = [n for n in graph.nodes()
                     if str(n).startswith('person_')]
    graph.remove_nodes_from(virtual_nodes)


def _get_journey_details(graph, from_node, to_station_id):
    """
    Get detailed journey info from a node to a station hub.
    Returns dict with time, lines used, and path info.
    """
    hub_node = str(to_station_id)
    time = get_journey_time(graph, from_node, hub_node)
    if time is None:
        return None

    path = get_journey_path(graph, from_node, hub_node)
    lines = get_lines_used(graph, path) if path else set()

    return {
        'time_minutes': round(time, 1),
        'lines': sorted(lines),
    }


def calculate_meetup_spots(people):
    """
    Calculate the best meeting stations for a group of people.

    Args:
        people: list of dicts, each with:
            - name: str
            - origin_lat, origin_lon: float (where they're coming from)
            - home_lat, home_lon: float (where they'll go home to)

    Returns:
        dict with keys: 'fairness', 'efficiency', 'quick_arrival', 'easy_home'
        Each value is a list of up to MAX_RESULTS station results, each with:
            - station_id, station_name, lat, lon
            - score (the metric value)
            - journeys: per-person journey details
    """
    if len(people) < 2:
        return {'error': 'Need at least 2 people'}

    graph = get_graph()
    stations = get_stations()

    # Work on a copy so we can add virtual nodes without polluting the cache
    g = graph.copy()

    try:
        # Connect each person's origin and home to the graph
        origin_nodes = []
        home_nodes = []
        for i, person in enumerate(people):
            origin_node = _connect_person_to_graph(
                g, f"origin_{i}", person['origin_lat'], person['origin_lon'])
            origin_nodes.append(origin_node)

            home_node = _connect_person_to_graph(
                g, f"home_{i}", person['home_lat'], person['home_lon'])
            home_nodes.append(home_node)

        # Get candidate stations
        origins = [(p['origin_lat'], p['origin_lon']) for p in people]
        candidates = _get_candidate_stations(origins)

        if not candidates:
            return {'error': 'No candidate stations found near the group'}

        # Score each candidate station
        scored = []
        for station_id in candidates:
            hub_node = str(station_id)
            if hub_node not in g:
                continue

            # Compute outbound journey times (origin -> station)
            outbound_times = []
            outbound_details = []
            all_reachable = True
            for i, origin_node in enumerate(origin_nodes):
                details = _get_journey_details(g, origin_node, station_id)
                if details is None:
                    all_reachable = False
                    break
                outbound_times.append(details['time_minutes'])
                outbound_details.append({
                    'person': people[i]['name'],
                    'direction': 'outbound',
                    'time_minutes': details['time_minutes'],
                    'lines': details['lines'],
                })

            if not all_reachable:
                continue

            # Compute return journey times (station -> home)
            return_times = []
            return_details = []
            for i, home_node in enumerate(home_nodes):
                details = _get_journey_details(g, hub_node, home_node)
                if details is None:
                    # If return journey not found, still allow station but
                    # mark return as unknown
                    return_times.append(None)
                    return_details.append({
                        'person': people[i]['name'],
                        'direction': 'return',
                        'time_minutes': None,
                        'lines': [],
                    })
                else:
                    return_times.append(details['time_minutes'])
                    return_details.append({
                        'person': people[i]['name'],
                        'direction': 'return',
                        'time_minutes': details['time_minutes'],
                        'lines': details['lines'],
                    })

            station_info = stations[station_id]

            # Collect all lines used across all journeys for disruption checking
            all_lines = set()
            for d in outbound_details + return_details:
                all_lines.update(d.get('lines', []))

            scored.append({
                'station_id': station_id,
                'station_name': station_info['name'],
                'lat': station_info['lat'],
                'lon': station_info['lon'],
                'outbound_times': outbound_times,
                'return_times': return_times,
                'outbound_details': outbound_details,
                'return_details': return_details,
                'lines_used': sorted(all_lines),
                # Scores
                'score_fairness': max(outbound_times) + (
                    max(t for t in return_times if t is not None)
                    if any(t is not None for t in return_times) else 0
                ),
                'score_efficiency': sum(outbound_times),
                'score_quick_arrival': max(outbound_times),
                'score_easy_home': (
                    max(t for t in return_times if t is not None)
                    if any(t is not None for t in return_times) else float('inf')
                ),
            })

        if not scored:
            return {'error': 'Could not find reachable stations for all people'}

        # Sort by each scoring mode and take top results
        results = {}
        for mode, key in [
            ('fairness', 'score_fairness'),
            ('efficiency', 'score_efficiency'),
            ('quick_arrival', 'score_quick_arrival'),
            ('easy_home', 'score_easy_home'),
        ]:
            sorted_stations = sorted(scored, key=lambda x: x[key])
            results[mode] = []
            for s in sorted_stations[:MAX_RESULTS]:
                google_maps_url = (
                    f"https://www.google.com/maps/search/"
                    f"?api=1&query={s['lat']},{s['lon']}"
                )
                results[mode].append({
                    'station_id': s['station_id'],
                    'station_name': s['station_name'],
                    'lat': s['lat'],
                    'lon': s['lon'],
                    'score': round(s[key], 1),
                    'outbound_details': s['outbound_details'],
                    'return_details': s['return_details'],
                    'lines_used': s['lines_used'],
                    'google_maps_url': google_maps_url,
                })

        return results

    finally:
        # Clean up virtual nodes from the copy (not strictly necessary
        # since we're working on a copy, but good practice)
        pass
