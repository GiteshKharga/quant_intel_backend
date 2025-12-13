# app/resources/advanced_analytics.py
"""
API ENDPOINTS FOR ADVANCED ANALYTICS
====================================
All the novel features exposed via REST API.
"""

from flask_smorest import Blueprint
from flask.views import MethodView
from flask import request, current_app
from marshmallow import Schema, fields
from app.extensions import limiter, cache

blp = Blueprint("AdvancedAnalytics", "advanced", 
                description="Advanced quantitative analytics endpoints")


class SymbolQuerySchema(Schema):
    symbol = fields.Str(required=True, metadata={"description": "Stock symbol (e.g. AAPL, RELIANCE.NS)"})
    period = fields.Str(load_default="60d", metadata={"description": "Lookback period"})


class PortfolioSchema(Schema):
    symbols = fields.List(fields.Str(), required=True, 
                         metadata={"description": "List of stock symbols"})
    weights = fields.List(fields.Float(), required=False,
                         metadata={"description": "Portfolio weights (optional)"})
    portfolio_value = fields.Float(load_default=100000,
                                  metadata={"description": "Total portfolio value"})


# ---------------------------------------------------------
# LIQUIDITY DROUGHT PREDICTION
# ---------------------------------------------------------
@blp.route("/analytics/liquidity-drought")
class LiquidityDroughtResource(MethodView):
    
    @blp.arguments(SymbolQuerySchema, location="query")
    @limiter.limit("60/minute")
    def get(self, args):
        """Predict liquidity drought probability for a stock."""
        from app.services.liquidity_drought import predict_liquidity_drought
        from app.core.result import Result
        
        result = predict_liquidity_drought(
            args["symbol"],
            period=args.get("period", "60d")
        )
        
        # Check if result is a Result object (it should be)
        if isinstance(result, Result):
            if not result.success:
                return {"error": result.error}, 404
            return result.value
        
        # Fallback for non-Result return (backward compat)
        if result is None:
            return {"error": "Unable to analyze - no data available"}, 404
        
        return result



# ---------------------------------------------------------
# INTRADAY REGIME
# ---------------------------------------------------------
@blp.route("/analytics/intraday-regime")
class IntradayRegimeResource(MethodView):
    
    @blp.arguments(SymbolQuerySchema, location="query")
    @limiter.limit("60/minute")
    def get(self, args):
        """Detect current intraday market regime."""
        from app.services.intraday_regime import detect_intraday_regime
        
        result = detect_intraday_regime(
            args["symbol"],
            period="5d",
            interval="5m"
        )
        
        if result is None:
            return {"error": "Unable to analyze - no data available"}, 404
        
        return result


# ---------------------------------------------------------
# STRESS PROPAGATION
# ---------------------------------------------------------
@blp.route("/analytics/stress-propagation")
class StressPropagationResource(MethodView):
    
    @blp.arguments(SymbolQuerySchema, location="query")
    @limiter.limit("30/minute")
    def get(self, args):
        """Analyze cross-asset stress propagation."""
        from app.services.stress_propagation import analyze_stress_propagation
        
        result = analyze_stress_propagation(
            args["symbol"],
            period=args.get("period", "60d")
        )
        
        if result is None:
            return {"error": "Unable to analyze - no data available"}, 404
        
        return result


# ---------------------------------------------------------
# SENTIMENT VELOCITY
# ---------------------------------------------------------
@blp.route("/analytics/sentiment-velocity")
class SentimentVelocityResource(MethodView):
    
    @blp.arguments(SymbolQuerySchema, location="query")
    @limiter.limit("60/minute")
    def get(self, args):
        """Analyze sentiment velocity and manipulation risk."""
        from app.services.sentiment_velocity import analyze_sentiment_velocity
        
        result = analyze_sentiment_velocity(
            args["symbol"],
            days=30
        )
        
        if result is None:
            return {"error": "Unable to analyze - no data available"}, 404
        
        return result


# ---------------------------------------------------------
# NARRATIVE MOMENTUM
# ---------------------------------------------------------
@blp.route("/analytics/narrative-momentum")
class NarrativeMomentumResource(MethodView):
    
    @blp.arguments(SymbolQuerySchema, location="query")
    @limiter.limit("30/minute")
    def get(self, args):
        """Analyze market narrative lifecycle stage."""
        from app.services.narrative_momentum import analyze_narrative_momentum
        
        result = analyze_narrative_momentum(
            args["symbol"],
            period=args.get("period", "90d")
        )
        
        if result is None:
            return {"error": "Unable to analyze - no data available"}, 404
        
        return result


# ---------------------------------------------------------
# INSTITUTIONAL FLOW
# ---------------------------------------------------------
@blp.route("/analytics/institutional-flow")
class InstitutionalFlowResource(MethodView):
    
    @blp.arguments(SymbolQuerySchema, location="query")
    @limiter.limit("60/minute")
    def get(self, args):
        """Analyze retail vs institutional flow divergence."""
        from app.services.institutional_flow import analyze_institutional_flow
        
        result = analyze_institutional_flow(
            args["symbol"],
            period=args.get("period", "60d")
        )
        
        if result is None:
            return {"error": "Unable to analyze - no data available"}, 404
        
        return result


