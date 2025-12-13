
import sys
import os
from app import create_app
from app.services.liquidity_drought import predict_liquidity_drought
from app.services.institutional_flow import analyze_institutional_flow
from app.services.options_danger_zones import analyze_options_danger_zones
from app.services.pattern_recognition import analyze_manipulation_patterns

def verify_symbol(symbol):
    print(f"\n{'='*50}")
    print(f"🕵️  ANALYZING LIVE MARKET DATA: {symbol}")
    print(f"{'='*50}")
    
    app = create_app()
    with app.app_context():
        # 1. Liquidity Check
        from app.core.result import Result
        liq_res = predict_liquidity_drought(symbol)
        liq = None
        if isinstance(liq_res, Result):
            if liq_res.success:
                liq = liq_res.value
            else:
                print(f"   ❌ Liquidity Check Failed: {liq_res.error}")
        else:
            liq = liq_res

        if liq:
            print(f"\n💧 LIQUIDITY CHECK:")
            print(f"   - Drought Probability: {liq['drought_probability']:.2%}")
            print(f"   - Status: {liq['risk_level']}")
            if liq['drought_probability'] > 0.5:
                print("   ❌ WARNING: Do not enter large positions!")
            else:
                print("   ✅ Safe to trade size.")


        # 2. Institutional Flow
        flow = analyze_institutional_flow(symbol)
        if flow:
            print(f"\n🐳 INSTITUTIONAL FLOW:")
            print(f"   - Market Type: {flow['flow_analysis']['market_type']}")
            div = flow['divergence']
            if div['divergence_detected']:
                print(f"   🚨 SIGNAL: {div['type']} DIVERGENCE DETECTED!")
                print(f"      {div['interpretation']}")
            else:
                print("   - No divergence (Retail & Institutions agree)")

        # 3. Manipulation Scan
        manip = analyze_manipulation_patterns(symbol)
        if manip:
            print(f"\n🕵️ MANIPULATION SCAN:")
            print(f"   - Risk Level: {manip['manipulation_risk']['level']}")
            if manip['patterns_detected']:
                print(f"   ⚠️  PATTERNS FOUND: {[p['pattern'] for p in manip['patterns_detected']]}")
            else:
                print("   ✅ No manipulation patterns found.")

        # 4. Profit Opportunity
        print(f"\n💰 REAL-WORLD PROFIT CHECK:")
        score = 0
        if liq and liq['risk_level'] == 'LOW': score += 1
        if flow and "INSTITUTIONAL" in flow['flow_analysis']['market_type']: score += 1
        if manip and manip['manipulation_risk']['level'] == 'LOW': score += 1
        
        if score == 3:
            print("   🟢 VERDICT: HIGH QUALITY SETUP (Institutions in, Safe, Liquid)")
        elif score == 0:
            print("   🔴 VERDICT: TOXIC ASSET (Avoid)")
        else:
            print("   🟡 VERDICT: MIXED SIGNALS (Trade cautiously)")

if __name__ == "__main__":
    verify_symbol("AAPL")        # Global Tech
    verify_symbol("RELIANCE.NS") # Indian Bluechip
    verify_symbol("IDEA.NS")     # Indian Speculative (Vodafone Idea)
