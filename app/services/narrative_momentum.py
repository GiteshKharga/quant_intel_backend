# app/services/narrative_momentum.py
"""
NARRATIVE MOMENTUM SCORE
========================
Track how long a market "story" stays in consciousness.
Narratives have lifecycles - early = opportunity, late = danger.

Examples of narratives:
- "AI stocks" (2023-2024)
- "EV revolution" (2020-2021)
- "Work from home stocks" (2020)
- "Metaverse plays" (2021-2022)

Novel approach: Lifecycle stage detection of market narratives.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

from app.services.market_weather import _fetch_ohlcv


# Define known market narratives and their related stocks
MARKET_NARRATIVES = {
    "ai_boom": {
        "name": "AI/Machine Learning Boom",
        "keywords": ["ai", "artificial intelligence", "machine learning", "chatgpt", "nvidia"],
        "indian_stocks": ["TATAELXSI.NS", "LTIM.NS", "INFY.NS", "TCS.NS", "WIPRO.NS"],
        "global_stocks": ["NVDA", "MSFT", "GOOGL", "META", "AMD"],
        "start_date": "2023-01-01"
    },
    "ev_revolution": {
        "name": "Electric Vehicle Revolution",
        "keywords": ["ev", "electric vehicle", "battery", "lithium", "tesla"],
        "indian_stocks": ["TATAMOTORS.NS", "M&M.NS", "EXIDEIND.NS", "AMARAJABAT.NS"],
        "global_stocks": ["TSLA", "RIVN", "NIO", "LCID"],
        "start_date": "2020-01-01"
    },
    "renewable_energy": {
        "name": "Green Energy Transition",
        "keywords": ["solar", "wind", "renewable", "green energy", "hydrogen"],
        "indian_stocks": ["ADANIGREEN.NS", "TATAPOWER.NS", "NHPC.NS", "RELIANCE.NS"],
        "global_stocks": ["ENPH", "SEDG", "FSLR"],
        "start_date": "2020-01-01"
    },
    "fintech": {
        "name": "Fintech & Digital Banking",
        "keywords": ["fintech", "digital payment", "upi", "neobank"],
        "indian_stocks": ["PAYTM.NS", "POLICYBZR.NS", "PNB.NS"],
        "global_stocks": ["SQ", "PYPL", "COIN"],
        "start_date": "2019-01-01"
    },
    "defense": {
        "name": "Defense & Aerospace",
        "keywords": ["defense", "military", "aerospace", "make in india"],
        "indian_stocks": ["HAL.NS", "BEL.NS", "BEML.NS", "BDL.NS"],
        "global_stocks": ["LMT", "RTX", "NOC"],
        "start_date": "2022-01-01"
    },
    "infra_capex": {
        "name": "Infrastructure & Capex Cycle",
        "keywords": ["infrastructure", "construction", "capex", "railways"],
        "indian_stocks": ["LT.NS", "IRB.NS", "NCC.NS", "IRCTC.NS"],
        "global_stocks": [],
        "start_date": "2021-01-01"
    }
}


def calculate_narrative_strength(
    symbols: List[str],
    period: str = "90d"
) -> Dict[str, float]:
    """
    Calculate the strength of a narrative based on constituent stocks.
    """
    total_return = 0.0
    total_momentum = 0.0
    total_volume_surge = 0.0
    valid_count = 0
    
    for symbol in symbols[:5]:  # Limit to 5 stocks for speed
        try:
            df = _fetch_ohlcv(symbol, period=period, interval="1d")
            if df is None or df.empty:
                continue
            
            # Calculate return
            start_price = df['close'].iloc[0]
            end_price = df['close'].iloc[-1]
            ret = (end_price - start_price) / start_price
            total_return += ret
            
            # Calculate momentum (recent vs older performance)
            mid = len(df) // 2
            early_ret = (df['close'].iloc[mid] - df['close'].iloc[0]) / df['close'].iloc[0]
            late_ret = (df['close'].iloc[-1] - df['close'].iloc[mid]) / df['close'].iloc[mid]
            momentum = late_ret - early_ret
            total_momentum += momentum
            
            # Volume surge
            early_vol = df['volume'].iloc[:mid].mean()
            late_vol = df['volume'].iloc[mid:].mean()
            vol_surge = (late_vol / early_vol) - 1 if early_vol > 0 else 0
            total_volume_surge += vol_surge
            
            valid_count += 1
            
        except Exception:
            continue
    
    if valid_count == 0:
        return {
            "avg_return": 0.0,
            "momentum": 0.0,
            "volume_surge": 0.0,
            "strength_score": 0.0
        }
    
    avg_return = total_return / valid_count
    avg_momentum = total_momentum / valid_count
    avg_vol_surge = total_volume_surge / valid_count
    
    # Combined strength score
    strength = (
        np.tanh(avg_return * 2) * 0.4 +
        np.tanh(avg_momentum * 5) * 0.3 +
        np.tanh(avg_vol_surge) * 0.3
    )
    
    return {
        "avg_return": float(avg_return),
        "momentum": float(avg_momentum),
        "volume_surge": float(avg_vol_surge),
        "strength_score": float(max(0, min(1, (strength + 1) / 2)))
    }


def detect_narrative_lifecycle(
    strength_score: float,
    momentum: float,
    start_date: str
) -> Dict[str, Any]:
    """
    Detect which lifecycle stage a narrative is in.
    
    Stages:
    1. EARLY: Low strength, positive momentum - opportunity
    2. GROWTH: Rising strength, positive momentum - ride the wave
    3. PEAK: High strength, flat/negative momentum - be cautious
    4. DECLINE: Falling strength, negative momentum - exit
    5. DEAD: Low strength, no momentum - narrative exhausted
    """
    # Calculate age of narrative in months
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        age_months = (datetime.now() - start).days / 30
    except:
        age_months = 0
    
    if strength_score < 0.3:
        if momentum > 0.05:
            stage = "EARLY"
            action = "Consider early entry - narrative gaining traction"
            risk = "HIGH"
        else:
            stage = "DEAD"
            action = "Narrative exhausted - look elsewhere"
            risk = "LOW"
    elif strength_score < 0.5:
        if momentum > 0:
            stage = "EMERGING"
            action = "Building momentum - watch for confirmation"
            risk = "MODERATE"
        else:
            stage = "FADING"
            action = "Losing steam - tighten stops"
            risk = "MODERATE"
    elif strength_score < 0.75:
        if momentum > 0:
            stage = "GROWTH"
            action = "Strong trend - ride with trailing stops"
            risk = "MODERATE"
        else:
            stage = "MATURE"
            action = "Peak forming - take partial profits"
            risk = "ELEVATED"
    else:
        if momentum > -0.05:
            stage = "PEAK"
            action = "Likely overbought - consider exiting"
            risk = "HIGH"
        else:
            stage = "DECLINE"
            action = "Trend reversing - exit positions"
            risk = "VERY_HIGH"
    
    return {
        "stage": stage,
        "action": action,
        "risk": risk,
        "age_months": float(age_months),
        "maturity": "mature" if age_months > 18 else "mid" if age_months > 6 else "young"
    }


def analyze_narrative_momentum(
    symbol: str,
    period: str = "90d"
) -> Optional[Dict[str, Any]]:
    """
    Analyze which narratives a stock belongs to and their lifecycle stages.
    """
    try:
        # Find which narratives this symbol belongs to
        matched_narratives = []
        
        for narrative_id, narrative_info in MARKET_NARRATIVES.items():
            all_stocks = narrative_info.get("indian_stocks", []) + \
                        narrative_info.get("global_stocks", [])
            
            if symbol.upper() in [s.upper() for s in all_stocks]:
                matched_narratives.append((narrative_id, narrative_info))
        
        if not matched_narratives:
            # Even if not in a known narrative, analyze independently
            df = _fetch_ohlcv(symbol, period=period, interval="1d")
            if df is None or df.empty:
                return None
            
            return {
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "price": float(df['close'].iloc[-1]),
                "matched_narratives": [],
                "narrative_exposure": "NONE",
                "advice": "Stock not part of any tracked market narrative",
                "algorithm_version": "1.0.0"
            }
        
        # Analyze each matched narrative
        narrative_analyses = []
        
        for narrative_id, narrative_info in matched_narratives:
            all_stocks = narrative_info.get("indian_stocks", []) + \
                        narrative_info.get("global_stocks", [])
            
            strength = calculate_narrative_strength(all_stocks, period)
            lifecycle = detect_narrative_lifecycle(
                strength["strength_score"],
                strength["momentum"],
                narrative_info.get("start_date", "2020-01-01")
            )
            
            narrative_analyses.append({
                "narrative_id": narrative_id,
                "name": narrative_info["name"],
                "keywords": narrative_info.get("keywords", []),
                "strength": strength,
                "lifecycle": lifecycle,
                "peers_in_narrative": len(all_stocks),
            })
        
        # Determine overall advice based on dominant narrative
        dominant = max(narrative_analyses, key=lambda x: x["strength"]["strength_score"])
        
        if dominant["lifecycle"]["stage"] in ["EARLY", "EMERGING", "GROWTH"]:
            overall_advice = f"Positive narrative tailwind from '{dominant['name']}'"
        elif dominant["lifecycle"]["stage"] in ["PEAK", "MATURE"]:
            overall_advice = f"Narrative '{dominant['name']}' may be peaking - caution advised"
        else:
            overall_advice = f"Narrative '{dominant['name']}' weakening - consider reducing exposure"
        
        # Get current price
        df = _fetch_ohlcv(symbol, period="5d", interval="1d")
        current_price = float(df['close'].iloc[-1]) if df is not None and not df.empty else 0
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "price": current_price,
            
            "matched_narratives": narrative_analyses,
            "narrative_exposure": "SINGLE" if len(narrative_analyses) == 1 else "MULTIPLE",
            "dominant_narrative": dominant["name"],
            
            "overall_analysis": {
                "advice": overall_advice,
                "dominant_stage": dominant["lifecycle"]["stage"],
                "risk_level": dominant["lifecycle"]["risk"],
            },
            
            "algorithm_version": "1.0.0",
            "methodology": "Narrative lifecycle analysis with momentum scoring"
        }
        
    except Exception:
        logger.exception("Failed narrative momentum analysis for %s", symbol)
        return None
