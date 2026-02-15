import json
from unittest.mock import patch
from django.test import TestCase, Client
from meetup.models import MeetupSession, Person, MeetupResult


class IndexViewTest(TestCase):
    def test_index_returns_200(self):
        response = self.client.get('/meetup/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'meetup/index.html')

    def test_index_contains_key_elements(self):
        response = self.client.get('/meetup/')
        content = response.content.decode()
        self.assertIn('Meetup Spot', content)
        self.assertIn('person-template', content)
        self.assertIn('calculate-btn', content)


class AutocompleteViewTest(TestCase):
    def test_autocomplete_requires_query(self):
        response = self.client.get('/meetup/api/autocomplete/')
        data = json.loads(response.content)
        self.assertEqual(data['results'], [])

    def test_autocomplete_short_query(self):
        response = self.client.get('/meetup/api/autocomplete/?q=a')
        data = json.loads(response.content)
        self.assertEqual(data['results'], [])

    @patch('meetup.views.geocode_autocomplete')
    def test_autocomplete_returns_results(self, mock_autocomplete):
        mock_autocomplete.return_value = [
            {'label': 'Old Street', 'lat': 51.5263, 'lon': -0.0876},
        ]
        response = self.client.get('/meetup/api/autocomplete/?q=Old+Street')
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['label'], 'Old Street')

    def test_autocomplete_rejects_post(self):
        response = self.client.post('/meetup/api/autocomplete/')
        self.assertEqual(response.status_code, 405)


