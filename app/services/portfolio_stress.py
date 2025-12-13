# app/services/portfolio_stress.py
"""
PORTFOLIO STRESS TEST WITH HISTORICAL EVENTS
=============================================
Instead of Monte Carlo simulation, use ACTUAL historical crisis data.

"What happens to my portfolio if 2008 repeats?"
"What if demonetization happens again?"
"What if COVID-like crash occurs?"
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

from app.services.market_weather import _fetch_ohlcv


# Historical crisis events
HISTORICAL_CRISES = {
    "2008_financial_crisis": {
        "name": "2008 Global Financial Crisis",
        "start_date": "2008-09-01",
        "end_date": "2009-03-31",
        "description": "Lehman Brothers collapse, global banking crisis",
        "nifty_drawdown": -61,  # Approximate peak to trough
        "recovery_months": 24,
    },
    "2011_eurozone_crisis": {
        "name": "2011 Eurozone Debt Crisis",
        "start_date": "2011-07-01",
        "end_date": "2011-12-31",
        "description": "European sovereign debt concerns",
        "nifty_drawdown": -28,
        "recovery_months": 12,
    },
    "2015_china_crash": {
        "name": "2015-16 China Slowdown",
        "start_date": "2015-08-01",
        "end_date": "2016-02-28",
        "description": "Chinese market crash and yuan devaluation",
        "nifty_drawdown": -23,
        "recovery_months": 10,
    },
    "2016_demonetization": {
        "name": "2016 India Demonetization",
        "start_date": "2016-11-08",
        "end_date": "2017-01-31",
        "description": "India's sudden demonetization of currency notes",
        "nifty_drawdown": -8,
        "recovery_months": 2,
    },
    "2020_covid_crash": {
        "name": "2020 COVID-19 Crash",
        "start_date": "2020-02-20",
        "end_date": "2020-03-23",
        "description": "Global pandemic market crash",
        "nifty_drawdown": -38,
        "recovery_months": 8,
    },
    "2022_russia_ukraine": {
        "name": "2022 Russia-Ukraine War",
        "start_date": "2022-02-24",
        "end_date": "2022-06-30",
        "description": "War outbreak and global supply chain disruption",
        "nifty_drawdown": -12,
        "recovery_months": 4,
    }
}

# Sector sensitivity to different crises (multipliers)
SECTOR_SENSITIVITY = {
    "banking": {
        "2008_financial_crisis": 1.5,  # 50% more affected
        "2020_covid_crash": 1.3,
        "2016_demonetization": 1.4,
        "default": 1.0
    },
    "it": {
        "2008_financial_crisis": 1.2,
        "2020_covid_crash": 0.7,  # Less affected, benefited from WFH
        "default": 0.9
    },
    "pharma": {
        "2020_covid_crash": 0.5,  # Defensive, benefited
        "default": 0.8
    },
    "metals": {
        "2015_china_crash": 1.5,
        "2022_russia_ukraine": 1.3,
        "default": 1.1
    },
    "auto": {
        "2016_demonetization": 1.5,
        "2020_covid_crash": 1.4,
        "default": 1.0
    },
    "fmcg": {
        "default": 0.7  # Defensive sector
    }
}

# Stock to sector mapping (sample)
STOCK_SECTORS = {
    "HDFCBANK.NS": "banking", "ICICIBANK.NS": "banking", "SBIN.NS": "banking",
    "TCS.NS": "it", "INFY.NS": "it", "WIPRO.NS": "it",
    "SUNPHARMA.NS": "pharma", "DRREDDY.NS": "pharma", "CIPLA.NS": "pharma",
    "TATASTEEL.NS": "metals", "HINDALCO.NS": "metals",
    "MARUTI.NS": "auto", "TATAMOTORS.NS": "auto",
    "HINDUNILVR.NS": "fmcg", "ITC.NS": "fmcg",
    "RELIANCE.NS": "conglomerate",
}


def get_stock_sector(symbol: str) -> str:
    """Get sector for a stock."""
    return STOCK_SECTORS.get(symbol.upper(), "unknown")


def calculate_crisis_impact(
    symbol: str,
    crisis_id: str,
    portfolio_value: float = 100000
) -> Dict[str, Any]:
    """
    Calculate the impact of a specific historical crisis on a stock.
    """
    if crisis_id not in HISTORICAL_CRISES:
        return {"error": "Unknown crisis"}
    
    crisis = HISTORICAL_CRISES[crisis_id]
    base_drawdown = crisis["nifty_drawdown"]
    
    # Adjust for sector sensitivity
    sector = get_stock_sector(symbol)
    sensitivity_map = SECTOR_SENSITIVITY.get(sector, SECTOR_SENSITIVITY.get("fmcg", {}))
    sensitivity = sensitivity_map.get(crisis_id, sensitivity_map.get("default", 1.0))
    
    adjusted_drawdown = base_drawdown * sensitivity
    
    # Calculate portfolio impact
    value_at_bottom = portfolio_value * (1 + adjusted_drawdown / 100)
    loss = portfolio_value - value_at_bottom
    
    return {
        "crisis_id": crisis_id,
        "crisis_name": crisis["name"],
        "description": crisis["description"],
        "base_market_drawdown": base_drawdown,
        "sector": sector,
        "sector_sensitivity": sensitivity,
        "adjusted_drawdown_pct": float(adjusted_drawdown),
        "portfolio_impact": {
            "initial_value": portfolio_value,
            "estimated_bottom_value": float(value_at_bottom),
            "estimated_loss": float(loss),
            "recovery_months": crisis["recovery_months"],
        }
    }


def run_full_stress_test(
    symbols: List[str],
    weights: List[float] = None,
    portfolio_value: float = 100000
) -> Optional[Dict[str, Any]]:
    """
    Run stress test on a portfolio against all historical crises.
    
    Args:
        symbols: List of stock symbols
        weights: Portfolio weights (optional, defaults to equal weight)
        portfolio_value: Total portfolio value
    """
    try:
        if not symbols:
            return None
        
        if weights is None:
            weights = [1.0 / len(symbols)] * len(symbols)
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Get current prices and validate
        portfolio_holdings = []
        for i, symbol in enumerate(symbols):
            df = _fetch_ohlcv(symbol, period="5d", interval="1d")
            if df is not None and not df.empty:
                price = float(df['close'].iloc[-1])
                value = portfolio_value * weights[i]
                sector = get_stock_sector(symbol)
                
                portfolio_holdings.append({
                    "symbol": symbol,
                    "weight": weights[i],
                    "value": value,
                    "current_price": price,
                    "sector": sector
                })
        
        if not portfolio_holdings:
            return None
        
        # Run stress tests for each crisis
        crisis_results = []
        
        for crisis_id, crisis_info in HISTORICAL_CRISES.items():
            total_portfolio_loss = 0
            stock_impacts = []
            
            for holding in portfolio_holdings:
                impact = calculate_crisis_impact(
                    holding["symbol"],
                    crisis_id,
                    holding["value"]
                )
                stock_impacts.append({
                    "symbol": holding["symbol"],
                    "loss": impact["portfolio_impact"]["estimated_loss"],
                    "drawdown_pct": impact["adjusted_drawdown_pct"]
                })
                total_portfolio_loss += impact["portfolio_impact"]["estimated_loss"]
            
            portfolio_drawdown = (total_portfolio_loss / portfolio_value) * 100
            
            crisis_results.append({
                "crisis_id": crisis_id,
                "crisis_name": crisis_info["name"],
                "period": f"{crisis_info['start_date']} to {crisis_info['end_date']}",
                "portfolio_drawdown_pct": float(portfolio_drawdown),
                "estimated_loss": float(total_portfolio_loss),
                "recovery_months": crisis_info["recovery_months"],
                "stock_impacts": stock_impacts,
            })
        
        # Sort by impact
        crisis_results.sort(key=lambda x: x["portfolio_drawdown_pct"])
        
        # Calculate risk metrics
        worst_case = crisis_results[0]
        avg_drawdown = np.mean([c["portfolio_drawdown_pct"] for c in crisis_results])
        
        # Value at Risk (historical simulation method)
        var_95 = np.percentile([c["portfolio_drawdown_pct"] for c in crisis_results], 5)
        
        # Sector concentration risk
        sectors = [h["sector"] for h in portfolio_holdings]
        sector_counts = {s: sectors.count(s) for s in set(sectors)}
        max_sector_concentration = max(sector_counts.values()) / len(sectors)
        
        if max_sector_concentration > 0.5:
            concentration_warning = f"High concentration in {max(sector_counts, key=sector_counts.get)} sector"
        else:
            concentration_warning = "Sector diversification adequate"
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "portfolio_value": portfolio_value,
            
            "holdings": portfolio_holdings,
            
            "stress_test_results": crisis_results,
            
            "risk_summary": {
                "worst_case_scenario": worst_case["crisis_name"],
                "worst_case_drawdown_pct": worst_case["portfolio_drawdown_pct"],
                "worst_case_loss": worst_case["estimated_loss"],
                "average_crisis_drawdown_pct": float(avg_drawdown),
                "var_95_pct": float(var_95),  # 95% of the time, loss won't exceed this
                "max_recovery_months": max(c["recovery_months"] for c in crisis_results),
            },
            
            "diversification_analysis": {
                "sector_breakdown": sector_counts,
                "max_concentration": float(max_sector_concentration),
                "warning": concentration_warning,
            },
            
            "recommendations": generate_portfolio_recommendations(
                crisis_results, 
                portfolio_holdings,
                max_sector_concentration
            ),
            
            "algorithm_version": "1.0.0",
            "methodology": "Historical crisis simulation with sector sensitivity adjustment"
        }
        
    except Exception:
        logger.exception("Failed portfolio stress test")
        return None


def generate_portfolio_recommendations(
    crisis_results: List[Dict],
    holdings: List[Dict],
    sector_concentration: float
) -> List[str]:
    """Generate actionable recommendations based on stress test."""
    recommendations = []
    
    worst_drawdown = abs(crisis_results[0]["portfolio_drawdown_pct"])
    
    if worst_drawdown > 40:
        recommendations.append("⚠️ HIGH RISK: Portfolio could lose >40% in severe crisis. Consider adding defensive sectors.")
    
    if sector_concentration > 0.6:
        recommendations.append("🔄 DIVERSIFY: Too concentrated in one sector. Add stocks from different sectors.")
    
    # Check for defensive holdings
    defensive_sectors = ["pharma", "fmcg"]
    has_defensive = any(h["sector"] in defensive_sectors for h in holdings)
    
    if not has_defensive:
        recommendations.append("🛡️ ADD DEFENSIVES: Include pharma or FMCG stocks for crisis protection.")
    
    if worst_drawdown > 30:
        recommendations.append("💰 MAINTAIN CASH: Consider 10-20% cash allocation for crisis buying opportunities.")
    
    if not recommendations:
        recommendations.append("✅ Portfolio has reasonable risk characteristics for various market scenarios.")
    
    return recommendations
