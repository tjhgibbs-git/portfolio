from unittest.mock import patch, MagicMock
from django.test import TestCase
from meetup.services.disruptions import get_line_disruptions


class DisruptionsTest(TestCase):
    @patch('meetup.services.disruptions.requests.get')
    def test_returns_disrupted_lines(self, mock_get):
        """Lines with severity < 10 should be returned as disruptions."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'Central',
                'lineStatuses': [
                    {
                        'statusSeverity': 5,
                        'statusSeverityDescription': 'Minor Delays',
                        'reason': 'Signal failure at Bank',
                    },
                ],
            },
            {
                'name': 'Northern',
                'lineStatuses': [
                    {
                        'statusSeverity': 10,
                        'statusSeverityDescription': 'Good Service',
                    },
                ],
            },
        ]
        mock_get.return_value = mock_response

        disruptions = get_line_disruptions()
        self.assertEqual(len(disruptions), 1)
        self.assertEqual(disruptions[0]['line'], 'Central')
        self.assertEqual(disruptions[0]['status'], 'Minor Delays')
        self.assertIn('Signal failure', disruptions[0]['reason'])

    @patch('meetup.services.disruptions.requests.get')
    def test_filters_to_requested_lines(self, mock_get):
        """Should only return disruptions for requested lines."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'Central',
                'lineStatuses': [
                    {'statusSeverity': 5, 'statusSeverityDescription': 'Delays'},
                ],
            },
            {
                'name': 'Victoria',
                'lineStatuses': [
                    {'statusSeverity': 3, 'statusSeverityDescription': 'Suspended'},
                ],
            },
        ]
        mock_get.return_value = mock_response

        # Only ask about Victoria
        disruptions = get_line_disruptions(['Victoria'])
        self.assertEqual(len(disruptions), 1)
        self.assertEqual(disruptions[0]['line'], 'Victoria')

    @patch('meetup.services.disruptions.requests.get')
    def test_good_service_not_included(self, mock_get):
        """Lines with severity 10 (Good Service) should not appear."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'Central',
                'lineStatuses': [
                    {'statusSeverity': 10, 'statusSeverityDescription': 'Good Service'},
                ],
            },
        ]
        mock_get.return_value = mock_response

        disruptions = get_line_disruptions()
        self.assertEqual(len(disruptions), 0)

    @patch('meetup.services.disruptions.requests.get')
    def test_api_failure_returns_empty(self, mock_get):
        """Network errors should return empty list, not crash."""
        import requests
        mock_get.side_effect = requests.RequestException("timeout")
        disruptions = get_line_disruptions()
        self.assertEqual(disruptions, [])

    @patch('meetup.services.disruptions.requests.get')
    def test_non_200_returns_empty(self, mock_get):
        """Non-200 response should return empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        disruptions = get_line_disruptions()
        self.assertEqual(disruptions, [])

    @patch('meetup.services.disruptions.requests.get')
    def test_line_name_matching_case_insensitive(self, mock_get):
        """Line name matching should be case-insensitive."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'Central',
                'lineStatuses': [
                    {'statusSeverity': 5, 'statusSeverityDescription': 'Delays'},
                ],
            },
        ]
        mock_get.return_value = mock_response

        # Query with different case
        disruptions = get_line_disruptions(['central'])
        self.assertEqual(len(disruptions), 1)
