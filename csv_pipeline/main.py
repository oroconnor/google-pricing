import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_pricing_api import get_gemini_pricing
from storage import read_pricing_data, append_pricing_data

PRICING_CSV_FILE = 'pricing.csv'

def check_and_update_pricing(pricing_csv_file=PRICING_CSV_FILE):
    print("Starting pricing update check...")

    try:
        current_prices = get_gemini_pricing()
        if not current_prices:
            print("No Gemini pricing data fetched from API or an error occurred. Exiting.")
            return
    except Exception as e:
        print(f"Error fetching current pricing from API: {e}")
        return

    last_known_prices = read_pricing_data(pricing_csv_file)
    current_dict = {item['sku_id']: item for item in current_prices}
    last_dict = {item['sku_id']: item for item in last_known_prices}

    rows_to_append = []

    for sku_id, current in current_dict.items():
        if sku_id not in last_dict:
            print(f"New SKU: {current['description']} @ {current['usd_price']}")
            rows_to_append.append(current)
        elif current['usd_price'] != last_dict[sku_id]['usd_price']:
            print(f"Price change: {current['description']} "
                  f"{last_dict[sku_id]['usd_price']} -> {current['usd_price']}")
            rows_to_append.append(current)

    for sku_id, last in last_dict.items():
        if sku_id not in current_dict:
            print(f"SKU removed: {last['description']}")

    if rows_to_append:
        append_pricing_data(pricing_csv_file, rows_to_append)
        print(f"Appended {len(rows_to_append)} row(s). Update complete.")
    else:
        print("No pricing changes detected.")

if __name__ == '__main__':
    check_and_update_pricing()
