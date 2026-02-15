"""
Geocoding service using Photon (Komoot) and Postcodes.io.

Photon provides free-text geocoding with autocomplete, biased towards London.
Postcodes.io provides UK postcode lookup.

Neither requires an API key.
"""
import re
import requests
import logging

logger = logging.getLogger(__name__)

PHOTON_URL = 'https://photon.komoot.io/api/'
POSTCODES_URL = 'https://api.postcodes.io/postcodes/'

# London center for biasing geocoding results
LONDON_LAT = 51.5074
LONDON_LON = -0.1278

# UK postcode regex
POSTCODE_RE = re.compile(
    r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$',
    re.IGNORECASE
)

REQUEST_TIMEOUT = 5  # seconds


def is_postcode(text):
    """Check if text looks like a UK postcode."""
    return bool(POSTCODE_RE.match(text.strip()))


def geocode_postcode(postcode):
    """
    Look up a UK postcode using Postcodes.io.
    Returns dict with 'label', 'lat', 'lon' or None if not found.
    """
    postcode = postcode.strip().upper()
    try:
        response = requests.get(
            f'{POSTCODES_URL}{postcode}',
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 200 and data.get('result'):
                result = data['result']
                return {
                    'label': result['postcode'],
                    'lat': result['latitude'],
                    'lon': result['longitude'],
                }
    except requests.RequestException as e:
        logger.warning("Postcodes.io request failed: %s", e)
    return None


def autocomplete(query, limit=5):
    """
    Get autocomplete suggestions for a location query.

    First checks if the query is a postcode (uses Postcodes.io).
    Otherwise uses Photon geocoder biased towards London.

    Returns list of dicts with 'label', 'lat', 'lon'.
    """
    query = query.strip()
    if not query or len(query) < 2:
        return []

    results = []

    # If it looks like a postcode, try Postcodes.io
    if is_postcode(query):
        postcode_result = geocode_postcode(query)
        if postcode_result:
            return [postcode_result]

    # Use Photon for free-text geocoding
    try:
        response = requests.get(
            PHOTON_URL,
            params={
                'q': query,
                'lat': LONDON_LAT,
                'lon': LONDON_LON,
                'limit': limit,
                'lang': 'en',
            },
            timeout=REQUEST_TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [])
                if len(coords) >= 2:
                    # Build a readable label
                    parts = []
                    if props.get('name'):
                        parts.append(props['name'])
                    if props.get('street'):
                        parts.append(props['street'])
                    if props.get('city'):
                        parts.append(props['city'])
                    elif props.get('county'):
                        parts.append(props['county'])
                    if props.get('postcode'):
                        parts.append(props['postcode'])

                    label = ', '.join(parts) if parts else query
                    results.append({
                        'label': label,
                        'lat': coords[1],  # GeoJSON is [lon, lat]
                        'lon': coords[0],
                    })
    except requests.RequestException as e:
        logger.warning("Photon geocoding request failed: %s", e)

    return results
