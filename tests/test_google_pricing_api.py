import unittest
from unittest.mock import patch, MagicMock
import os
from google_pricing_api import get_gemini_pricing

class TestGooglePricingApi(unittest.TestCase):
    @patch('google_pricing_api.billing_v1.CloudCatalogClient')
    @patch('google_pricing_api.google.auth.default')
    def test_get_gemini_pricing_no_service_account(self, mock_auth_default, mock_client):
        # This test ensures that the original authentication method (google.auth.default) is used
        # when the service_account.json file is not present.
        with patch('os.path.exists', return_value=False):
            # Mock authentication
            mock_credentials = MagicMock()
            mock_auth_default.return_value = (mock_credentials, 'test-project-id')

            # Mock the CloudCatalogClient and its list_skus method
            mock_client_instance = mock_client.return_value
            
            # Create mock SKU objects
            mock_sku_gemini_2_5 = MagicMock()
            mock_sku_gemini_2_5.sku_id = 'test-gemini-2-5-sku'
            mock_sku_gemini_2_5.description = 'Google Gemini 2.5 Pro Model'
            mock_sku_gemini_2_5.pricing_info = [MagicMock()]
            mock_sku_gemini_2_5.pricing_info[0].pricing_expression.retail_price = MagicMock(units=0, nanos=1000000) # $0.001

            mock_client_instance.list_skus.return_value = [mock_sku_gemini_2_5]

            # Call the function under test
            gemini_pricing_data = get_gemini_pricing()

            # Assertions
            self.assertEqual(len(gemini_pricing_data), 1)
            self.assertEqual(gemini_pricing_data[0]['sku_id'], 'test-gemini-2-5-sku')
            mock_auth_default.assert_called_once()
            mock_client.assert_called_once_with(credentials=mock_credentials)

    @patch('google_pricing_api.billing_v1.CloudCatalogClient')
    @patch('google_pricing_api.service_account.Credentials.from_service_account_file')
    @patch('os.path.exists', return_value=True)
    def test_get_gemini_pricing_with_service_account(self, mock_os_exists, mock_from_service_account_file, mock_client):
        # This test ensures that the service account file is used for authentication when present.
        
        # Mock service account credentials
        mock_credentials = MagicMock()
        mock_from_service_account_file.return_value = mock_credentials

        # Mock the CloudCatalogClient and its list_skus method
        mock_client_instance = mock_client.return_value
        
        # Create mock SKU objects
        mock_sku_gemini_3_0 = MagicMock()
        mock_sku_gemini_3_0.sku_id = 'test-gemini-3-0-sku'
        mock_sku_gemini_3_0.description = 'Google Gemini 3.0 Ultra Model'
        mock_sku_gemini_3_0.pricing_info = [MagicMock()]
        mock_sku_gemini_3_0.pricing_info[0].pricing_expression.retail_price = MagicMock(units=0, nanos=2000000) # $0.002

        mock_client_instance.list_skus.return_value = [mock_sku_gemini_3_0]

        # Call the function under test
        gemini_pricing_data = get_gemini_pricing()

        # Assertions
        self.assertEqual(len(gemini_pricing_data), 1)
        self.assertEqual(gemini_pricing_data[0]['sku_id'], 'test-gemini-3-0-sku')
        
        # Verify that the service account file was used
        mock_os_exists.assert_called_once_with('service_account.json')
        mock_from_service_account_file.assert_called_once_with('service_account.json')
        mock_client.assert_called_once_with(credentials=mock_credentials)
        
        # Ensure the fallback authentication was not used
        with patch('google_pricing_api.google.auth.default') as mock_auth_default:
            get_gemini_pricing()
            mock_auth_default.assert_not_called()


if __name__ == '__main__':
    unittest.main()
