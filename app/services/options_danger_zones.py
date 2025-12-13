# app/services/options_danger_zones.py
"""
OPTIONS-IMPLIED DANGER ZONES
============================
Use options chain data concepts to predict where the stock 
will be "forced" to move by expiry.

Max Pain Theory: Stock tends to close at price where most 
options expire worthless (maximum loss for option buyers).

This is especially powerful for F&O stocks in India.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

from app.services.market_weather import _fetch_ohlcv


def calculate_price_magnets(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Calculate price levels that act as "magnets" for the stock.
    Based on historical volume clusters and round numbers.
    """
    if len(df) < 20:
        return []
    
    current_price = df['close'].iloc[-1]
    
    magnets = []
    
    # Round number magnets (psychological levels)
    base = 10 ** (len(str(int(current_price))) - 2)
    lower_round = int(current_price / base) * base
    upper_round = lower_round + base
    
    magnets.append({
        "level": float(lower_round),
        "type": "psychological",
        "strength": 0.3 + 0.2 * (1 - abs(current_price - lower_round) / (current_price * 0.05))
    })
    magnets.append({
        "level": float(upper_round),
        "type": "psychological",
        "strength": 0.3 + 0.2 * (1 - abs(current_price - upper_round) / (current_price * 0.05))
    })
    
    # Volume-weighted price levels (VWAP clusters)
    # Find price levels with highest volume
    try:
        price_bins = pd.cut(df['close'], bins=20)
        volume_by_price = df.groupby(price_bins, observed=True)['volume'].sum()
        
        for i, (price_range, volume) in enumerate(volume_by_price.items()):
            if volume > 0 and hasattr(price_range, 'left') and hasattr(price_range, 'right'):
                mid_price = (price_range.left + price_range.right) / 2
                volume_pct = volume / df['volume'].sum()
                
                if volume_pct > 0.08:  # Significant volume cluster
                    magnets.append({
                        "level": float(mid_price),
                        "type": "volume_cluster",
                        "strength": float(min(1.0, volume_pct * 5))
                    })
    except Exception:
        pass  # Skip volume clusters if calculation fails
    
    # Previous day high/low
    recent = df.tail(5)
    magnets.append({
        "level": float(recent['high'].max()),
        "type": "recent_high",
        "strength": 0.6
    })
    magnets.append({
        "level": float(recent['low'].min()),
        "type": "recent_low",
        "strength": 0.6
    })
    
    # Sort by strength
    magnets.sort(key=lambda x: x["strength"], reverse=True)
    
    return magnets[:5]  # Top 5 magnets


def estimate_max_pain(
    current_price: float,
    magnets: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Estimate "max pain" level where price might gravitate.
    
    In reality, this requires options chain data.
    This is an approximation using price magnets.
    """
    if not magnets:
        return {
            "estimated_level": current_price,
            "confidence": 0.0,
            "distance_pct": 0.0
        }
    
    # Weighted average of magnet levels
    total_weight = sum(m["strength"] for m in magnets)
    if total_weight == 0:
        return {
            "estimated_level": current_price,
            "confidence": 0.0,
            "distance_pct": 0.0
        }
    
    max_pain = sum(m["level"] * m["strength"] for m in magnets) / total_weight
    
    # Confidence based on magnet clustering
    distances = [abs(m["level"] - max_pain) / max_pain for m in magnets]
    avg_distance = np.mean(distances)
    confidence = max(0, 1 - avg_distance * 5)
    
    distance_pct = (max_pain - current_price) / current_price * 100
    
    return {
        "estimated_level": float(max_pain),
        "confidence": float(confidence),
        "distance_pct": float(distance_pct),
        "direction": "UP" if distance_pct > 0 else "DOWN" if distance_pct < 0 else "NEUTRAL"
    }


def calculate_gamma_exposure_proxy(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Estimate gamma exposure using price volatility patterns.
    High gamma = price accelerates near certain levels.
    """
    if len(df) < 14:
        return {
            "gamma_proxy": 0.0,
            "volatility_by_level": {}
        }
    
    returns = df['close'].pct_change().dropna()
    
    # Calculate volatility in different price zones
    current_price = df['close'].iloc[-1]
    
    zones = {
        "below_current": df[df['close'] < current_price * 0.98],
        "at_current": df[(df['close'] >= current_price * 0.98) & (df['close'] <= current_price * 1.02)],
        "above_current": df[df['close'] > current_price * 1.02]
    }
    
    volatility_by_zone = {}
    for zone_name, zone_df in zones.items():
        if len(zone_df) >= 3:
            zone_returns = zone_df['close'].pct_change().dropna()
            volatility_by_zone[zone_name] = float(zone_returns.std() * 100) if not zone_returns.empty else 0.0
        else:
            volatility_by_zone[zone_name] = 0.0
    
    # Gamma proxy: how much does volatility change with price
    gamma_proxy = np.std(list(volatility_by_zone.values())) if volatility_by_zone else 0.0
    
    return {
        "gamma_proxy": float(gamma_proxy),
        "volatility_by_zone": volatility_by_zone,
        "interpretation": "High gamma environment" if gamma_proxy > 0.5 else "Low gamma environment"
    }


def analyze_options_danger_zones(
    symbol: str,
    period: str = "60d",
    interval: str = "1d"
) -> Optional[Dict[str, Any]]:
    """
    Main function for options-implied danger zone analysis.
    """
    try:
        df = _fetch_ohlcv(symbol, period=period, interval=interval)
        if df is None or df.empty:
            return None
        
        current_price = float(df['close'].iloc[-1])
        
        # Calculate price magnets
        magnets = calculate_price_magnets(df)
        
        # Estimate max pain
        max_pain = estimate_max_pain(current_price, magnets)
        
        # Gamma exposure proxy
        gamma = calculate_gamma_exposure_proxy(df)
        
        # Identify danger zones (where rapid moves might occur)
        danger_zones = []
        for magnet in magnets:
            distance = abs(magnet["level"] - current_price) / current_price
            if distance < 0.03:  # Within 3%
                danger_zones.append({
                    "level": magnet["level"],
                    "type": magnet["type"],
                    "risk": "HIGH" if magnet["strength"] > 0.5 else "MODERATE",
                    "reason": f"Price near {magnet['type']} level"
                })
        
        # Trading advice
        if len(danger_zones) > 2:
            advice = "Multiple danger zones nearby - expect volatile price action"
            risk_level = "HIGH"
        elif len(danger_zones) > 0:
            advice = f"Approaching {danger_zones[0]['type']} zone - watch for reaction"
            risk_level = "MODERATE"
        else:
            advice = "Price in neutral territory - normal trading conditions"
            risk_level = "LOW"
        
        # Max pain direction
        if abs(max_pain["distance_pct"]) > 2:
            if max_pain["direction"] == "UP":
                advice += f". Max pain suggests upward pull towards {max_pain['estimated_level']:.2f}"
            else:
                advice += f". Max pain suggests downward pressure towards {max_pain['estimated_level']:.2f}"
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "price": current_price,
            
            "max_pain_estimate": max_pain,
            
            "price_magnets": magnets,
            
            "danger_zones": danger_zones,
            
            "gamma_analysis": gamma,
            
            "summary": {
                "risk_level": risk_level,
                "advice": advice,
                "zones_nearby": len(danger_zones),
            },
            
            "algorithm_version": "1.0.0",
            "note": "For accurate max pain, integrate with NSE/BSE options chain API"
        }
        
    except Exception:
        logger.exception("Failed options danger zone analysis for %s", symbol)
        return None
