import unittest
from unittest.mock import patch, MagicMock
from main import check_and_update_pricing
import os

class TestMain(unittest.TestCase):

    def setUp(self):
        # Ensure a clean .env for tests that might try to load it
        if os.path.exists('.env'):
            os.remove('.env')

    def tearDown(self):
        if os.path.exists('.env'):
            os.remove('.env')

    @patch('main.get_gemini_pricing')
    @patch('main.read_pricing_data')
    @patch('main.write_pricing_data')
    def test_price_change_triggers_update(self, mock_write_data, mock_read_data, mock_get_pricing):
        # Scenario 1: Price change
        mock_get_pricing.return_value = [
            {'sku_id': 'gemini_2_5_pro', 'description': 'Gemini 2.5 Pro Model', 'usd_price': '0.001', 'last_updated': '2023-01-01 10:00:00'}
        ]
        mock_read_data.return_value = [
            {'sku_id': 'gemini_2_5_pro', 'description': 'Gemini 2.5 Pro Model', 'usd_price': '0.002', 'last_updated': '2023-01-01 09:00:00'}
        ]

        check_and_update_pricing('test_pricing.csv')

        mock_write_data.assert_called_once()
        # Ensure the written data matches the new pricing from the API
        written_data = mock_write_data.call_args[0][1]
        self.assertEqual(len(written_data), 1)
        self.assertEqual(written_data[0]['usd_price'], '0.001')

    @patch('main.get_gemini_pricing')
    @patch('main.read_pricing_data')
    @patch('main.write_pricing_data')
    def test_no_price_change_does_nothing(self, mock_write_data, mock_read_data, mock_get_pricing):
        # Scenario 2: No price change
        current_time = '2023-01-01 10:00:00'
        mock_get_pricing.return_value = [
            {'sku_id': 'gemini_2_5_pro', 'description': 'Gemini 2.5 Pro Model', 'usd_price': '0.001', 'last_updated': current_time}
        ]
        mock_read_data.return_value = [
            {'sku_id': 'gemini_2_5_pro', 'description': 'Gemini 2.5 Pro Model', 'usd_price': '0.001', 'last_updated': current_time}
        ]

        check_and_update_pricing('test_pricing.csv')

        mock_write_data.assert_not_called()

    @patch('main.get_gemini_pricing')
    @patch('main.read_pricing_data')
    @patch('main.write_pricing_data')
    @patch('builtins.print') # Mock print to capture output for error logging test
    def test_api_error_is_logged_and_no_update(self, mock_print, mock_write_data, mock_read_data, mock_get_pricing):
        # Scenario 3: API error
        mock_get_pricing.side_effect = Exception("API call failed")
        mock_read_data.return_value = [] # Assume no previous data

        check_and_update_pricing('test_pricing.csv')

        mock_write_data.assert_not_called()
        mock_print.assert_any_call("Error fetching current pricing from API: API call failed")

if __name__ == '__main__':
    unittest.main()
