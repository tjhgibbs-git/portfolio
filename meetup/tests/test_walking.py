from django.test import TestCase
from meetup.services.walking import (
    haversine_distance, estimate_walking_time, find_nearest_stations,
)
from meetup.services.graph import reset_cache


class HaversineTest(TestCase):
    def test_same_point_zero_distance(self):
        dist = haversine_distance(51.5, -0.1, 51.5, -0.1)
        self.assertAlmostEqual(dist, 0, places=5)

    def test_known_distance(self):
        """Bank (51.5133, -0.0886) to Waterloo (51.5036, -0.1143)
        should be roughly 2km straight line."""
        dist = haversine_distance(51.5133, -0.0886, 51.5036, -0.1143)
        self.assertGreater(dist, 1.0)
        self.assertLess(dist, 3.0)

    def test_symmetry(self):
        d1 = haversine_distance(51.5, -0.1, 51.6, -0.2)
        d2 = haversine_distance(51.6, -0.2, 51.5, -0.1)
        self.assertAlmostEqual(d1, d2, places=5)


class WalkingTimeTest(TestCase):
    def test_walking_time_1km(self):
        """1km straight line at 5km/h with 1.3x multiplier ~ 15.6 min."""
        time = estimate_walking_time(1.0)
        self.assertGreater(time, 10)
        self.assertLess(time, 25)

    def test_zero_distance(self):
        time = estimate_walking_time(0)
        self.assertEqual(time, 0)


class NearestStationsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        reset_cache()

    def test_whitechapel_area(self):
        """E1 6AN (Whitechapel area, lat=51.5155, lon=-0.0715) should
        find Whitechapel, Aldgate East, or Aldgate as nearest stations."""
        nearest = find_nearest_stations(51.5155, -0.0715, n=3)
        self.assertEqual(len(nearest), 3)
        names = [info['name'].lower() for _, info, _, _ in nearest]
        # At least one of these should be in the top 3
        expected = {'whitechapel', 'aldgate east', 'aldgate'}
        self.assertTrue(expected & set(names),
                        f"Expected one of {expected} in {names}")

    def test_returns_walking_time(self):
        """Each result should include a walking time estimate."""
        nearest = find_nearest_stations(51.5, -0.1, n=3)
        for station_id, info, dist_km, walk_minutes in nearest:
            self.assertIsInstance(walk_minutes, float)
            self.assertGreater(walk_minutes, 0)

    def test_sorted_by_distance(self):
        """Results should be sorted by distance (ascending)."""
        nearest = find_nearest_stations(51.5, -0.1, n=5)
        distances = [dist for _, _, dist, _ in nearest]
        self.assertEqual(distances, sorted(distances))
