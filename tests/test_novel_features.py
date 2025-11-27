# tests/test_novel_features.py
from app.services.liquidity_vacuum import liquidity_vacuum_score
from app.services.market_storm import storm_probability

def test_vacuum():
    vols = [100, 120, 110, 90, 10]  # sudden drop
    r = liquidity_vacuum_score(vols)
    assert r["vacuum_score"] > 0

def test_storm():
    prices = [100, 99, 97, 95, 90, 85, 80, 70]
    s = storm_probability(prices, loss_threshold_pct=0.05, horizon_bars=3)
    assert 0 <= s["storm_probability"] <= 1
