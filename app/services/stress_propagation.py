# app/services/stress_propagation.py
"""
CROSS-ASSET STRESS PROPAGATION
==============================
Analyzes how stress in one market propagates to others.
Detects time-delayed causality chains between assets.

Key insight: When VIX spikes, which Indian sectors get hit first?
Uses Granger causality concepts and lead-lag analysis.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

from app.services.market_weather import _fetch_ohlcv


# Define asset relationships for stress propagation
STRESS_INDICATORS = {
    "global": ["^VIX", "^GSPC", "^DJI"],  # VIX, S&P 500, Dow Jones
    "india_indices": ["^NSEI", "^BSESN"],  # Nifty, Sensex
    "india_sectors": {
        "banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"],
        "it": ["TCS.NS", "INFY.NS", "WIPRO.NS"],
        "metals": ["TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS"],
        "auto": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS"],
        "pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS"],
    }
}


def calculate_rolling_correlation(
    series1: pd.Series, 
    series2: pd.Series, 
    window: int = 20
) -> pd.Series:
    """Calculate rolling correlation between two series."""
    return series1.rolling(window).corr(series2)


def calculate_lead_lag_correlation(
    leader: pd.Series,
    follower: pd.Series,
    max_lag: int = 5
) -> Tuple[int, float]:
    """
    Find optimal lag where correlation is highest.
    Returns (best_lag, correlation_at_best_lag)
    """
    best_lag = 0
    best_corr = 0.0
    
    for lag in range(0, max_lag + 1):
        if lag == 0:
            corr = leader.corr(follower)
        else:
            # Leader leads follower by 'lag' periods
            corr = leader.iloc[:-lag].corr(follower.iloc[lag:])
        
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag
    
    return best_lag, float(best_corr)


def calculate_stress_score(df: pd.DataFrame) -> float:
    """
    Calculate a stress score based on volatility and drawdown.
    """
    if df.empty or len(df) < 2:
        return 0.0
    
    returns = df['close'].pct_change().dropna()
    
    if returns.empty:
        return 0.0
    
    # Volatility component
    volatility = returns.std() * np.sqrt(252)  # Annualized
    
    # Drawdown component
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdown.min())
    
    # Negative return bias
    negative_returns = returns[returns < 0]
    negative_bias = abs(negative_returns.mean()) if len(negative_returns) > 0 else 0
    
    stress = (volatility * 0.4 + max_drawdown * 0.4 + negative_bias * 10 * 0.2)
    
    return float(min(1.0, stress))


def analyze_stress_propagation(
    target_symbol: str,
    period: str = "60d",
    interval: str = "1d"
) -> Optional[Dict[str, Any]]:
    """
    Analyze how stress from global markets propagates to the target symbol.
    """
    try:
        # Fetch target data
        target_df = _fetch_ohlcv(target_symbol, period=period, interval=interval)
        if target_df is None or target_df.empty:
            return None
        
        target_returns = target_df['close'].pct_change().dropna()
        target_stress = calculate_stress_score(target_df)
        
        # Analyze relationships with stress indicators
        propagation_chains = []
        
        # Check VIX relationship (most important)
        vix_df = _fetch_ohlcv("^VIX", period=period, interval=interval)
        if vix_df is not None and not vix_df.empty:
            vix_returns = vix_df['close'].pct_change().dropna()
            
            # Align data
            common_idx = target_returns.index.intersection(vix_returns.index)
            if len(common_idx) > 10:
                target_aligned = target_returns.loc[common_idx]
                vix_aligned = vix_returns.loc[common_idx]
                
                lag, corr = calculate_lead_lag_correlation(vix_aligned, target_aligned)
                
                propagation_chains.append({
                    "source": "VIX",
                    "lag_days": lag,
                    "correlation": corr,
                    "relationship": "inverse" if corr < 0 else "positive",
                    "strength": "strong" if abs(corr) > 0.5 else "moderate" if abs(corr) > 0.3 else "weak"
                })
        
        # Check S&P 500 relationship
        sp500_df = _fetch_ohlcv("^GSPC", period=period, interval=interval)
        if sp500_df is not None and not sp500_df.empty:
            sp_returns = sp500_df['close'].pct_change().dropna()
            
            common_idx = target_returns.index.intersection(sp_returns.index)
            if len(common_idx) > 10:
                target_aligned = target_returns.loc[common_idx]
                sp_aligned = sp_returns.loc[common_idx]
                
                lag, corr = calculate_lead_lag_correlation(sp_aligned, target_aligned)
                
                propagation_chains.append({
                    "source": "S&P 500",
                    "lag_days": lag,
                    "correlation": corr,
                    "relationship": "positive" if corr > 0 else "inverse",
                    "strength": "strong" if abs(corr) > 0.5 else "moderate" if abs(corr) > 0.3 else "weak"
                })
        
        # Check Nifty relationship
        nifty_df = _fetch_ohlcv("^NSEI", period=period, interval=interval)
        if nifty_df is not None and not nifty_df.empty:
            nifty_returns = nifty_df['close'].pct_change().dropna()
            
            common_idx = target_returns.index.intersection(nifty_returns.index)
            if len(common_idx) > 10:
                target_aligned = target_returns.loc[common_idx]
                nifty_aligned = nifty_returns.loc[common_idx]
                
                corr = target_aligned.corr(nifty_aligned)
                
                propagation_chains.append({
                    "source": "NIFTY 50",
                    "lag_days": 0,
                    "correlation": float(corr),
                    "relationship": "follows index" if corr > 0.7 else "partially correlated" if corr > 0.4 else "independent",
                    "strength": "strong" if abs(corr) > 0.5 else "moderate" if abs(corr) > 0.3 else "weak"
                })
        
        # Calculate overall vulnerability
        strong_correlations = [c for c in propagation_chains if c["strength"] == "strong"]
        vulnerability = len(strong_correlations) / max(1, len(propagation_chains))
        
        # Risk assessment
        if target_stress > 0.6:
            current_state = "HIGH_STRESS"
            advice = "Asset is currently stressed. Global factors may amplify moves."
        elif target_stress > 0.3:
            current_state = "ELEVATED"
            advice = "Moderate stress. Monitor global indicators."
        else:
            current_state = "NORMAL"
            advice = "Low stress environment. Standard risk management applies."
        
        return {
            "symbol": target_symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "price": float(target_df['close'].iloc[-1]),
            
            "stress_analysis": {
                "current_stress_score": target_stress,
                "state": current_state,
                "advice": advice,
            },
            
            "propagation_chains": propagation_chains,
            
            "vulnerability": {
                "global_sensitivity": float(vulnerability),
                "most_influential": propagation_chains[0]["source"] if propagation_chains else "Unknown",
                "warning": "High sensitivity to global events" if vulnerability > 0.5 else "Moderate global exposure"
            },
            
            "algorithm_version": "1.0.0",
            "methodology": "Lead-lag correlation analysis with stress scoring"
        }
        
    except Exception:
        logger.exception("Failed stress propagation analysis for %s", target_symbol)
        return None
