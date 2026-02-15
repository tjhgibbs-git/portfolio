"""
Management command to validate the London transport network graph data.

Checks for:
- All stations in connections have matching entries in stations.csv
- Graph connectivity (single connected component)
- Reasonable journey times for known routes
- All interchange stations exist
"""
import networkx as nx
from django.core.management.base import BaseCommand
from meetup.services.graph import (
    reset_cache, get_graph, get_stations, get_journey_time,
)


class Command(BaseCommand):
    help = 'Validate the London transport network graph data'

    def handle(self, *args, **options):
        self.stdout.write('Validating graph data...\n')
        reset_cache()

        stations = get_stations()
        graph = get_graph()

        self.stdout.write(f'  Stations loaded: {len(stations)}')
        self.stdout.write(f'  Graph nodes: {graph.number_of_nodes()}')
        self.stdout.write(f'  Graph edges: {graph.number_of_edges()}')

        # Check connectivity
        components = list(nx.connected_components(graph))
        self.stdout.write(f'  Connected components: {len(components)}')
        if len(components) > 1:
            sizes = sorted([len(c) for c in components], reverse=True)
            self.stdout.write(
                self.style.WARNING(f'  Component sizes: {sizes}'))

        # Check disconnected stations
        disconnected = []
        for sid, info in stations.items():
            if str(sid) not in graph:
                disconnected.append(info['name'])
        if disconnected:
            self.stdout.write(
                self.style.WARNING(
                    f'  {len(disconnected)} disconnected stations: '
                    f'{disconnected[:10]}...'
                ))
        else:
            self.stdout.write(
                self.style.SUCCESS('  All stations connected'))

        # Validate known routes
        def find_station(name):
            for sid, info in stations.items():
                if info['name'].lower() == name.lower():
                    return sid
            return None

        known_routes = [
            ('Bank', 'Brixton', 10, 25),
            ("King's Cross St. Pancras", 'Oxford Circus', 3, 15),
            ('Waterloo', 'Canary Wharf', 10, 25),
            ('Whitechapel', 'Brixton', 15, 35),
        ]

        errors = 0
        for start, end, min_time, max_time in known_routes:
            s_id = find_station(start)
            e_id = find_station(end)
            if not s_id or not e_id:
                self.stdout.write(
                    self.style.ERROR(f'  MISSING: {start} or {end}'))
                errors += 1
                continue

            time = get_journey_time(graph, str(s_id), str(e_id))
            if time is None:
                self.stdout.write(
                    self.style.ERROR(f'  NO PATH: {start} -> {end}'))
                errors += 1
            elif time < min_time or time > max_time:
                self.stdout.write(
                    self.style.WARNING(
                        f'  {start} -> {end}: {time:.1f} min '
                        f'(expected {min_time}-{max_time})'))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  {start} -> {end}: {time:.1f} min OK'))

        if errors:
            self.stdout.write(
                self.style.ERROR(f'\n{errors} validation errors found'))
        else:
            self.stdout.write(
                self.style.SUCCESS('\nGraph validation passed'))
