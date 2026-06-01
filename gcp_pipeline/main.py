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
