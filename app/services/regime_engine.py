# app/services/regime_engine.py

import logging
from datetime import datetime
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd

# Market data providers
try:
    import yfinance as yf
    _HAS_YFIN = True
except Exception:
    _HAS_YFIN = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Fetch OHLCV
# ---------------------------------------------------------
def _fetch_ohlcv(symbol: str, period: str = "60d", interval: str = "1d") -> Optional[pd.DataFrame]:
    try:
        if _HAS_YFIN:
            df = yf.download(symbol, period=period, interval=interval, auto_adjust=False)
            if df.empty:
                return None
            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            })
            return df[["open", "high", "low", "close", "volume"]]
        else:
            logger.warning("No market data provider")
            return None
    except Exception:
        logger.exception("Failed fetching OHLCV")
        return None

# ---------------------------------------------------------
# Indicator functions
# ---------------------------------------------------------
def average_true_range(df: pd.DataFrame, n: int = 14) -> float:
    high = df['high']
    low = df['low']
    prev_close = df['close'].shift(1).fillna(df['close'])
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().dropna().iloc[-1])

def volatility_score(df: pd.DataFrame) -> float:
    returns = df["close"].pct_change().dropna()
    return float(returns.rolling(14).std().iloc[-1]) if not returns.empty else 0.0

def momentum_score(df: pd.DataFrame, short=7, long=30) -> float:
    short_ma = df['close'].rolling(short).mean().iloc[-1]
    long_ma = df['close'].rolling(min(long, len(df))).mean().iloc[-1]
    return float((short_ma - long_ma) / long_ma) if long_ma > 0 else 0.0

def liquidity_proxy(df: pd.DataFrame) -> float:
    v = df["volume"].tail(20).mean()
    p = df["close"].iloc[-1]
    return float(v / p) if p else 0.0

# ---------------------------------------------------------
# Extra risk analytics
# ---------------------------------------------------------
from app.services.liquidity_vacuum import liquidity_vacuum_score
from app.services.market_storm import storm_probability

def _get_last_volumes(df):
    return df["volume"].tail(30).tolist()

def _get_last_prices(df):
    return df["close"].tail(30).tolist()

# ---------------------------------------------------------
# Main function: Market Weather + Vacuum + Storm
# ---------------------------------------------------------
def compute_market_weather(symbol: str, period="60d", interval="1d") -> Optional[Dict[str, Any]]:
    df = _fetch_ohlcv(symbol, period, interval)
    if df is None or df.empty:
        return None

    try:
        atr = average_true_range(df)
        vol = volatility_score(df)
        mom = momentum_score(df)
        liq = liquidity_proxy(df)
        price = float(df["close"].iloc[-1])

        # Normalization
        vol_norm = min(1.0, vol / 0.05)
        liq_norm = min(1.0, liq / 1e6)
        mom_norm = max(-1.0, min(1.0, mom * 5))

        # Base weather score
        safety_score = int(
            max(0, min(1.0,
                (1 - vol_norm) * 0.5 +
                liq_norm * 0.3 +
                (0.1 + mom_norm * 0.1)))
            * 100
        )

        # Liquidity vacuum
        vac = liquidity_vacuum_score(_get_last_volumes(df))

        # Market storm predictor
        storm = storm_probability(_get_last_prices(df))

        # Final risk score (higher = riskier)
        final_risk_score = 0.6 * (100 - safety_score) + 0.4 * (storm["storm_probability"] * 100)

        # Recommendation
        if final_risk_score > 75:
            recommendation = "avoid"
        elif final_risk_score > 55:
            recommendation = "caution"
        elif final_risk_score > 35:
            recommendation = "neutral"
        else:
            recommendation = "bullish"

        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "price": price,
            "atr": atr,
            "volatility": vol,
            "momentum": mom,
            "liquidity": liq,
            "market_weather_score": safety_score,
            "liquidity_vacuum": vac,
            "storm_probability": storm,
            "final_risk_score": final_risk_score,
            "recommendation": recommendation,
        }
    except Exception:
        logger.exception("Failed to compute market weather")
        return None

# ---------------------------------------------------------
# Regime Classification (used by regime endpoint)
# ---------------------------------------------------------
def classify_regime(symbol: str) -> Dict[str, Any]:
    """
    Lightweight wrapper for regime detection.
    Uses compute_market_weather() output.
    """
    out = compute_market_weather(symbol, period="180d", interval="1d")
    if not out:
        return {"error": "No data found"}

    vol = out.get("volatility", 0.0)
    mom = out.get("momentum", 0.0)

    # trend based on momentum
    if mom > 0.02:
        trend = "bullish"
    elif mom < -0.02:
        trend = "bearish"
    else:
        trend = "sideways"

    # volatility regimes
    if vol < 0.01:
        volatility = "low_volatility"
    elif vol < 0.025:
        volatility = "medium_volatility"
    else:
        volatility = "high_volatility"

    return {
        "symbol": symbol,
        "trend_regime": trend,
        "volatility_regime": volatility,
        "mean_return": mom,     # FIXED here
        "volatility": vol
    }
