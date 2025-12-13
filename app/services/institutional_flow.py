# app/services/institutional_flow.py
"""
RETAIL VS INSTITUTIONAL FLOW DIVERGENCE
=======================================
Detect when retail investors are buying but institutions are selling 
(or vice versa). This divergence often predicts reversals.

Uses volume patterns and price action to estimate flow types.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

from app.services.market_weather import _fetch_ohlcv


def estimate_institutional_activity(df: pd.DataFrame) -> Dict[str, float]:
    """
    Estimate institutional vs retail activity using proxy signals.
    
    Institutional footprints:
    - Large volume on low volatility (accumulation)
    - Block-sized moves during specific times
    - Volume clusters near support/resistance
    
    Retail footprints:
    - High volatility with high volume (panic/FOMO)
    - Erratic price action
    - Volume spikes at market open/close
    """
    if len(df) < 10:
        return {
            "institutional_score": 0.5,
            "retail_score": 0.5,
            "dominant": "unknown"
        }
    
    # Calculate metrics
    returns = df['close'].pct_change().dropna()
    volatility = returns.rolling(5).std().iloc[-1] if len(returns) >= 5 else returns.std()
    
    # Volume analysis
    avg_volume = df['volume'].mean()
    recent_volume = df['volume'].tail(5).mean()
    volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
    
    # Institutional signal: High volume, low volatility
    institutional_signal = volume_ratio * (1 - min(1, volatility * 50))
    
    # Retail signal: High volatility, erratic moves
    price_changes = df['close'].diff().dropna()
    direction_changes = np.sum(np.diff(np.sign(price_changes)) != 0)
    choppiness = direction_changes / max(1, len(price_changes) - 1)
    
    retail_signal = volatility * 20 * choppiness
    
    # Normalize to 0-1
    total = institutional_signal + retail_signal + 0.01
    institutional_score = float(institutional_signal / total)
    retail_score = float(retail_signal / total)
    
    dominant = "institutional" if institutional_score > retail_score else "retail"
    
    return {
        "institutional_score": institutional_score,
        "retail_score": retail_score,
        "dominant": dominant
    }


def detect_flow_divergence(df: pd.DataFrame, window: int = 10) -> Dict[str, Any]:
    """
    Detect divergence between price movement and flow type.
    
    Bearish divergence: Price up, but retail FOMO (institutions selling)
    Bullish divergence: Price down, but institutional accumulation
    """
    if len(df) < window * 2:
        return {
            "divergence_detected": False,
            "type": None,
            "strength": 0.0
        }
    
    # Split into older and recent periods
    older = df.iloc[-window*2:-window]
    recent = df.iloc[-window:]
    
    older_flow = estimate_institutional_activity(older)
    recent_flow = estimate_institutional_activity(recent)
    
    # Price change
    price_change = (recent['close'].iloc[-1] - older['close'].iloc[-1]) / older['close'].iloc[-1]
    
    # Flow shift
    institutional_shift = recent_flow["institutional_score"] - older_flow["institutional_score"]
    
    divergence_detected = False
    divergence_type = None
    strength = 0.0
    interpretation = ""
    
    # Bearish divergence: Price up, institutional selling
    if price_change > 0.02 and institutional_shift < -0.1:
        divergence_detected = True
        divergence_type = "BEARISH"
        strength = abs(institutional_shift) * abs(price_change) * 10
        interpretation = "Price rising on retail FOMO - institutions may be distributing"
    
    # Bullish divergence: Price down, institutional buying
    elif price_change < -0.02 and institutional_shift > 0.1:
        divergence_detected = True
        divergence_type = "BULLISH"
        strength = abs(institutional_shift) * abs(price_change) * 10
        interpretation = "Price falling but institutions accumulating - potential reversal"
    
    return {
        "divergence_detected": divergence_detected,
        "type": divergence_type,
        "strength": float(min(1.0, strength)),
        "interpretation": interpretation,
        "price_change_pct": float(price_change * 100),
        "institutional_shift": float(institutional_shift)
    }


def calculate_smart_money_index(df: pd.DataFrame) -> float:
    """
    Smart Money Index: Based on the theory that smart money 
    trades at the end of day, dumb money at the open.
    
    SMI = Yesterday's Close + (Today's Close - Today's Open)
    """
    if len(df) < 2:
        return 0.5
    
    # Calculate daily SMI components
    smi_values = []
    for i in range(1, len(df)):
        prev_close = df['close'].iloc[i-1]
        today_open = df['open'].iloc[i]
        today_close = df['close'].iloc[i]
        
        # Normalize
        smi = (today_close - today_open) / today_open if today_open > 0 else 0
        smi_values.append(smi)
    
    # Recent SMI trend
    if len(smi_values) >= 5:
        recent_smi = np.mean(smi_values[-5:])
    else:
        recent_smi = np.mean(smi_values) if smi_values else 0
    
    # Convert to 0-1 scale
    return float((np.tanh(recent_smi * 20) + 1) / 2)


def analyze_institutional_flow(
    symbol: str,
    period: str = "60d",
    interval: str = "1d"
) -> Optional[Dict[str, Any]]:
    """
    Main function to analyze institutional vs retail flow.
    """
    try:
        df = _fetch_ohlcv(symbol, period=period, interval=interval)
        if df is None or df.empty:
            return None
        
        # Current flow analysis
        flow_analysis = estimate_institutional_activity(df)
        
        # Divergence detection
        divergence = detect_flow_divergence(df)
        
        # Smart money index
        smi = calculate_smart_money_index(df)
        
        # Overall interpretation
        if flow_analysis["dominant"] == "institutional":
            if flow_analysis["institutional_score"] > 0.7:
                market_type = "INSTITUTIONAL_CONTROLLED"
                advice = "Strong institutional presence - follow the trend"
            else:
                market_type = "INSTITUTIONAL_LEANING"
                advice = "Moderate institutional activity - normal market"
        else:
            if flow_analysis["retail_score"] > 0.7:
                market_type = "RETAIL_DRIVEN"
                advice = "High retail activity - expect volatility and potential reversals"
            else:
                market_type = "RETAIL_LEANING"
                advice = "Moderate retail activity - watch for sentiment shifts"
        
        # Add divergence warning
        if divergence["divergence_detected"]:
            if divergence["type"] == "BEARISH":
                advice = "⚠️ BEARISH DIVERGENCE: " + divergence["interpretation"]
            else:
                advice = "🔄 BULLISH DIVERGENCE: " + divergence["interpretation"]
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "price": float(df['close'].iloc[-1]),
            
            "flow_analysis": {
                "institutional_score": flow_analysis["institutional_score"],
                "retail_score": flow_analysis["retail_score"],
                "dominant_flow": flow_analysis["dominant"],
                "market_type": market_type,
            },
            
            "divergence": divergence,
            
            "smart_money_index": {
                "value": smi,
                "interpretation": "Smart money bullish" if smi > 0.6 else \
                                "Smart money bearish" if smi < 0.4 else "Neutral"
            },
            
            "advice": advice,
            
            "algorithm_version": "1.0.0",
            "methodology": "Volume-volatility flow estimation with divergence detection"
        }
        
    except Exception:
        logger.exception("Failed institutional flow analysis for %s", symbol)
        return None
