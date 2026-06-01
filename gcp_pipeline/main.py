"""
GCP Production Pipeline entry point.
Designed to run as a Cloud Run Job triggered by Cloud Scheduler.

Steps:
  1. Fetch current Gemini pricing from Google Cloud Billing API
  2. Parse and upsert into the Postgres pricing table
  3. Find api_request records where cost_usd IS NULL
  4. Calculate cost using point-in-time price lookup
  5. Write cost_usd back to api_requests
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

import psycopg2
from google_pricing_api import get_gemini_pricing
from pricing_db import upsert_pricing


def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])


def main():
    print("=== Step 1: Fetch pricing from Google Billing API ===")
    skus = get_gemini_pricing()
    if not skus:
        print("No pricing data returned. Exiting.")
        return
    print(f"Fetched {len(skus)} SKUs.")

    print("\n=== Step 2: Upsert into Postgres pricing table ===")
    conn = get_db_connection()
    try:
        inserted = upsert_pricing(conn, skus)
        print(f"Inserted {inserted} new/changed row(s).")
    finally:
        conn.close()

    # Steps 3-5: cost calculation (coming soon)


if __name__ == '__main__':
    main()
