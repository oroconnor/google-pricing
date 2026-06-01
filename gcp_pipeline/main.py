"""
GCP Production Pipeline entry point.
Deployed as a Cloud Function (Gen 2), triggered daily by Cloud Scheduler.

Steps:
  1. Fetch current Gemini pricing from Google Cloud Billing API
  2. Parse and upsert into the Postgres pricing table
  3. Find api_request records where cost_usd IS NULL
  4. Calculate cost using point-in-time price lookup
  5. Write cost_usd back to api_requests
"""
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

import functions_framework
import psycopg2
from google.cloud.sql.connector import Connector
from google_pricing_api import get_gemini_pricing
from pricing_db import upsert_pricing


def get_db_connection():
    instance = os.environ.get('INSTANCE_CONNECTION_NAME')
    if instance:
        # Production: Cloud SQL Python Connector (no socket mounting needed)
        connector = Connector()
        return connector.connect(
            instance,
            "pg8000",
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASS'],
            db=os.environ['DB_NAME'],
        )
    # Local dev: direct connection via DATABASE_URL
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


@functions_framework.http
def run_pricing_update(request):
    """Cloud Functions entry point. Triggered by Cloud Scheduler via HTTP."""
    main()
    return 'OK', 200


if __name__ == '__main__':
    main()
