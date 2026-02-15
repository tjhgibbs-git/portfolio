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
        # Collect all unique station sets across modes (not just #1)
        mode_station_sets = {}
        for mode in ['fairness', 'efficiency', 'quick_arrival', 'easy_home']:
            mode_station_sets[mode] = [r['station_name'] for r in results[mode]]
        # At least two modes should have different top-5 orderings
        orderings = set(tuple(v) for v in mode_station_sets.values())
        self.assertGreaterEqual(len(orderings), 2,
                                "Expected at least two distinct station orderings "
                                "across scoring modes")

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

    def test_results_sorted_by_score(self):
        """Each mode's results should be sorted ascending by score."""
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
        for mode in ['fairness', 'efficiency', 'quick_arrival', 'easy_home']:
            scores = [r['score'] for r in results[mode]]
            self.assertEqual(scores, sorted(scores),
                             f"{mode} results not sorted by score")

    def test_results_include_all_four_scores(self):
        """Each result should include all 4 score values for DB persistence."""
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
        for mode in ['fairness', 'efficiency', 'quick_arrival', 'easy_home']:
            for r in results[mode]:
                self.assertIn('score_fairness', r)
                self.assertIn('score_efficiency', r)
                self.assertIn('score_quick_arrival', r)
                self.assertIn('score_easy_home', r)

    def test_same_origin_and_home(self):
        """People whose home is the same as their origin should still work."""
        people = [
            {
                'name': 'Alice',
                'origin_lat': 51.5155, 'origin_lon': -0.0715,
                'home_lat': 51.5155, 'home_lon': -0.0715,
            },
            {
                'name': 'Bob',
                'origin_lat': 51.4627, 'origin_lon': -0.1145,
                'home_lat': 51.4627, 'home_lon': -0.1145,
            },
        ]
        results = calculate_meetup_spots(people)
        self.assertNotIn('error', results)
        for mode in ['fairness', 'efficiency', 'quick_arrival', 'easy_home']:
            self.assertGreater(len(results[mode]), 0)

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
