# app/services/liquidity_vacuum.py
from typing import Dict, Any
import numpy as np

def compute_volume_z(volume_series):
    arr = np.array(volume_series, dtype=float)
    if arr.size < 5:
        return 0.0
    m = arr.mean()
    s = arr.std(ddof=0) if arr.std(ddof=0) > 0 else 1.0
    return (arr[-1] - m) / s

def liquidity_vacuum_score(last_volumes, bid_ask_spread_proxy=None):
    """
    Returns score between 0 and 1 where 1 means strong vacuum (danger).
    last_volumes: list/array of historical volume (older .. newest)
    bid_ask_spread_proxy: float or None (if not available)
    """
    vol_z = compute_volume_z(last_volumes)
    # vacuum when last volume is much lower than mean -> negative vol_z
    vacuum_factor = max(0.0, -vol_z) / 4.0  # scale; -4 sigma => 1.0
    spread_factor = 0.0
    if bid_ask_spread_proxy is not None:
        # scale spread to reasonable range: assume typical spread ~ small
        spread_factor = min(1.0, bid_ask_spread_proxy / 0.01)  # tune as necessary
    # final score
    score = min(1.0, vacuum_factor * 0.7 + spread_factor * 0.3)
    return {
        "vacuum_score": float(score),
        "volume_z": float(vol_z),
        "spread_proxy": float(bid_ask_spread_proxy or 0.0)
    }
