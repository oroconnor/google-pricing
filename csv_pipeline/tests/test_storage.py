import unittest
import os
import csv
from datetime import datetime
from storage import read_pricing_data, write_pricing_data

class TestStorage(unittest.TestCase):
    def setUp(self):
        self.test_csv_file = 'test_pricing.csv'
        # Ensure the test CSV is clean before each test
        if os.path.exists(self.test_csv_file):
            os.remove(self.test_csv_file)

    def tearDown(self):
        # Clean up the test CSV after each test
        if os.path.exists(self.test_csv_file):
            os.remove(self.test_csv_file)

    def test_read_pricing_data_empty_or_non_existent_file(self):
        # Test case 1: File does not exist
        self.assertEqual(read_pricing_data(self.test_csv_file), [])

        # Test case 2: File exists but is empty (only headers)
        with open(self.test_csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['sku_id', 'description', 'usd_price', 'last_updated'])
        self.assertEqual(read_pricing_data(self.test_csv_file), [])

    def test_write_and_read_pricing_data(self):
        # Data to write
        data_to_write = [
            {'sku_id': 'gemini_2_5_pro', 'description': 'Gemini 2.5 Pro Model', 'usd_price': '0.001', 'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {'sku_id': 'gemini_3_0_ultra', 'description': 'Gemini 3.0 Ultra Model', 'usd_price': '0.002', 'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ]

        # Test writing data
        write_pricing_data(self.test_csv_file, data_to_write)
        self.assertTrue(os.path.exists(self.test_csv_file))

        # Test reading data back and verifying contents
        read_data = read_pricing_data(self.test_csv_file)
        self.assertEqual(len(read_data), len(data_to_write))
        
        # Convert usd_price back to string for comparison as it's stored as string in CSV
        for i in range(len(read_data)):
            # Convert read_data usd_price to float for accurate comparison, then back to string.
            # This accounts for potential float representation differences if not careful.
            # For this simple mock, direct string comparison after ensuring format is fine.
            read_data[i]['usd_price'] = str(float(read_data[i]['usd_price'])) 
            self.assertEqual(read_data[i]['sku_id'], data_to_write[i]['sku_id'])
            self.assertEqual(read_data[i]['description'], data_to_write[i]['description'])
            # Compare formatted string prices
            self.assertEqual(f"{float(read_data[i]['usd_price']):.3f}", f"{float(data_to_write[i]['usd_price']):.3f}")
            self.assertEqual(read_data[i]['last_updated'], data_to_write[i]['last_updated'])

if __name__ == '__main__':
    unittest.main()
