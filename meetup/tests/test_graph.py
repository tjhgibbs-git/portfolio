from django.test import TestCase
from meetup.services.graph import (
    get_graph, get_stations, get_journey_time, get_journey_path,
    get_lines_used, get_station_lookup, reset_cache,
)


class GraphLoadingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        reset_cache()
        cls.graph = get_graph()
        cls.stations = get_stations()

    def test_stations_loaded(self):
        """Should load a substantial number of stations."""
        self.assertGreater(len(self.stations), 300)

    def test_graph_has_nodes_and_edges(self):
        """Graph should have nodes and edges."""
        self.assertGreater(self.graph.number_of_nodes(), 500)
        self.assertGreater(self.graph.number_of_edges(), 500)

    def test_key_stations_exist(self):
        """Key London stations should be in the dataset."""
        station_names = {info['name'].lower() for info in self.stations.values()}
        for name in ['bank', 'oxford circus', 'waterloo', 'brixton',
                     "king's cross st. pancras", 'canary wharf', 'angel',
                     'whitechapel', 'victoria', 'paddington']:
            self.assertIn(name, station_names, f"Missing station: {name}")

    def test_station_has_coordinates(self):
        """Each station should have valid lat/lon."""
        for sid, info in self.stations.items():
            self.assertIsInstance(info['lat'], float)
            self.assertIsInstance(info['lon'], float)
            # London is roughly lat 51.3-51.7, lon -0.5 to 0.3
            self.assertGreater(info['lat'], 51.0,
                               f"Station {info['name']} lat too low")
            self.assertLess(info['lat'], 52.0,
                            f"Station {info['name']} lat too high")

    def test_station_lookup(self):
        """Station lookup by name should work."""
        lookup = get_station_lookup()
        self.assertIn('bank', lookup)
        self.assertIn('oxford circus', lookup)


class GraphRoutingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        reset_cache()
        cls.graph = get_graph()
        cls.stations = get_stations()

    def _find_station(self, name):
        for sid, info in self.stations.items():
            if info['name'].lower() == name.lower():
                return sid
        return None

    def test_bank_to_brixton(self):
        """Bank to Brixton should be reachable and ~15-25 min."""
        bank = self._find_station('Bank')
        brixton = self._find_station('Brixton')
        self.assertIsNotNone(bank)
        self.assertIsNotNone(brixton)
        time = get_journey_time(self.graph, str(bank), str(brixton))
        self.assertIsNotNone(time)
        self.assertGreater(time, 10)
        self.assertLess(time, 30)

    def test_waterloo_to_canary_wharf(self):
        """Waterloo to Canary Wharf should be ~12-25 min."""
        wl = self._find_station('Waterloo')
        cw = self._find_station('Canary Wharf')
        time = get_journey_time(self.graph, str(wl), str(cw))
        self.assertIsNotNone(time)
        self.assertGreater(time, 8)
        self.assertLess(time, 30)

    def test_same_station_zero_time(self):
        """Journey from a station to itself should be 0."""
        bank = self._find_station('Bank')
        time = get_journey_time(self.graph, str(bank), str(bank))
        self.assertEqual(time, 0)

    def test_journey_path_returns_nodes(self):
        """get_journey_path should return a list of node IDs."""
        bank = self._find_station('Bank')
        waterloo = self._find_station('Waterloo')
        path = get_journey_path(self.graph, str(bank), str(waterloo))
        self.assertIsNotNone(path)
        self.assertIsInstance(path, list)
        self.assertGreater(len(path), 1)

    def test_lines_used_extraction(self):
        """get_lines_used should return tube line names."""
        bank = self._find_station('Bank')
        waterloo = self._find_station('Waterloo')
        path = get_journey_path(self.graph, str(bank), str(waterloo))
        lines = get_lines_used(self.graph, path)
        self.assertIsInstance(lines, set)
        # Should use at least one real line (not just transfer)
        real_lines = lines - {'transfer', 'walking'}
        self.assertGreater(len(real_lines), 0)

    def test_unreachable_returns_none(self):
        """Non-existent station should return None."""
        time = get_journey_time(self.graph, 'nonexistent', '12')
        self.assertIsNone(time)

    def test_reset_cache(self):
        """reset_cache should allow fresh reload."""
        reset_cache()
        graph = get_graph()
        self.assertGreater(graph.number_of_nodes(), 500)
