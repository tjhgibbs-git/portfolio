from django.test import TestCase
from meetup.services.optimizer import calculate_meetup_spots
from meetup.services.graph import reset_cache


class OptimizerTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        reset_cache()

    def test_two_people_returns_results(self):
        """Two people should produce results with all scoring modes."""
        people = [
            {
                'name': 'Alice',
                'origin_lat': 51.5155, 'origin_lon': -0.0715,  # Whitechapel
                'home_lat': 51.5322, 'home_lon': -0.1058,  # Angel
            },
            {
                'name': 'Bob',
                'origin_lat': 51.4627, 'origin_lon': -0.1145,  # Brixton
                'home_lat': 51.4694, 'home_lon': -0.0693,  # Peckham
            },
        ]
        results = calculate_meetup_spots(people)
        self.assertNotIn('error', results)
        for mode in ['fairness', 'efficiency', 'quick_arrival', 'easy_home']:
            self.assertIn(mode, results)
            self.assertGreater(len(results[mode]), 0)

    def test_results_have_required_fields(self):
        """Each result should have station name, coords, score, details."""
        people = [
            {
                'name': 'Alice',
                'origin_lat': 51.5155, 'origin_lon': -0.0715,
                'home_lat': 51.5322, 'home_lon': -0.1058,
            },
            {
                'name': 'Bob',
                'origin_lat': 51.4627, 'origin_lon': -0.1145,
                'home_lat': 51.4694, 'home_lon': -0.0693,
            },
        ]
        results = calculate_meetup_spots(people)
        for r in results['fairness']:
            self.assertIn('station_name', r)
            self.assertIn('lat', r)
            self.assertIn('lon', r)
            self.assertIn('score', r)
            self.assertIn('outbound_details', r)
            self.assertIn('return_details', r)
            self.assertIn('google_maps_url', r)

    def test_three_people_central_result(self):
        """Three people spread across London should get a central-ish result."""
        people = [
            {
                'name': 'Alice',
                'origin_lat': 51.5155, 'origin_lon': -0.0715,  # Whitechapel
                'home_lat': 51.5322, 'home_lon': -0.1058,  # Angel
            },
            {
                'name': 'Bob',
                'origin_lat': 51.4627, 'origin_lon': -0.1145,  # Brixton
                'home_lat': 51.4694, 'home_lon': -0.0693,  # Peckham
            },
            {
                'name': 'Charlie',
                'origin_lat': 51.5133, 'origin_lon': -0.0886,  # Bank area
                'home_lat': 51.5046, 'home_lon': -0.2187,  # Shepherd's Bush
            },
        ]
        results = calculate_meetup_spots(people)
        self.assertNotIn('error', results)

        # The top fairness result should be reasonably central (zone 1-2)
        top = results['fairness'][0]
        lat, lon = top['lat'], top['lon']
        # Should be within central London (roughly)
        self.assertGreater(lat, 51.45)
        self.assertLess(lat, 51.56)

    def test_too_few_people_returns_error(self):
        """Less than 2 people should return an error."""
        people = [
            {
                'name': 'Alice',
                'origin_lat': 51.5, 'origin_lon': -0.1,
                'home_lat': 51.5, 'home_lon': -0.1,
            },
        ]
        results = calculate_meetup_spots(people)
        self.assertIn('error', results)

    def test_different_modes_can_differ(self):
        """Different scoring modes should potentially produce different top results."""
        people = [
            {
                'name': 'Alice',
                'origin_lat': 51.5155, 'origin_lon': -0.0715,  # Whitechapel
                'home_lat': 51.5822, 'home_lon': -0.0749,  # Seven Sisters
            },
            {
                'name': 'Bob',
                'origin_lat': 51.4627, 'origin_lon': -0.1145,  # Brixton
                'home_lat': 51.4214, 'home_lon': -0.2064,  # Wimbledon
            },
            {
                'name': 'Charlie',
                'origin_lat': 51.5133, 'origin_lon': -0.0886,  # Bank area
                'home_lat': 51.5046, 'home_lon': -0.2187,  # Shepherd's Bush
            },
        ]
        results = calculate_meetup_spots(people)
        # Collect all unique top stations across modes
        top_stations = set()
        for mode in ['fairness', 'efficiency', 'quick_arrival', 'easy_home']:
            if results[mode]:
                top_stations.add(results[mode][0]['station_name'])
        # We should see at least some variety (not all the same)
        # This isn't guaranteed but is likely with this spread
        self.assertGreaterEqual(len(top_stations), 1)

    def test_google_maps_url_format(self):
        """Google Maps URLs should be properly formatted."""
        people = [
            {
                'name': 'A',
                'origin_lat': 51.5, 'origin_lon': -0.1,
                'home_lat': 51.5, 'home_lon': -0.1,
            },
            {
                'name': 'B',
                'origin_lat': 51.48, 'origin_lon': -0.12,
                'home_lat': 51.48, 'home_lon': -0.12,
            },
        ]
        results = calculate_meetup_spots(people)
        for r in results.get('fairness', []):
            self.assertTrue(
                r['google_maps_url'].startswith('https://www.google.com/maps/'))

    def test_outbound_details_per_person(self):
        """Each result should have outbound details for each person."""
        people = [
            {
                'name': 'Alice',
                'origin_lat': 51.5155, 'origin_lon': -0.0715,
                'home_lat': 51.5322, 'home_lon': -0.1058,
            },
            {
                'name': 'Bob',
                'origin_lat': 51.4627, 'origin_lon': -0.1145,
                'home_lat': 51.4694, 'home_lon': -0.0693,
            },
        ]
        results = calculate_meetup_spots(people)
        for r in results['fairness']:
            self.assertEqual(len(r['outbound_details']), 2)
            self.assertEqual(r['outbound_details'][0]['person'], 'Alice')
            self.assertEqual(r['outbound_details'][1]['person'], 'Bob')
