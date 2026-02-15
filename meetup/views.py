import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import MeetupSession, Person, MeetupResult
from .services.geocoding import autocomplete as geocode_autocomplete
from .services.optimizer import calculate_meetup_spots
from .services.disruptions import get_line_disruptions


@ensure_csrf_cookie
def index(request):
    """Main page - add people and calculate meeting spot."""
    return render(request, 'meetup/index.html')


@require_POST
def calculate(request):
    """Process the form and calculate optimal meeting stations."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    people_data = data.get('people', [])
    if len(people_data) < 2:
        return JsonResponse({'error': 'Need at least 2 people'}, status=400)

    # Validate people data
    for p in people_data:
        required = ['name', 'origin_lat', 'origin_lon', 'origin_label',
                     'home_lat', 'home_lon', 'home_label']
        if not all(k in p for k in required):
            return JsonResponse(
                {'error': f'Missing fields for {p.get("name", "unknown")}'},
                status=400
            )

    # Create session
    session = MeetupSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
    )

    # Create person records
    for p in people_data:
        Person.objects.create(
            session=session,
            name=p['name'],
            origin_label=p['origin_label'],
            origin_lat=float(p['origin_lat']),
            origin_lon=float(p['origin_lon']),
            home_label=p['home_label'],
            home_lat=float(p['home_lat']),
            home_lon=float(p['home_lon']),
        )

    # Calculate meetup spots
    people_for_calc = [
        {
            'name': p['name'],
            'origin_lat': float(p['origin_lat']),
            'origin_lon': float(p['origin_lon']),
            'home_lat': float(p['home_lat']),
            'home_lon': float(p['home_lon']),
        }
        for p in people_data
    ]

    results = calculate_meetup_spots(people_for_calc)

    if 'error' in results:
        return JsonResponse({'error': results['error']}, status=400)

    # Collect all lines used across all results for disruption check
    all_lines = set()
    for mode_results in results.values():
        for r in mode_results:
            all_lines.update(r.get('lines_used', []))

    # Check for disruptions
    disruptions = []
    if all_lines:
        disruptions = get_line_disruptions(all_lines)

    # Save results — all unique stations across all 4 scoring modes
    station_data = {}
    for mode in ['fairness', 'efficiency', 'quick_arrival', 'easy_home']:
        for r in results.get(mode, []):
            sid = r['station_id']
            if sid not in station_data:
                station_data[sid] = {
                    'station_name': r['station_name'],
                    'station_lat': r['lat'],
                    'station_lon': r['lon'],
                    'score_fairness': r['score_fairness'],
                    'score_efficiency': r['score_efficiency'],
                    'score_quick_arrival': r['score_quick_arrival'],
                    'score_easy_home': r['score_easy_home'],
                    'journey_details_json': json.dumps({
                        'outbound': r['outbound_details'],
                        'return': r['return_details'],
                    }),
                    'google_maps_url': r['google_maps_url'],
                }

    for data in station_data.values():
        MeetupResult.objects.create(session=session, **data)

    return JsonResponse({
        'session_uuid': str(session.uuid),
        'results': results,
        'disruptions': disruptions,
    })


def results(request, session_uuid):
    """Display results for a meetup session, loaded from saved DB records."""
    session = get_object_or_404(MeetupSession, uuid=session_uuid)
    people = session.people.all()
    saved_results = list(session.results.all())

    if not saved_results:
        context = {
            'session': session,
            'people': people,
            'results': {'error': 'No results found for this session.'},
            'results_json': json.dumps({'error': 'No results found'}),
            'disruptions': [],
        }
        return render(request, 'meetup/results.html', context)

    # Reconstruct per-mode results from saved DB records
    all_lines = set()
    calc_results = {}
    mode_fields = [
        ('fairness', 'score_fairness'),
        ('efficiency', 'score_efficiency'),
        ('quick_arrival', 'score_quick_arrival'),
        ('easy_home', 'score_easy_home'),
    ]

    for mode, score_field in mode_fields:
        mode_records = [r for r in saved_results
                        if getattr(r, score_field) is not None]
        mode_records.sort(key=lambda r: getattr(r, score_field))

        calc_results[mode] = []
        for r in mode_records[:5]:
            details = r.journey_details
            outbound = details.get('outbound', [])
            return_details = details.get('return', [])

            lines_used = set()
            for d in outbound + return_details:
                lines_used.update(d.get('lines', []))
            all_lines.update(lines_used)

            calc_results[mode].append({
                'station_name': r.station_name,
                'lat': r.station_lat,
                'lon': r.station_lon,
                'score': getattr(r, score_field),
                'outbound_details': outbound,
                'return_details': return_details,
                'lines_used': sorted(lines_used),
                'google_maps_url': r.google_maps_url,
            })

    # Check live disruptions for lines used in results
    disruptions = get_line_disruptions(all_lines) if all_lines else []

    context = {
        'session': session,
        'people': people,
        'results': calc_results,
        'results_json': json.dumps(calc_results),
        'disruptions': disruptions,
    }
    return render(request, 'meetup/results.html', context)


@require_GET
def autocomplete(request):
    """API endpoint for location autocomplete."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    results = geocode_autocomplete(query, limit=5)
    return JsonResponse({'results': results})
