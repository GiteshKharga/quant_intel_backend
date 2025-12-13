# app/services/intraday_regime.py
"""
INTRADAY REGIME SWITCHING DETECTION
===================================
Detects different market regimes during trading hours:
- Opening volatility burst (9:15-9:45)
- Morning momentum (9:45-11:30)
- Lunch lull (11:30-13:30)
- Afternoon reversal zone (13:30-14:30)
- Power hour (14:30-15:15)
- Closing auction games (15:15-15:30)

Novel approach: Time-weighted regime detection with transition probabilities.
"""

import logging
from datetime import datetime, time
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

from app.services.market_weather import _fetch_ohlcv


# Define trading regimes for Indian markets (IST)
INTRADAY_REGIMES = {
    "opening_burst": {
        "start": time(9, 15),
        "end": time(9, 45),
        "characteristics": "High volatility, gap fills, fake breakouts",
        "strategy": "Wait for confirmation, avoid first 15 mins"
    },
    "morning_momentum": {
        "start": time(9, 45),
        "end": time(11, 30),
        "characteristics": "Trend establishment, institutional activity",
        "strategy": "Trade with trend, use momentum indicators"
    },
    "lunch_lull": {
        "start": time(11, 30),
        "end": time(13, 30),
        "characteristics": "Low volume, range-bound, choppy",
        "strategy": "Avoid trading or use mean reversion"
    },
    "afternoon_reversal": {
        "start": time(13, 30),
        "end": time(14, 30),
        "characteristics": "Potential trend reversals, profit booking",
        "strategy": "Watch for reversal signals, tighten stops"
    },
    "power_hour": {
        "start": time(14, 30),
        "end": time(15, 15),
        "characteristics": "Volume surge, strong moves",
        "strategy": "Trade breakouts, follow smart money"
    },
    "closing_auction": {
        "start": time(15, 15),
        "end": time(15, 30),
        "characteristics": "Index rebalancing, window dressing",
        "strategy": "Avoid new positions, close intraday trades"
    }
}


def get_current_regime(current_time: time = None) -> Dict[str, Any]:
    """
    Determine current intraday regime based on time.
    """
    if current_time is None:
        current_time = datetime.now().time()
    
    for regime_name, regime_info in INTRADAY_REGIMES.items():
        if regime_info["start"] <= current_time < regime_info["end"]:
            return {
                "regime": regime_name,
                **regime_info
            }
    
    return {
        "regime": "market_closed",
        "characteristics": "Market is closed",
        "strategy": "Plan for next session"
    }


def calculate_regime_metrics(df: pd.DataFrame, regime: str) -> Dict[str, float]:
    """
    Calculate performance metrics for a specific regime using historical data.
    """
    metrics = {
        "avg_volatility": 0.0,
        "avg_volume_ratio": 1.0,
        "trend_strength": 0.0,
        "reversal_probability": 0.0
    }
    
    if df.empty or len(df) < 2:
        return metrics
    
    returns = df['close'].pct_change().dropna()
    
    if not returns.empty:
        metrics["avg_volatility"] = float(returns.std() * 100)  # Percentage
        metrics["trend_strength"] = float(abs(returns.mean() / (returns.std() + 0.0001)))
        
        # Reversal probability: how often does direction change?
        directions = np.sign(returns.values)
        changes = np.sum(np.abs(np.diff(directions)) > 0)
        metrics["reversal_probability"] = float(changes / len(directions)) if len(directions) > 1 else 0.0
    
    # Volume ratio compared to daily average
    if 'volume' in df.columns and df['volume'].mean() > 0:
        current_vol = df['volume'].iloc[-1]
        avg_vol = df['volume'].mean()
        metrics["avg_volume_ratio"] = float(current_vol / avg_vol)
    
    return metrics


def calculate_regime_transition_matrix(
    historical_regimes: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate transition probabilities between regimes.
    This is useful for predicting what comes next.
    """
    transitions = {}
    
    for i in range(len(historical_regimes) - 1):
        current = historical_regimes[i]
        next_regime = historical_regimes[i + 1]
        
        if current not in transitions:
            transitions[current] = {}
        if next_regime not in transitions[current]:
            transitions[current][next_regime] = 0
        
        transitions[current][next_regime] += 1
    
    # Normalize to probabilities
    for regime, next_regimes in transitions.items():
        total = sum(next_regimes.values())
        if total > 0:
            for next_r in next_regimes:
                next_regimes[next_r] /= total
    
    return transitions


def detect_intraday_regime(
    symbol: str,
    period: str = "5d",
    interval: str = "5m"
) -> Optional[Dict[str, Any]]:
    """
    Main function to detect current intraday regime and provide predictions.
    """
    df = _fetch_ohlcv(symbol, period=period, interval=interval)
    if df is None or df.empty:
        return None
    
    try:
        current_time = datetime.now().time()
        current_regime_info = get_current_regime(current_time)
        
        # Calculate metrics for current period
        current_metrics = calculate_regime_metrics(df, current_regime_info["regime"])
        
        # Calculate overall session characteristics
        today_data = df.tail(78)  # Approx bars for one day at 5min
        
        if not today_data.empty:
            session_high = float(today_data['high'].max())
            session_low = float(today_data['low'].min())
            session_range = session_high - session_low
            current_price = float(today_data['close'].iloc[-1])
            
            # Position within day's range
            if session_range > 0:
                range_position = (current_price - session_low) / session_range
            else:
                range_position = 0.5
        else:
            session_high = session_low = current_price = 0
            range_position = 0.5
        
        # Determine regime strength
        vol_ratio = current_metrics["avg_volume_ratio"]
        volatility = current_metrics["avg_volatility"]
        
        if vol_ratio > 1.5 and volatility > 1.0:
            regime_strength = "STRONG"
        elif vol_ratio < 0.5 or volatility < 0.3:
            regime_strength = "WEAK"
        else:
            regime_strength = "NORMAL"
        
        # Next regime prediction
        ordered_regimes = list(INTRADAY_REGIMES.keys())
        current_idx = ordered_regimes.index(current_regime_info["regime"]) \
                      if current_regime_info["regime"] in ordered_regimes else -1
        
        if current_idx >= 0 and current_idx < len(ordered_regimes) - 1:
            next_regime = ordered_regimes[current_idx + 1]
            next_regime_info = INTRADAY_REGIMES[next_regime]
        else:
            next_regime = "market_closed"
            next_regime_info = {"strategy": "Session ended"}
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "current_time_ist": current_time.strftime("%H:%M:%S"),
            "price": current_price,
            
            # Current regime
            "current_regime": {
                "name": current_regime_info["regime"],
                "characteristics": current_regime_info.get("characteristics", ""),
                "recommended_strategy": current_regime_info.get("strategy", ""),
                "strength": regime_strength,
            },
            
            # Metrics
            "metrics": current_metrics,
            
            # Session context
            "session": {
                "high": session_high,
                "low": session_low,
                "range": session_range,
                "range_position": float(range_position),
                "range_description": "Near highs" if range_position > 0.7 else \
                                   "Near lows" if range_position < 0.3 else "Mid-range"
            },
            
            # Prediction
            "next_regime": {
                "name": next_regime,
                "expected_change": next_regime_info.get("strategy", ""),
            },
            
            "algorithm_version": "1.0.0"
        }
        
    except Exception:
        logger.exception("Failed to detect intraday regime for %s", symbol)
        return None
