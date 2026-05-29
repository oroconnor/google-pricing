This project is to create a recurring process that pulls pricing data from Google's Pricing API for specific SKUs, and updates a table on a database if there are changes. 

The process should run daily, at 6am. 

We are looking to pull the pricing data for Gemini 2.5 and 3 models, such as shown here:
https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing
We do not need pricing for cached tokens, or for pricing that is not on the standard list (priority or flex/batched requests). 

## API Data Assumptions

- The Cloud Billing Catalog API requires a `parent` service argument for `list_skus()`. We first call `list_services()` and filter for services with "Vertex" in the display name, then fetch SKUs under those services.
- Gemini API token pricing lives under bare model SKUs like `Gemini 2.5 Flash Text Input - Predictions`. The `Gemini Enterprise` SKUs in the catalog are per-seat Google Workspace subscriptions and are unrelated to API costs.
- Prices are stored in the API as integer `nanos` (billionths of a dollar per token). Converting to per-million tokens is exact: `nanos / 1,000 = price_per_mil_tokens`. No precision is lost and `NUMERIC(7,3)` captures the full resolution.
- The `(Long)` suffix in a SKU description corresponds to the >200K input token pricing tier on the pricing page. No suffix = ≤200K tokens (standard tier).
- SKU descriptions with `Batch Predictions` are a discounted off-peak pricing tier, not standard on-demand pricing — excluded.
- Cache storage SKUs are priced per hour (not per token) and do not fit the `price_per_mil_tokens` schema — excluded.
- Image output SKUs are excluded; all output SKUs retained are text.
- New model versions (e.g. Gemini 3.7) are expected to follow the same description naming convention and will be picked up automatically by the existing filter logic.

