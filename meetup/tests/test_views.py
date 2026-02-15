import json
from unittest.mock import patch
from django.test import TestCase, Client
from meetup.models import MeetupSession, Person


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


class ResultsViewTest(TestCase):
    @patch('meetup.views.get_line_disruptions')
    @patch('meetup.views.calculate_meetup_spots')
    def test_results_page_loads(self, mock_calc, mock_disruptions):
        mock_disruptions.return_value = []
        mock_calc.return_value = {
            'fairness': [{
                'station_id': 1, 'station_name': 'Test Station',
                'lat': 51.5, 'lon': -0.1, 'score': 10.0,
                'outbound_details': [], 'return_details': [],
                'lines_used': [], 'google_maps_url': 'https://example.com',
            }],
            'efficiency': [],
            'quick_arrival': [],
            'easy_home': [],
        }
        session = MeetupSession.objects.create()
        Person.objects.create(
            session=session, name='Alice',
            origin_label='A', origin_lat=51.5, origin_lon=-0.1,
            home_label='B', home_lat=51.5, home_lon=-0.1,
        )
        Person.objects.create(
            session=session, name='Bob',
            origin_label='C', origin_lat=51.48, origin_lon=-0.12,
            home_label='D', home_lat=51.48, home_lon=-0.12,
        )

        response = self.client.get(f'/meetup/results/{session.uuid}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'meetup/results.html')

    def test_invalid_uuid_returns_404(self):
        import uuid
        response = self.client.get(
            f'/meetup/results/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, 404)
