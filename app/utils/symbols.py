# app/utils/symbols.py
# Maintain a controlled whitelist for production.
# Seed this DB or maintain a JSON file that maps allowed tickers.
ALLOWED_SYMBOLS = set([
    "AAPL", "MSFT", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"
    # extend this list: ideally load from DB or S3 in production
])

def is_symbol_allowed(symbol: str) -> bool:
    if not symbol:
        return False
    return symbol.upper() in ALLOWED_SYMBOLS
