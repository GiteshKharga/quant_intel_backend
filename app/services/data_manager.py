
import logging
import time
import pandas as pd
import yfinance as yf
from typing import Optional

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

from app.core.decorators import robust_service
from app.core.result import Result

@robust_service(name="DataFetch")
def fetch_stock_data(symbol: str, period: str = "60d", interval: str = "1d") -> Result[pd.DataFrame]:
    """
    Robust data fetching with retries, validation, and cleaning.
    Wrapped in @robust_service for automatic error handling.
    """
    for attempt in range(MAX_RETRIES):
        try:
            # 1. Fetch Data
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            # 2. Basic Validation
            if df.empty:
                logger.warning(f"Empty data for {symbol} on attempt {attempt + 1}")
                continue
                
            # 3. Standardization
            df.columns = df.columns.str.lower()
            required_cols = ["open", "high", "low", "close", "volume"]
            
            # Check if all required columns exist
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Missing columns for {symbol}: {df.columns}")
                continue

            # Rename adjust close/splits if present, for safety
            rename_map = {
                "adj close": "adj_close",
                "stock splits": "stock_splits"
            }
            df = df.rename(columns=rename_map)
            
            # 4. Filter and Clean
            df = df[[c for c in df.columns if c in required_cols or c in rename_map.values()]]
            
            # Handle missing values (simple interpolation)
            if df[required_cols].isnull().values.any():
                df[required_cols] = df[required_cols].interpolate(method='linear').ffill().bfill()
            
            # 5. Zero Volume Check (Warning only, as some assets might be illiquid)
            if (df['volume'] == 0).all():
                logger.warning(f"Symbol {symbol} has ZERO volume for all records")
                
            return Result.Ok(df)

        except Exception as e:
            logger.error(f"Error fetching data for {symbol} (Attempt {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    
    return Result.Fail(f"Failed to fetch data for {symbol} after {MAX_RETRIES} attempts")

