"""
Calculates cost_usd for api_request records where cost_usd IS NULL.
Joins request timestamp to pricing history for point-in-time price lookup.
Writes cost_usd back to the api_requests table.
"""