# ---------------------------------------------------------
# OPTIONS DANGER ZONES
# ---------------------------------------------------------
@blp.route("/analytics/options-danger-zones")
class OptionsDangerZonesResource(MethodView):
    
    @blp.arguments(SymbolQuerySchema, location="query")
    @limiter.limit("60/minute")
    def get(self, args):
        """Analyze options-implied danger zones and max pain."""
        from app.services.options_danger_zones import analyze_options_danger_zones
        
        result = analyze_options_danger_zones(
            args["symbol"],
            period=args.get("period", "60d")
        )
        
        if result is None:
            return {"error": "Unable to analyze - no data available"}, 404
        
        return result


# ---------------------------------------------------------
# MANIPULATION PATTERNS
# ---------------------------------------------------------
@blp.route("/analytics/manipulation-detection")
class ManipulationPatternResource(MethodView):
    
    @blp.arguments(SymbolQuerySchema, location="query")
    @limiter.limit("30/minute")
    def get(self, args):
        """Detect potential market manipulation patterns."""
        from app.services.pattern_recognition import analyze_manipulation_patterns
        
        result = analyze_manipulation_patterns(
            args["symbol"],
            period=args.get("period", "30d")
        )
        
        if result is None:
            return {"error": "Unable to analyze - no data available"}, 404
        
        return result


# ---------------------------------------------------------
# PORTFOLIO STRESS TEST
# ---------------------------------------------------------
@blp.route("/analytics/portfolio-stress-test", methods=["POST"])
class PortfolioStressTestResource(MethodView):
    
    @blp.arguments(PortfolioSchema)
    @limiter.limit("10/minute")
    def post(self, args):
        """
        Run portfolio stress test against historical crises.
        
        POST body:
        {
            "symbols": ["HDFCBANK.NS", "TCS.NS", "RELIANCE.NS"],
            "weights": [0.4, 0.3, 0.3],
            "portfolio_value": 100000
        }
        """
        from app.services.portfolio_stress import run_full_stress_test
        
        result = run_full_stress_test(
            symbols=args["symbols"],
            weights=args.get("weights"),
            portfolio_value=args.get("portfolio_value", 100000)
        )
        
        if result is None:
            return {"error": "Unable to run stress test - check symbols"}, 400
        
        return result


# ---------------------------------------------------------
# COMPREHENSIVE ANALYSIS (ALL IN ONE)
# ---------------------------------------------------------
@blp.route("/analytics/comprehensive")
class ComprehensiveAnalysisResource(MethodView):
    
    @blp.arguments(SymbolQuerySchema, location="query")
    @limiter.limit("10/minute")
    def get(self, args):
        """
        Run all analyses for a single stock.
        Returns a comprehensive report with all insights.
        """
        symbol = args["symbol"]
        
        comprehensive_result = {
            "symbol": symbol,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
            "analyses": {}
        }
        
        # Import all analyzers
        try:
            from app.services.liquidity_drought import predict_liquidity_drought
            comprehensive_result["analyses"]["liquidity_drought"] = predict_liquidity_drought(symbol)
        except Exception as e:
            comprehensive_result["analyses"]["liquidity_drought"] = {"error": str(e)}
        
        try:
            from app.services.institutional_flow import analyze_institutional_flow
            comprehensive_result["analyses"]["institutional_flow"] = analyze_institutional_flow(symbol)
        except Exception as e:
            comprehensive_result["analyses"]["institutional_flow"] = {"error": str(e)}
        
        try:
            from app.services.options_danger_zones import analyze_options_danger_zones
            comprehensive_result["analyses"]["options_zones"] = analyze_options_danger_zones(symbol)
        except Exception as e:
            comprehensive_result["analyses"]["options_zones"] = {"error": str(e)}
        
        try:
            from app.services.pattern_recognition import analyze_manipulation_patterns
            comprehensive_result["analyses"]["manipulation"] = analyze_manipulation_patterns(symbol)
        except Exception as e:
            comprehensive_result["analyses"]["manipulation"] = {"error": str(e)}
        
        try:
            from app.services.narrative_momentum import analyze_narrative_momentum
            comprehensive_result["analyses"]["narrative"] = analyze_narrative_momentum(symbol)
        except Exception as e:
            comprehensive_result["analyses"]["narrative"] = {"error": str(e)}
        
        try:
            from app.services.sentiment_velocity import analyze_sentiment_velocity
            comprehensive_result["analyses"]["sentiment"] = analyze_sentiment_velocity(symbol)
        except Exception as e:
            comprehensive_result["analyses"]["sentiment"] = {"error": str(e)}
        
        # Generate summary
        comprehensive_result["summary"] = generate_comprehensive_summary(comprehensive_result["analyses"])
        
        return comprehensive_result


def generate_comprehensive_summary(analyses: dict) -> dict:
    """Generate an overall summary from all analyses."""
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
