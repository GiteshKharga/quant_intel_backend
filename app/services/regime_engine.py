# app/services/regime_engine.py

import logging
from datetime import datetime
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Reuse the working fetch function from market_weather
from app.services.market_weather import _fetch_ohlcv

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
# Main function
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

        vol_norm = min(1.0, vol / 0.05)
        liq_norm = min(1.0, liq / 1e6)
        mom_norm = max(-1.0, min(1.0, mom * 5))

        # base weather score
        safety_score = int(
            max(0, min(1.0,
                (1 - vol_norm) * 0.5 +
                liq_norm * 0.3 +
                (0.1 + mom_norm * 0.1)))
            * 100
        )

        # -------------------------------------
        # Liquidity Vacuum & Storm Risk
        # -------------------------------------
        vac = liquidity_vacuum_score(_get_last_volumes(df))
        storm = storm_probability(_get_last_prices(df))

        final_risk_score = 0.6 * (100 - safety_score) + 0.4 * (storm["storm_probability"] * 100)

        # recommendation logic
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
# Regime Classification (wrapper for API)
# ---------------------------------------------------------
def classify_regime(symbol: str, period: str = "60d", interval: str = "1d") -> Optional[Dict[str, Any]]:
    """
    Classify market regime based on weather metrics.
    Returns regime type: trending_up, trending_down, ranging, volatile
    """
    weather = compute_market_weather(symbol, period, interval)
    if weather is None:
        return None
    
    try:
        momentum = weather.get("momentum", 0)
        volatility = weather.get("volatility", 0)
        safety_score = weather.get("market_weather_score", 50)
        final_risk = weather.get("final_risk_score", 50)
        
        # Regime classification logic
        if volatility > 0.03:
            regime = "volatile"
        elif momentum > 0.02:
            regime = "trending_up"
        elif momentum < -0.02:
            regime = "trending_down"
        else:
            regime = "ranging"
        
        return {
            "symbol": symbol,
            "timestamp": weather.get("timestamp"),
            "price": weather.get("price"),
            "regime": regime,
            "momentum": momentum,
            "volatility": volatility,
            "safety_score": safety_score,
            "final_risk_score": final_risk,
            "recommendation": weather.get("recommendation"),
            "details": {
                "atr": weather.get("atr"),
                "liquidity": weather.get("liquidity"),
                "liquidity_vacuum": weather.get("liquidity_vacuum"),
                "storm_probability": weather.get("storm_probability"),
            }
        }
    except Exception:
        logger.exception("Failed to classify regime for %s", symbol)
        return None
