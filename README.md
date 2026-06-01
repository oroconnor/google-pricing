# Google Gemini Pricing Tracker

Tracks Gemini model pricing from the Google Cloud Billing Catalog API and calculates the cost of API requests.

## Architecture

### Shared
- `google_pricing_api.py` — fetches and filters Gemini SKUs from the Google Cloud Billing Catalog API. Used by both pipelines.
- `api_snapshot.json` — raw API snapshot for documentation and team reference.

### Pipeline 1: CSV Reference (`csv_pipeline/`)
A lightweight daily pipeline that fetches Gemini pricing and appends changes to `pricing.csv`.

- Runs as a **GitHub Action** on a daily cron schedule (6am UTC)
- Append-only CSV with full price history (`valid_from` column)
- `pricing.csv` is committed to the public repo as a stable, shareable reference

### Pipeline 2: GCP Production (`gcp_pipeline/`)
The production pipeline that writes pricing to a Postgres database and calculates API request costs.

- Designed to run as a **Cloud Run Job** triggered by **Cloud Scheduler** on GCP
- Writes parsed pricing data to a `pricing` table in Cloud SQL (Postgres)
- Reads new API request records where `cost_usd IS NULL`, calculates cost, and writes back

## Data Flow

```
Google Cloud Billing API
  └── csv_pipeline  →  pricing.csv  (public reference, GitHub)
  └── gcp_pipeline  →  pricing table (Postgres, GCP)
                    →  api_requests.cost_usd (calculated, written back to DB)
```

## Database Schema

### `pricing` table
| Column | Type | Notes |
|---|---|---|
| sku_id | VARCHAR(100) | composite PK with valid_from |
| description | VARCHAR(200) | raw description from Google API |
| valid_from | TIMESTAMP | composite PK — when this price became active |
| model | VARCHAR(50) | e.g. `Gemini 2.5 Flash` |
| direction | VARCHAR(10) | `input` or `output` |
| format | VARCHAR(20) | `text`, `audio`, `video` |
| input_token_threshold | VARCHAR(20) | `standard` (≤200K tokens) or `long` (>200K) |
| price_per_mil_tokens | NUMERIC(7,3) | |

### `api_requests` table additions
| Column | Type | Notes |
|---|---|---|
| cost_usd | NUMERIC(12,8) | calculated at write time, frozen |

## API Data Assumptions

- The Cloud Billing Catalog API requires a `parent` service argument for `list_skus()`. We first call `list_services()` and filter for services with "Vertex" in the display name, then fetch SKUs under those services.
- Gemini API token pricing lives under bare model SKUs like `Gemini 2.5 Flash Text Input - Predictions`. The `Gemini Enterprise` SKUs in the catalog are per-seat Google Workspace subscriptions and are unrelated to API costs.
- Prices are stored in the API as integer `nanos` (billionths of a dollar per token). Converting to per-million tokens is exact: `nanos / 1,000 = price_per_mil_tokens`. No precision is lost and `NUMERIC(7,3)` captures the full resolution.
- The `(Long)` suffix in a SKU description corresponds to the >200K input token pricing tier. No suffix = ≤200K tokens (standard tier).
- SKU descriptions with `Batch Predictions` are a discounted off-peak pricing tier — excluded.
- Cache storage SKUs are priced per hour (not per token) — excluded.
- Image output SKUs are excluded; all output SKUs retained are text.
- `AI Dev Tools` SKUs are from the Gemini API / Google AI Studio billing system — excluded. We use Vertex AI (`- Predictions` SKUs).
- New model versions (e.g. Gemini 3.7) are expected to follow the same description naming convention and will be picked up automatically by the existing filter logic.