class CalculateViewTest(TestCase):
    def test_calculate_requires_post(self):
        response = self.client.get('/meetup/calculate/')
        self.assertEqual(response.status_code, 405)

    def test_calculate_requires_json(self):
        response = self.client.post(
            '/meetup/calculate/',
            'not json',
            content_type='text/plain',
        )
        self.assertEqual(response.status_code, 400)

    def test_calculate_requires_two_people(self):
        response = self.client.post(
            '/meetup/calculate/',
            json.dumps({'people': []}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_calculate_validates_required_fields(self):
        """People with missing fields should return 400."""
        response = self.client.post(
            '/meetup/calculate/',
            json.dumps({'people': [
                {'name': 'Alice'},
                {'name': 'Bob'},
            ]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    @patch('meetup.views.get_line_disruptions')
    def test_calculate_creates_session(self, mock_disruptions):
        mock_disruptions.return_value = []
        data = {
            'people': [
                {
                    'name': 'Alice',
                    'origin_lat': 51.5155, 'origin_lon': -0.0715,
                    'origin_label': 'Whitechapel',
                    'home_lat': 51.5322, 'home_lon': -0.1058,
                    'home_label': 'Angel',
                },
                {
                    'name': 'Bob',
                    'origin_lat': 51.4627, 'origin_lon': -0.1145,
                    'origin_label': 'Brixton',
                    'home_lat': 51.4694, 'home_lon': -0.0693,
                    'home_label': 'Peckham',
                },
            ],
        }
        response = self.client.post(
            '/meetup/calculate/',
            json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertIn('session_uuid', result)
        self.assertIn('results', result)

        # Check session was created in DB
        session = MeetupSession.objects.get(uuid=result['session_uuid'])
        self.assertEqual(session.people.count(), 2)

    @patch('meetup.views.get_line_disruptions')
    def test_calculate_saves_all_scoring_modes(self, mock_disruptions):
        """Results should be saved for all 4 scoring modes, not just fairness."""
        mock_disruptions.return_value = []
        data = {
            'people': [
                {
                    'name': 'Alice',
                    'origin_lat': 51.5155, 'origin_lon': -0.0715,
                    'origin_label': 'Whitechapel',
                    'home_lat': 51.5322, 'home_lon': -0.1058,
                    'home_label': 'Angel',
                },
                {
                    'name': 'Bob',
                    'origin_lat': 51.4627, 'origin_lon': -0.1145,
                    'origin_label': 'Brixton',
                    'home_lat': 51.4694, 'home_lon': -0.0693,
                    'home_label': 'Peckham',
                },
            ],
        }
        response = self.client.post(
            '/meetup/calculate/',
            json.dumps(data),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        session = MeetupSession.objects.get(uuid=result['session_uuid'])
        saved = session.results.all()

        # Every saved result should have all 4 scores populated
        for r in saved:
            self.assertIsNotNone(r.score_fairness,
                                 f"{r.station_name} missing score_fairness")
            self.assertIsNotNone(r.score_efficiency,
                                 f"{r.station_name} missing score_efficiency")
            self.assertIsNotNone(r.score_quick_arrival,
                                 f"{r.station_name} missing score_quick_arrival")
            self.assertIsNotNone(r.score_easy_home,
                                 f"{r.station_name} missing score_easy_home")

    @patch('meetup.views.get_line_disruptions')
    def test_calculate_returns_disruptions(self, mock_disruptions):
        """Disruption warnings should be included in the response."""
        mock_disruptions.return_value = [
            {'line': 'Central', 'status': 'Minor Delays', 'reason': 'Signal failure'},
        ]
        data = {
            'people': [
                {
                    'name': 'Alice',
                    'origin_lat': 51.5155, 'origin_lon': -0.0715,
                    'origin_label': 'Whitechapel',
                    'home_lat': 51.5322, 'home_lon': -0.1058,
                    'home_label': 'Angel',
                },
                {
                    'name': 'Bob',
                    'origin_lat': 51.4627, 'origin_lon': -0.1145,
                    'origin_label': 'Brixton',
                    'home_lat': 51.4694, 'home_lon': -0.0693,
                    'home_label': 'Peckham',
                },
            ],
        }
        response = self.client.post(
            '/meetup/calculate/',
            json.dumps(data),
            content_type='application/json',
        )
        result = json.loads(response.content)
        self.assertIn('disruptions', result)
        self.assertEqual(len(result['disruptions']), 1)
        self.assertEqual(result['disruptions'][0]['line'], 'Central')


class ResultsViewTest(TestCase):
    def _create_session_with_results(self):
        """Helper: create a session with people and saved MeetupResult records."""
        session = MeetupSession.objects.create()
        Person.objects.create(
            session=session, name='Alice',
            origin_label='Whitechapel', origin_lat=51.5155, origin_lon=-0.0715,
            home_label='Angel', home_lat=51.5322, home_lon=-0.1058,
        )
        Person.objects.create(
            session=session, name='Bob',
            origin_label='Brixton', origin_lat=51.4627, origin_lon=-0.1145,
            home_label='Peckham', home_lat=51.4694, home_lon=-0.0693,
        )
        MeetupResult.objects.create(
            session=session,
            station_name='Bank',
            station_lat=51.5133, station_lon=-0.0886,
            score_fairness=25.0, score_efficiency=30.0,
            score_quick_arrival=15.0, score_easy_home=12.0,
            journey_details_json=json.dumps({
                'outbound': [
                    {'person': 'Alice', 'direction': 'outbound',
                     'time_minutes': 10.0, 'lines': ['Central']},
                    {'person': 'Bob', 'direction': 'outbound',
                     'time_minutes': 15.0, 'lines': ['Victoria']},
                ],
                'return': [
                    {'person': 'Alice', 'direction': 'return',
                     'time_minutes': 8.0, 'lines': ['Northern']},
                    {'person': 'Bob', 'direction': 'return',
                     'time_minutes': 12.0, 'lines': ['Victoria']},
                ],
            }),
            google_maps_url='https://www.google.com/maps/search/?api=1&query=51.5133,-0.0886',
        )
        MeetupResult.objects.create(
            session=session,
            station_name='Waterloo',
            station_lat=51.5036, station_lon=-0.1143,
            score_fairness=28.0, score_efficiency=26.0,
            score_quick_arrival=18.0, score_easy_home=10.0,
            journey_details_json=json.dumps({
                'outbound': [
                    {'person': 'Alice', 'direction': 'outbound',
                     'time_minutes': 12.0, 'lines': ['Jubilee']},
                    {'person': 'Bob', 'direction': 'outbound',
                     'time_minutes': 18.0, 'lines': ['Northern']},
                ],
                'return': [
                    {'person': 'Alice', 'direction': 'return',
                     'time_minutes': 10.0, 'lines': ['Northern']},
                    {'person': 'Bob', 'direction': 'return',
                     'time_minutes': 10.0, 'lines': ['Northern']},
                ],
            }),
            google_maps_url='https://www.google.com/maps/search/?api=1&query=51.5036,-0.1143',
        )
        return session

    @patch('meetup.views.get_line_disruptions')
    def test_results_page_loads_from_db(self, mock_disruptions):
        """Results page should load saved results from DB, not re-calculate."""
        mock_disruptions.return_value = []
        session = self._create_session_with_results()

        response = self.client.get(f'/meetup/results/{session.uuid}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'meetup/results.html')

        # Verify the template context has all 4 modes
        context_results = response.context['results']
        for mode in ['fairness', 'efficiency', 'quick_arrival', 'easy_home']:
            self.assertIn(mode, context_results)
            self.assertGreater(len(context_results[mode]), 0)

    @patch('meetup.views.get_line_disruptions')
    def test_results_sorted_by_mode_score(self, mock_disruptions):
        """Each mode's results should be sorted by that mode's score."""
        mock_disruptions.return_value = []
        session = self._create_session_with_results()

        response = self.client.get(f'/meetup/results/{session.uuid}/')
        context_results = response.context['results']

        # Fairness: Bank (25.0) should come before Waterloo (28.0)
        self.assertEqual(context_results['fairness'][0]['station_name'], 'Bank')
        # Efficiency: Waterloo (26.0) should come before Bank (30.0)
        self.assertEqual(context_results['efficiency'][0]['station_name'], 'Waterloo')
        # Easy home: Waterloo (10.0) should come before Bank (12.0)
        self.assertEqual(context_results['easy_home'][0]['station_name'], 'Waterloo')

    @patch('meetup.views.get_line_disruptions')
    def test_results_checks_live_disruptions(self, mock_disruptions):
        """Results page should check live TfL disruptions for lines in results."""
        mock_disruptions.return_value = [
            {'line': 'Central', 'status': 'Severe Delays', 'reason': ''},
        ]
        session = self._create_session_with_results()

        response = self.client.get(f'/meetup/results/{session.uuid}/')
        self.assertEqual(len(response.context['disruptions']), 1)
        # Should have called disruptions check with lines from journey details
        mock_disruptions.assert_called_once()
        called_lines = mock_disruptions.call_args[0][0]
        self.assertIn('Central', called_lines)

    @patch('meetup.views.get_line_disruptions')
    def test_results_no_saved_results_shows_error(self, mock_disruptions):
        """A session with no saved results should show an error."""
        mock_disruptions.return_value = []
        session = MeetupSession.objects.create()
        Person.objects.create(
            session=session, name='Alice',
            origin_label='A', origin_lat=51.5, origin_lon=-0.1,
            home_label='B', home_lat=51.5, home_lon=-0.1,
        )

        response = self.client.get(f'/meetup/results/{session.uuid}/')
        self.assertEqual(response.status_code, 200)
        context_results = response.context['results']
        self.assertIn('error', context_results)

    def test_invalid_uuid_returns_404(self):
        import uuid
        response = self.client.get(
            f'/meetup/results/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, 404)
