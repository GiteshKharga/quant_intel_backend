# app/services/sentiment_velocity.py
"""
SOCIAL SENTIMENT VELOCITY
=========================
Not just sentiment positive/negative, but HOW FAST sentiment is changing.
A stock going from neutral → positive slowly is different from sudden spike.

Novel approach: Rate of change of sentiment with acceleration detection.
Potential for manipulation detection via sudden sentiment spikes.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_sentiment_velocity(
    sentiment_scores: List[float],
    timestamps: List[datetime] = None
) -> Dict[str, float]:
    """
    Calculate velocity (rate of change) and acceleration of sentiment.
    
    Args:
        sentiment_scores: List of sentiment scores (-1 to 1)
        timestamps: Optional list of timestamps for each score
    
    Returns:
        velocity: How fast sentiment is changing
        acceleration: Rate of change of velocity
        volatility: How unstable the sentiment is
    """
    if len(sentiment_scores) < 3:
        return {
            "velocity": 0.0,
            "acceleration": 0.0,
            "volatility": 0.0
        }
    
    scores = np.array(sentiment_scores)
    
    # First derivative (velocity)
    velocity = np.diff(scores)
    current_velocity = float(velocity[-1])
    avg_velocity = float(np.mean(velocity))
    
    # Second derivative (acceleration)
    acceleration = np.diff(velocity)
    current_acceleration = float(acceleration[-1]) if len(acceleration) > 0 else 0.0
    
    # Volatility (standard deviation of changes)
    volatility = float(np.std(velocity))
    
    return {
        "velocity": current_velocity,
        "avg_velocity": avg_velocity,
        "acceleration": current_acceleration,
        "volatility": volatility
    }


def detect_sentiment_anomaly(
    sentiment_scores: List[float],
    threshold_std: float = 2.0
) -> Dict[str, Any]:
    """
    Detect anomalous sentiment changes that could indicate manipulation.
    """
    if len(sentiment_scores) < 10:
        return {
            "is_anomalous": False,
            "anomaly_score": 0.0,
            "reason": "Insufficient data"
        }
    
    scores = np.array(sentiment_scores)
    changes = np.diff(scores)
    
    mean_change = np.mean(changes)
    std_change = np.std(changes)
    
    if std_change == 0:
        return {
            "is_anomalous": False,
            "anomaly_score": 0.0,
            "reason": "No variation"
        }
    
    # Z-score of latest change
    latest_change = changes[-1]
    z_score = (latest_change - mean_change) / std_change
    
    is_anomalous = abs(z_score) > threshold_std
    
    if is_anomalous:
        if z_score > 0:
            reason = f"Sudden positive sentiment spike (z={z_score:.2f})"
        else:
            reason = f"Sudden negative sentiment drop (z={z_score:.2f})"
    else:
        reason = "Normal sentiment change"
    
    return {
        "is_anomalous": is_anomalous,
        "anomaly_score": float(abs(z_score) / threshold_std),
        "z_score": float(z_score),
        "reason": reason
    }


def simulate_sentiment_data(symbol: str, days: int = 30) -> List[Dict[str, Any]]:
    """
    Simulate sentiment data (in production, this would come from 
    Twitter API, Reddit API, news sources, etc.)
    
    Uses price action as a proxy for sentiment.
    """
    from app.services.market_weather import _fetch_ohlcv
    
    df = _fetch_ohlcv(symbol, period=f"{days}d", interval="1d")
    if df is None or df.empty:
        return []
    
    sentiment_data = []
    
    for idx, row in df.iterrows():
        # Use returns as sentiment proxy
        if len(sentiment_data) > 0:
            prev_close = sentiment_data[-1].get("price", row['close'])
            ret = (row['close'] - prev_close) / prev_close
            
            # Convert return to sentiment (-1 to 1)
            sentiment = np.tanh(ret * 50)  # Scale and bound
            
            # Add some noise for realism
            sentiment += np.random.normal(0, 0.1)
            sentiment = max(-1, min(1, sentiment))
        else:
            sentiment = 0.0
        
        sentiment_data.append({
            "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
            "sentiment": float(sentiment),
            "price": float(row['close']),
            "volume": int(row['volume'])
        })
    
    return sentiment_data


def analyze_sentiment_velocity(
    symbol: str,
    days: int = 30
) -> Optional[Dict[str, Any]]:
    """
    Main function to analyze sentiment velocity for a symbol.
    """
    try:
        # Get sentiment data (simulated from price in this version)
        sentiment_data = simulate_sentiment_data(symbol, days)
        
        if len(sentiment_data) < 5:
            return None
        
        scores = [d["sentiment"] for d in sentiment_data]
        
        # Calculate velocity metrics
        velocity_metrics = calculate_sentiment_velocity(scores)
        
        # Detect anomalies
        anomaly_info = detect_sentiment_anomaly(scores)
        
        # Current sentiment state
        current_sentiment = scores[-1]
        if current_sentiment > 0.3:
            sentiment_state = "BULLISH"
        elif current_sentiment < -0.3:
            sentiment_state = "BEARISH"
        else:
            sentiment_state = "NEUTRAL"
        
        # Velocity interpretation
        velocity = velocity_metrics["velocity"]
        if velocity > 0.1:
            velocity_state = "ACCELERATING_POSITIVE"
            interpretation = "Sentiment improving rapidly - potential trend"
        elif velocity < -0.1:
            velocity_state = "ACCELERATING_NEGATIVE"
            interpretation = "Sentiment deteriorating - caution advised"
        elif abs(velocity) < 0.02:
            velocity_state = "STABLE"
            interpretation = "Sentiment stable - no major shifts"
        else:
            velocity_state = "DRIFTING"
            interpretation = "Minor sentiment drift"
        
        # Manipulation risk assessment
        if anomaly_info["is_anomalous"]:
            manipulation_risk = "HIGH"
            risk_reason = "Abnormal sentiment change detected - possible manipulation"
        elif velocity_metrics["volatility"] > 0.3:
            manipulation_risk = "ELEVATED"
            risk_reason = "Sentiment volatility high - exercise caution"
        else:
            manipulation_risk = "LOW"
            risk_reason = "Normal sentiment patterns"
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "current_price": sentiment_data[-1]["price"] if sentiment_data else 0,
            
            "sentiment": {
                "current_score": current_sentiment,
                "state": sentiment_state,
                "history": sentiment_data[-10:],  # Last 10 data points
            },
            
            "velocity": {
                "current": velocity_metrics["velocity"],
                "average": velocity_metrics["avg_velocity"],
                "acceleration": velocity_metrics["acceleration"],
                "volatility": velocity_metrics["volatility"],
                "state": velocity_state,
                "interpretation": interpretation,
            },
            
            "anomaly_detection": anomaly_info,
            
            "manipulation_risk": {
                "level": manipulation_risk,
                "reason": risk_reason,
            },
            
            "algorithm_version": "1.0.0",
            "data_source": "price_derived"  # In production: "twitter", "reddit", "news"
        }
        
    except Exception:
        logger.exception("Failed sentiment velocity analysis for %s", symbol)
        return None
