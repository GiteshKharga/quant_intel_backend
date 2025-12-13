# app/services/liquidity_drought.py
"""
LIQUIDITY DROUGHT PREDICTION
============================
Novel algorithm to predict when a stock is about to become illiquid.
Uses multiple signals including volume patterns, volatility clustering,
and bid-ask proxy estimation.

Potential Patent Claim: Method for predicting liquidity drought events
in financial instruments using multi-factor temporal analysis.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Reuse fetch function
from app.services.market_weather import _fetch_ohlcv


def calculate_volume_decay_rate(volumes: List[float], window: int = 10) -> float:
    """
    Calculate the rate at which volume is decaying.
    Higher values indicate faster liquidity drain.
    """
    if len(volumes) < window:
        return 0.0
    
    recent = volumes[-window:]
    if len(recent) < 2:
        return 0.0
    
    # Calculate exponential decay coefficient
    x = np.arange(len(recent))
    y = np.log(np.array(recent) + 1)  # +1 to avoid log(0)
    
    # Linear regression on log values = exponential decay
    if np.std(x) == 0:
        return 0.0
    
    slope = np.corrcoef(x, y)[0, 1] * np.std(y) / np.std(x)
    return float(-slope)  # Negative slope = positive decay


def calculate_volume_concentration(df: pd.DataFrame, window: int = 20) -> float:
    """
    Calculate how concentrated volume is in few bars.
    High concentration = liquidity bursts, not steady flow.
    """
    volumes = df['volume'].tail(window).values
    if len(volumes) == 0 or volumes.sum() == 0:
        return 0.0
    
    # Gini coefficient for volume distribution
    sorted_v = np.sort(volumes)
    n = len(sorted_v)
    cumulative = np.cumsum(sorted_v)
    gini = (2 * np.sum((np.arange(1, n+1) * sorted_v))) / (n * np.sum(sorted_v)) - (n + 1) / n
    
    return float(max(0, min(1, gini)))


def calculate_volatility_volume_ratio(df: pd.DataFrame, window: int = 14) -> float:
    """
    High volatility with low volume = dangerous illiquidity.
    """
    if len(df) < window:
        return 0.0
    
    recent = df.tail(window)
    returns = recent['close'].pct_change().dropna()
    
    if returns.empty:
        return 0.0
    
    volatility = returns.std()
    avg_volume = recent['volume'].mean()
    
    if avg_volume == 0:
        return 1.0  # Maximum danger
    
    # Normalize: high volatility / low volume = high ratio
    price = recent['close'].iloc[-1]
    normalized_volume = avg_volume / price if price > 0 else avg_volume
    
    return float(min(1.0, volatility / (normalized_volume / 1e6 + 0.001)))


def calculate_price_gap_frequency(df: pd.DataFrame, threshold: float = 0.02) -> float:
    """
    Frequent price gaps indicate thin order books.
    """
    if len(df) < 2:
        return 0.0
    
    opens = df['open'].values[1:]
    prev_closes = df['close'].values[:-1]
    
    gaps = np.abs(opens - prev_closes) / (prev_closes + 0.001)
    gap_count = np.sum(gaps > threshold)
    
    return float(gap_count / len(gaps)) if len(gaps) > 0 else 0.0


def calculate_spread_proxy(df: pd.DataFrame, window: int = 14) -> float:
    """
    Estimate bid-ask spread using high-low range.
    Larger spread = lower liquidity.
    """
    if len(df) < window:
        return 0.0
    
    recent = df.tail(window)
    
    # Use high-low as spread proxy
    spreads = (recent['high'] - recent['low']) / recent['close']
    avg_spread = spreads.mean()
    
    return float(avg_spread)


from app.core.decorators import robust_service
from app.core.result import Result

@robust_service(name="LiquidityDrought")
def predict_liquidity_drought(
    symbol: str, 
    period: str = "60d", 
    interval: str = "1d"
) -> Result[Dict[str, Any]]:
    """
    Main prediction function for Liquidity Drought.
    
    Returns a comprehensive liquidity assessment with drought probability.
    """
    df = _fetch_ohlcv(symbol, period=period, interval=interval)
    if df is None or df.empty:
        return Result.Fail("Missing data")
    
    volumes = df['volume'].tolist()
    
    # Calculate all components
    decay_rate = calculate_volume_decay_rate(volumes)
    concentration = calculate_volume_concentration(df)
    vol_ratio = calculate_volatility_volume_ratio(df)
    gap_freq = calculate_price_gap_frequency(df)
    spread_proxy = calculate_spread_proxy(df)
    
    # Normalize spread (typical spread is 0.01-0.05)
    spread_norm = min(1.0, spread_proxy / 0.05)
    
    # Weighted drought probability score
    drought_probability = (
        decay_rate * 0.25 +           # Volume drying up
        concentration * 0.15 +         # Volume concentrated
        vol_ratio * 0.25 +             # High vol, low volume
        gap_freq * 0.20 +              # Frequent gaps
        spread_norm * 0.15             # Wide spreads
    )
    
    drought_probability = float(max(0, min(1, drought_probability)))
    
    # Risk categorization
    if drought_probability > 0.7:
        risk_level = "CRITICAL"
        alert = "High probability of liquidity drought - avoid large orders"
    elif drought_probability > 0.5:
        risk_level = "HIGH"
        alert = "Elevated illiquidity risk - use limit orders only"
    elif drought_probability > 0.3:
        risk_level = "MODERATE"
        alert = "Some liquidity concerns - monitor order execution"
    else:
        risk_level = "LOW"
        alert = "Normal liquidity conditions"
    
    # Calculate trend
    recent_avg_vol = df['volume'].tail(5).mean()
    older_avg_vol = df['volume'].tail(20).head(15).mean()
    volume_trend = "DECLINING" if recent_avg_vol < older_avg_vol * 0.7 else \
                   "INCREASING" if recent_avg_vol > older_avg_vol * 1.3 else "STABLE"
    
    return Result.Ok({
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "price": float(df['close'].iloc[-1]),
        
        # Main prediction
        "drought_probability": drought_probability,
        "risk_level": risk_level,
        "alert": alert,
        
        # Component scores
        "components": {
            "volume_decay_rate": decay_rate,
            "volume_concentration": concentration,
            "volatility_volume_ratio": vol_ratio,
            "gap_frequency": gap_freq,
            "spread_proxy": spread_proxy,
        },
        
        # Additional context
        "volume_trend": volume_trend,
        "current_volume": int(df['volume'].iloc[-1]),
        "avg_volume_20d": int(df['volume'].tail(20).mean()),
        
        # For patent documentation
        "algorithm_version": "1.0.0",
        "methodology": "Multi-factor temporal liquidity analysis"
    })

