
import logging
from datetime import datetime
import json
import numpy as np

# Mock functions with numpy types to simulate real issues
def mock_liquidity():
    return {"drought_probability": np.float64(0.5), "risk_level": "LOW"}

def mock_flow():
    return {"divergence": {"divergence_detected": np.bool_(False)}}

def mock_options():
    return {
        "danger_zones": [{"level": np.float64(100.0), "type": "psychological"}],
        "max_pain_estimate": {"estimated_level": np.float64(100.0)}
    }

def mock_manipulation():
    return {"manipulation_risk": {"level": "LOW"}}

def mock_narrative():
    return {}

def mock_sentiment():
    return {}

# The function to test
def generate_comprehensive_summary(analyses: dict) -> dict:
    warnings = []
    opportunities = []
    risk_score = 0
    
    # Check liquidity
    if analyses.get("liquidity_drought") and not analyses["liquidity_drought"].get("error"):
        if analyses["liquidity_drought"].get("drought_probability", 0) > 0.5:
            warnings.append("High liquidity drought risk")
            risk_score += 20
    
    # Check manipulation
    if analyses.get("manipulation") and not analyses["manipulation"].get("error"):
        manipulation_risk = analyses["manipulation"].get("manipulation_risk", {})
        if manipulation_risk.get("level") in ["HIGH", "CRITICAL"]:
            warnings.append("Potential manipulation patterns detected")
            risk_score += 30
    
    # Check flow divergence
    if analyses.get("institutional_flow") and not analyses["institutional_flow"].get("error"):
        divergence = analyses["institutional_flow"].get("divergence", {})
        if divergence.get("divergence_detected"):
            if divergence.get("type") == "BULLISH":
                opportunities.append("Bullish institutional divergence")
            else:
                warnings.append("Bearish institutional divergence")
                risk_score += 15
    
    # Overall rating
    if risk_score >= 50:
        overall = "HIGH_RISK"
        action = "AVOID"
    elif risk_score >= 30:
        overall = "ELEVATED_RISK"
        action = "CAUTION"
    elif len(opportunities) > len(warnings):
        overall = "OPPORTUNITY"
        action = "CONSIDER_ENTRY"
    else:
        overall = "NEUTRAL"
        action = "HOLD/MONITOR"
    
    return {
        "overall_rating": overall,
        "recommended_action": action,
        "risk_score": risk_score,
        "warnings": warnings,
        "opportunities": opportunities
    }

# Test execution
try:
    analyses = {
        "liquidity_drought": mock_liquidity(),
        "institutional_flow": mock_flow(),
        "options_zones": mock_options(),
        "manipulation": mock_manipulation(),
        "narrative": mock_narrative(),
        "sentiment": mock_sentiment()
    }
    
    # This simulates what Flask does
    summary = generate_comprehensive_summary(analyses)
    result = {
        "symbol": "TEST",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "analyses": analyses,
        "summary": summary
    }
    
    # Try to serialize
    json_output = json.dumps(result)
    print("Serialization successful")
    print(json_output)

except Exception as e:
    print(f"Error: {e}")
    # import traceback
    # traceback.print_exc()
