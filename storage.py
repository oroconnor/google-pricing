import csv
import os

FIELDNAMES = ['sku_id', 'description', 'usd_price', 'valid_from']

def read_pricing_data(file_path):
    """
    Returns the most recent row per sku_id — used to compare against fresh API data.
    """
    if not os.path.exists(file_path):
        return []

    rows = []
    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        for row in csv.DictReader(csvfile):
            rows.append(row)

    latest = {}
    for row in rows:
        sku_id = row['sku_id']
        if sku_id not in latest or row['valid_from'] > latest[sku_id]['valid_from']:
            latest[sku_id] = row

    return list(latest.values())


def append_pricing_data(file_path, rows):
    """
    Appends changed/new rows to the CSV. Creates the file with headers on first run.
    Existing rows are never modified — history is preserved.
    """
    file_exists = os.path.exists(file_path) and os.path.getsize(file_path) > 0

    with open(file_path, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
