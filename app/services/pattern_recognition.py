# app/services/pattern_recognition.py
"""
BEHAVIORAL PATTERN RECOGNITION
==============================
Detect when a stock's price action matches historical 
manipulation patterns.

Patterns to detect:
- Pump and dump
- Ladder attack (short ladder)
- Wash trading signatures
- Spoofing patterns
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

from app.services.market_weather import _fetch_ohlcv


def detect_pump_and_dump(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect potential pump and dump patterns.
    
    Characteristics:
    - Sharp price increase (>20% in 5 days)
    - Volume spike during pump
    - Price reversal
    - Volume decline during dump
    """
    if len(df) < 20:
        return {"detected": False, "confidence": 0.0}
    
    # Look for pump phase
    windows = [5, 10, 15]
    
    for window in windows:
        recent = df.tail(window)
        older = df.tail(window * 2).head(window)
        
        if len(recent) < window or len(older) < window:
            continue
        
        price_change = (recent['close'].iloc[-1] - older['close'].iloc[-1]) / older['close'].iloc[-1]
        max_price = recent['high'].max()
        current_price = recent['close'].iloc[-1]
        
        drawdown_from_max = (max_price - current_price) / max_price
        
        volume_pump = recent['volume'].mean()
        volume_before = older['volume'].mean()
        volume_spike = volume_pump / volume_before if volume_before > 0 else 1
        
        # Pump and dump signature:
        # 1. Big move up then reversal
        # 2. Volume spike during pump
        if price_change > 0.1 and drawdown_from_max > 0.1 and volume_spike > 2:
            confidence = min(1.0, (price_change + drawdown_from_max + (volume_spike - 1) * 0.2) / 3)
            return {
                "detected": True,
                "confidence": float(confidence),
                "window_days": window,
                "price_change_pct": float(price_change * 100),
                "drawdown_pct": float(drawdown_from_max * 100),
                "volume_spike_ratio": float(volume_spike),
                "phase": "DUMP" if drawdown_from_max > price_change * 0.5 else "POST_PUMP"
            }
    
    return {"detected": False, "confidence": 0.0}


def detect_wash_trading(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect potential wash trading signatures.
    
    Characteristics:
    - High volume with minimal price change
    - Repetitive price patterns
    - Volume doesn't match price movement
    """
    if len(df) < 10:
        return {"detected": False, "confidence": 0.0}
    
    recent = df.tail(10)
    
    # Volume to price movement ratio
    price_range = (recent['high'].max() - recent['low'].min()) / recent['close'].mean()
    volume_intensity = recent['volume'].sum() / df['volume'].mean() / 10
    
    # Wash trading: lots of volume, little price movement
    if volume_intensity > 1.5 and price_range < 0.02:
        wash_score = (volume_intensity - 1) * (0.03 - price_range) * 100
        
        return {
            "detected": True,
            "confidence": float(min(1.0, wash_score)),
            "volume_intensity": float(volume_intensity),
            "price_range_pct": float(price_range * 100),
            "interpretation": "High volume with minimal price movement - possible wash trading"
        }
    
    return {"detected": False, "confidence": 0.0}


def detect_ladder_attack(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect potential short ladder attack patterns.
    
    Characteristics:
    - Step-down price action
    - Low volume on down moves
    - Quick succession of lower highs
    """
    if len(df) < 10:
        return {"detected": False, "confidence": 0.0}
    
    recent = df.tail(10)
    
    # Count consecutive lower closes
    closes = recent['close'].values
    lower_count = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i-1])
    lower_ratio = lower_count / (len(closes) - 1)
    
    # Volume on down bars vs up bars
    down_vol = []
    up_vol = []
    
    for i in range(1, len(recent)):
        if recent['close'].iloc[i] < recent['close'].iloc[i-1]:
            down_vol.append(recent['volume'].iloc[i])
        else:
            up_vol.append(recent['volume'].iloc[i])
    
    avg_down_vol = np.mean(down_vol) if down_vol else 0
    avg_up_vol = np.mean(up_vol) if up_vol else 0
    
    # Step pattern
    price_decline = (closes[0] - closes[-1]) / closes[0]
    
    # Ladder attack: Many down days, low relative volume on down moves
    if lower_ratio > 0.7 and price_decline > 0.05:
        vol_ratio = avg_down_vol / avg_up_vol if avg_up_vol > 0 else 1
        
        if vol_ratio < 0.8:  # Lower volume on down days = artificial
            confidence = lower_ratio * (1 - vol_ratio) * price_decline * 10
            
            return {
                "detected": True,
                "confidence": float(min(1.0, confidence)),
                "consecutive_down_ratio": float(lower_ratio),
                "price_decline_pct": float(price_decline * 100),
                "volume_ratio_down_vs_up": float(vol_ratio),
                "interpretation": "Stair-step decline with low selling volume - possible manipulation"
            }
    
    return {"detected": False, "confidence": 0.0}


