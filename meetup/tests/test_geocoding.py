from unittest.mock import patch, MagicMock
from django.test import TestCase
from meetup.services.geocoding import autocomplete, is_postcode, geocode_postcode


class PostcodeDetectionTest(TestCase):
    def test_valid_postcodes(self):
        self.assertTrue(is_postcode('E1 6AN'))
        self.assertTrue(is_postcode('SW1A 1AA'))
        self.assertTrue(is_postcode('EC2R 8AH'))
        self.assertTrue(is_postcode('W1A 0AX'))
        self.assertTrue(is_postcode('e1 6an'))  # lowercase

    def test_invalid_postcodes(self):
        self.assertFalse(is_postcode('Old Street'))
        self.assertFalse(is_postcode('London'))
        self.assertFalse(is_postcode('123'))
        self.assertFalse(is_postcode(''))


class AutocompleteTest(TestCase):
    def test_short_query_returns_empty(self):
        """Queries shorter than 2 chars should return empty list."""
        self.assertEqual(autocomplete(''), [])
        self.assertEqual(autocomplete('a'), [])

    @patch('meetup.services.geocoding.requests.get')
    def test_photon_autocomplete(self, mock_get):
        """Should parse Photon GeoJSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'features': [
                {
                    'properties': {
                        'name': 'Old Street Station',
                        'city': 'London',
                    },
                    'geometry': {
                        'coordinates': [-0.0876, 51.5263],  # lon, lat
                    },
                },
            ],
        }
        mock_get.return_value = mock_response

        results = autocomplete('Old Street Station')
        self.assertEqual(len(results), 1)
        self.assertIn('Old Street Station', results[0]['label'])
        self.assertAlmostEqual(results[0]['lat'], 51.5263)
        self.assertAlmostEqual(results[0]['lon'], -0.0876)

    @patch('meetup.services.geocoding.requests.get')
    def test_postcode_lookup(self, mock_get):
        """Postcode queries should use Postcodes.io."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 200,
            'result': {
                'postcode': 'E1 6AN',
                'latitude': 51.5155,
                'longitude': -0.0715,
            },
        }
        mock_get.return_value = mock_response

        results = autocomplete('E1 6AN')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['label'], 'E1 6AN')
        self.assertAlmostEqual(results[0]['lat'], 51.5155)

    @patch('meetup.services.geocoding.requests.get')
    def test_api_failure_returns_empty(self, mock_get):
        """Network errors should return empty list, not crash."""
        import requests
        mock_get.side_effect = requests.RequestException("timeout")
        results = autocomplete('Old Street')
        self.assertEqual(results, [])
