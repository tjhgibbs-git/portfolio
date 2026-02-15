"""
TfL line status service for disruption warnings.

Makes a single API call to TfL's line status endpoint to check
for disruptions on tube, overground, DLR, and Elizabeth line.

This is the ONLY external API call the calculation needs to make,
and it's optional — the app works fine without it.
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

TFL_LINE_STATUS_URL = (
    'https://api.tfl.gov.uk/Line/Mode/'
    'tube,overground,dlr,elizabeth-line/Status'
)

REQUEST_TIMEOUT = 5  # seconds


def get_line_disruptions(lines_to_check=None):
    """
    Check TfL line status for disruptions.

    Args:
        lines_to_check: optional set/list of line names to filter.
                        If None, returns all disruptions.

    Returns:
        list of dicts with 'line', 'status', 'reason' for disrupted lines.
        Returns empty list if the API call fails (fails silently).
    """
    disruptions = []

    params = {}
    api_key = os.environ.get('TFL_API_KEY')
    if api_key:
        params['app_key'] = api_key

    try:
        response = requests.get(
            TFL_LINE_STATUS_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            logger.warning("TfL API returned status %d", response.status_code)
            return []

        data = response.json()

        # Normalise line names for comparison
        line_name_map = {}
        if lines_to_check:
            for line in lines_to_check:
                line_name_map[line.lower()] = line

        for line_data in data:
            line_name = line_data.get('name', '')

            # Filter to requested lines if specified
            if lines_to_check:
                if line_name.lower() not in line_name_map:
                    continue

            for status in line_data.get('lineStatuses', []):
                severity = status.get('statusSeverity', 10)
                # Severity 10 = Good Service, lower = worse
                if severity < 10:
                    disruptions.append({
                        'line': line_name,
                        'status': status.get('statusSeverityDescription', 'Unknown'),
                        'reason': status.get('reason', ''),
                    })

    except requests.RequestException as e:
        logger.warning("TfL API request failed: %s", e)

    return disruptions