def detect_spoofing(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect potential spoofing patterns using price reversals.
    
    Spoofing leaves traces in the form of false breakouts
    followed by rapid reversals.
    """
    if len(df) < 5:
        return {"detected": False, "confidence": 0.0}
    
    # Look for false breakouts with reversals
    recent = df.tail(5)
    
    high_wick_ratio = (recent['high'] - np.maximum(recent['open'], recent['close'])) / \
                      (recent['high'] - recent['low'] + 0.001)
    
    low_wick_ratio = (np.minimum(recent['open'], recent['close']) - recent['low']) / \
                     (recent['high'] - recent['low'] + 0.001)
    
    avg_wick = (high_wick_ratio.mean() + low_wick_ratio.mean()) / 2
    
    # High wick ratio = lots of rejections = possible spoofing
    if avg_wick > 0.4:
        return {
            "detected": True,
            "confidence": float(min(1.0, (avg_wick - 0.3) * 3)),
            "avg_wick_ratio": float(avg_wick),
            "interpretation": "Frequent price rejections - possible spoofing activity"
        }
    
    return {"detected": False, "confidence": 0.0}


def analyze_manipulation_patterns(
    symbol: str,
    period: str = "30d",
    interval: str = "1d"
) -> Optional[Dict[str, Any]]:
    """
    Main function to detect manipulation patterns.
    """
    try:
        df = _fetch_ohlcv(symbol, period=period, interval=interval)
        if df is None or df.empty:
            return None
        
        # Run all detectors
        pump_dump = detect_pump_and_dump(df)
        wash_trading = detect_wash_trading(df)
        ladder_attack = detect_ladder_attack(df)
        spoofing = detect_spoofing(df)
        
        # Aggregate risk
        patterns_detected = []
        total_risk = 0.0
        
        if pump_dump["detected"]:
            patterns_detected.append({
                "pattern": "PUMP_AND_DUMP",
                "confidence": pump_dump["confidence"],
                "details": pump_dump
            })
            total_risk += pump_dump["confidence"]
        
        if wash_trading["detected"]:
            patterns_detected.append({
                "pattern": "WASH_TRADING",
                "confidence": wash_trading["confidence"],
                "details": wash_trading
            })
            total_risk += wash_trading["confidence"]
        
        if ladder_attack["detected"]:
            patterns_detected.append({
                "pattern": "LADDER_ATTACK",
                "confidence": ladder_attack["confidence"],
                "details": ladder_attack
            })
            total_risk += ladder_attack["confidence"]
        
        if spoofing["detected"]:
            patterns_detected.append({
                "pattern": "SPOOFING",
                "confidence": spoofing["confidence"],
                "details": spoofing
            })
            total_risk += spoofing["confidence"]
        
        # Normalize risk
        manipulation_risk = min(1.0, total_risk / 2)
        
        # Advisory
        if manipulation_risk > 0.7:
            risk_level = "CRITICAL"
            advice = "Multiple manipulation patterns detected - AVOID this stock"
        elif manipulation_risk > 0.4:
            risk_level = "HIGH"
            advice = "Potential manipulation signals - exercise extreme caution"
        elif manipulation_risk > 0.2:
            risk_level = "ELEVATED"
            advice = "Some unusual patterns - monitor closely"
        else:
            risk_level = "LOW"
            advice = "No significant manipulation patterns detected"
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "price": float(df['close'].iloc[-1]),
            
            "patterns_detected": patterns_detected,
            "patterns_count": len(patterns_detected),
            
            "manipulation_risk": {
                "score": float(manipulation_risk),
                "level": risk_level,
                "advice": advice,
            },
            
            "individual_checks": {
                "pump_and_dump": pump_dump,
                "wash_trading": wash_trading,
                "ladder_attack": ladder_attack,
                "spoofing": spoofing,
            },
            
            "algorithm_version": "1.0.0",
            "disclaimer": "This is algorithmic analysis, not definitive proof of manipulation"
        }
        
    except Exception:
        logger.exception("Failed manipulation pattern analysis for %s", symbol)
        return None
