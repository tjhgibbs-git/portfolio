"""
Walking distance and nearest station finder.

Uses haversine formula to calculate straight-line distance between coordinates,
then estimates walking time with a street routing multiplier.
"""
import math
from .graph import get_stations

# Walking speed in km/h
WALKING_SPEED_KMH = 5.0

# Multiplier for street routing vs straight-line distance
# Streets aren't straight, so actual walking distance is typically ~1.3x the
# haversine distance in London's grid-ish layout
STREET_ROUTING_MULTIPLIER = 1.3

# Number of nearest stations to consider when connecting a person to the graph
NUM_NEAREST_STATIONS = 3


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth.
    Returns distance in kilometres.
    """
    R = 6371.0  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def estimate_walking_time(distance_km):
    """
    Estimate walking time in minutes from straight-line distance.
    Applies a street routing multiplier to account for non-straight paths.
    """
    adjusted_distance = distance_km * STREET_ROUTING_MULTIPLIER
    return (adjusted_distance / WALKING_SPEED_KMH) * 60


def find_nearest_stations(lat, lon, n=NUM_NEAREST_STATIONS):
    """
    Find the n nearest stations to a given lat/lon coordinate.
    Returns a list of (station_id, station_info, distance_km, walking_minutes)
    sorted by distance.
    """
    stations = get_stations()
    distances = []

    for station_id, info in stations.items():
        dist = haversine_distance(lat, lon, info['lat'], info['lon'])
        walk_time = estimate_walking_time(dist)
        distances.append((station_id, info, dist, walk_time))

    distances.sort(key=lambda x: x[2])
    return distances[:n]
