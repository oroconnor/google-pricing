import os
from datetime import datetime
from google.cloud import billing_v1
import google.auth
from google.oauth2 import service_account

def get_gemini_pricing():
    """
    Fetches pricing data for Gemini models from the Google Cloud Billing Catalog API.
    Filters SKUs for "Gemini" in their description and extracts USD pricing.

    Returns:
        list: A list of dictionaries, each representing a Gemini SKU with its pricing.
              Example: [{'sku_id': '...', 'description': '...', 'usd_price': '...', 'last_updated': '...'}]
    """
    # Authenticate and create a client
    # Application Default Credentials (ADC) are used here, which relies on the
    # GOOGLE_APPLICATION_CREDENTIALS environment variable or gcloud CLI configuration.
    try:
        service_account_path = 'service_account.json'
        if os.path.exists(service_account_path):
            credentials = service_account.Credentials.from_service_account_file(service_account_path)
            client = billing_v1.CloudCatalogClient(credentials=credentials)
        else:
            credentials, project = google.auth.default()
            client = billing_v1.CloudCatalogClient(credentials=credentials)
    except Exception as e:
        print(f"Authentication or client creation failed: {e}")
        # In a real application, you might want to log this error and exit
        # or raise a custom exception. For now, we'll return an empty list.
        return []

    EXCLUDE = [
        'subscription',
        'cach',           # catches: caching, cached, cache storage
        'grounding',
        'tuning',
        'batch prediction',
        'image',
        'gemini enterprise',
        'gemini business',
        'priority',
        'flex',
        'embedding',
        'ai dev tools',
    ]

    gemini_skus = []

    try:
        vertex_services = [
            svc for svc in client.list_services()
            if "Vertex" in svc.display_name
        ]

        if not vertex_services:
            print("No Vertex AI service found in billing catalog.")
            return []

        for service in vertex_services:
            skus_iterator = client.list_skus(parent=service.name)
            for sku in skus_iterator:
                desc = sku.description.lower()
                if "gemini" not in desc:
                    continue
                if any(x in desc for x in EXCLUDE):
                    continue
                if sku.pricing_info:
                        expr = sku.pricing_info[0].pricing_expression
                        rates = expr.tiered_rates
                        if rates:
                            unit_price = rates[0].unit_price
                            usd_price = float(unit_price.units) + unit_price.nanos / 1e9
                            gemini_skus.append({
                                'sku_id': sku.sku_id,
                                'description': sku.description,
                                'usd_price': f"{usd_price:.9f}",
                                'valid_from': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
    except Exception as e:
        print(f"Error fetching or processing SKUs: {e}")
        return [] # Return empty list on error
        
    return gemini_skus
