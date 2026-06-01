"""
Handles parsing SKU descriptions into structured fields and
upserting into the Postgres pricing table.
"""
import re
from datetime import datetime


def parse_sku(sku):
    """
    Parse a raw SKU dict (from get_gemini_pricing) into structured fields
    for the pricing table.

    Returns a dict with: sku_id, description, valid_from, model, direction,
    format, input_token_threshold, price_per_mil_tokens
    """
    desc = sku['description'].strip()
    raw = desc  # preserve original

    # Remove " - Predictions" suffix
    desc = re.sub(r'\s*-\s*Predictions$', '', desc)

    # Detect threshold from parenthetical modifiers before stripping them
    thinking = '(Thinking On' in desc          # catches (Thinking On) and (Thinking On and Long)
    long_ctx = '(Long)' in desc or '(Thinking On and Long)' in desc

    # "Thinking" as a bare word in the name (e.g. "Thinking Text Output") also means thinking mode
    thinking = thinking or bool(re.search(r'\bThinking\b', desc))

    if thinking and long_ctx:
        threshold = 'thinking_long'
    elif thinking:
        threshold = 'thinking'
    elif long_ctx:
        threshold = 'long'
    else:
        threshold = 'standard'

    # Strip all parenthetical content (modifiers, codec names like AV2A)
    desc = re.sub(r'\s*\([^)]+\)', '', desc).strip()

    # Strip "Thinking" word now that it's captured in threshold
    desc = re.sub(r'\bThinking\b', '', desc).strip()

    # Detect direction
    if re.search(r'\bOutput\b', desc):
        direction = 'output'
        desc = re.sub(r'\bOutput\b', '', desc).strip()
    elif re.search(r'\bInput\b', desc):
        direction = 'input'
        desc = re.sub(r'\bInput\b', '', desc).strip()
    else:
        direction = None

    # Detect format (order matters — check before stripping)
    format_ = None
    for word, fmt in [('Audio', 'audio'), ('Video', 'video'), ('Text', 'text'), ('Image', 'image')]:
        if re.search(rf'\b{word}\b', desc):
            format_ = fmt
            desc = re.sub(rf'\b{word}\b', '', desc).strip()
            break

    # Strip routing/release markers — not model-defining, prices are the same
    for marker in ['GA', 'Global', 'Regional']:
        desc = re.sub(rf'\b{marker}\b', '', desc).strip()

    model = re.sub(r'\s+', ' ', desc).strip()

    # price_per_mil_tokens: CSV stores raw per-token price, multiply by 1M
    price_per_mil = round(float(sku['usd_price']) * 1_000_000, 3)

    return {
        'sku_id': sku['sku_id'],
        'description': raw,
        'valid_from': sku['valid_from'],
        'model': model,
        'direction': direction,
        'format': format_,
        'input_token_threshold': threshold,
        'price_per_mil_tokens': price_per_mil,
    }


def get_latest_prices(conn):
    """
    Returns a dict of {sku_id: price_per_mil_tokens} for the most recent
    row per SKU currently in the pricing table.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (sku_id) sku_id, price_per_mil_tokens
            FROM pricing
            ORDER BY sku_id, valid_from DESC
        """)
        return {row[0]: float(row[1]) for row in cur.fetchall()}


def upsert_pricing(conn, skus):
    """
    Compares freshly fetched SKUs against the latest prices in the DB.
    Inserts a new row only when a price has changed or is new.
    Existing rows are never modified — history is preserved.
    """
    latest = get_latest_prices(conn)
    rows_inserted = 0

    with conn.cursor() as cur:
        for sku in skus:
            parsed = parse_sku(sku)
            sku_id = parsed['sku_id']
            new_price = parsed['price_per_mil_tokens']

            if sku_id in latest and latest[sku_id] == new_price:
                continue  # no change

            if sku_id not in latest:
                print(f"New SKU:      {parsed['description'][:60]} @ {new_price}")
            else:
                print(f"Price change: {parsed['description'][:60]} "
                      f"{latest[sku_id]} -> {new_price}")

            cur.execute("""
                INSERT INTO pricing
                    (sku_id, description, valid_from, model, direction,
                     format, input_token_threshold, price_per_mil_tokens)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sku_id, valid_from) DO NOTHING
            """, (
                parsed['sku_id'],
                parsed['description'],
                parsed['valid_from'],
                parsed['model'],
                parsed['direction'],
                parsed['format'],
                parsed['input_token_threshold'],
                parsed['price_per_mil_tokens'],
            ))
            rows_inserted += 1

    conn.commit()
    return rows_inserted
