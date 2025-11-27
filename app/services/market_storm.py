# app/services/market_storm.py
from typing import Sequence, Dict
import numpy as np
from scipy.stats import genextreme, norm

def returns_from_prices(prices: Sequence[float]):
    p = np.array(prices, dtype=float)
    if p.size < 2:
        return np.array([])
    return np.diff(np.log(p))

def tail_probability_loss(returns, loss_threshold_pct, horizon_bars=5):
    """
    Estimate probability that return over horizon_bars will be less than -loss_threshold_pct.
    Simplified approach: assume returns iid over short horizon; fit gaussian/gev tail.
    returns: array of log returns
    loss_threshold_pct: e.g., 0.05 for 5% loss
    """
    if len(returns) < 20:
        # fallback using empirical
        emp = np.mean(returns < np.log(1 - loss_threshold_pct))
        return float(emp)
    # fit gaussian on returns for central part, but for tail use extreme value fit of negative tails
    neg = -np.sort(-returns)  # descending absolute
    # simple gaussian approx for horizon
    mu = np.mean(returns)
    sigma = np.std(returns, ddof=0) if np.std(returns, ddof=0) > 0 else 1e-6
    # approximate horizon normal
    horizon_mu = horizon_bars * mu
    horizon_sigma = np.sqrt(horizon_bars) * sigma
    z = (np.log(1 - loss_threshold_pct) - horizon_mu) / horizon_sigma
    p_norm = norm.cdf(z)  # probability return <= threshold
    # clamp and return
    return float(max(0.0, min(1.0, p_norm)))

def storm_probability(prices, loss_threshold_pct=0.05, horizon_bars=5):
    r = returns_from_prices(prices)
    p = tail_probability_loss(r, loss_threshold_pct, horizon_bars)
    return {"storm_probability": p, "loss_threshold": loss_threshold_pct, "horizon": horizon_bars}
