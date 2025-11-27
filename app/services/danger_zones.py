# app/services/danger_zones.py
from datetime import datetime
import logging
from typing import Optional, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

# reuse fetch from market_weather to ensure consistent source
from app.services.market_weather import _fetch_ohlcv, average_true_range

def pivot_support_resistance(df: pd.DataFrame) -> Dict[str, Any]:
    out = {"zones": []}
    # simple pivot detection using rolling window
    highs = df['high'].rolling(5, center=True).apply(lambda x: 1 if x[2] == x.max() else 0, raw=False)
    lows = df['low'].rolling(5, center=True).apply(lambda x: 1 if x[2] == x.min() else 0, raw=False)

    highs_idx = list(highs[highs == 1].index)
    lows_idx = list(lows[lows == 1].index)

    pivots = []
    for idx in highs_idx[-5:]:
        pivots.append(("res", float(df.loc[idx]['high'])))
    for idx in lows_idx[-5:]:
        pivots.append(("sup", float(df.loc[idx]['low'])))

    for kind, price in pivots:
        width = price * 0.002
        out["zones"].append({
            "type": "resistance" if kind == "res" else "support",
            "level": price,
            "low": price - width,
            "high": price + width
        })
    return out

def high_volume_events(df: pd.DataFrame, threshold_multiplier: float = 3.0) -> list:
    mean_vol = df['volume'].rolling(20).mean()
    recent = df.tail(60)
    events = []
    for idx, row in recent.iterrows():
        mv = mean_vol.loc[idx] if idx in mean_vol.index else None
        if mv is not None and row['volume'] > mv * threshold_multiplier:
            events.append({
                "ts": idx.isoformat(),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            })
    return events

def compute_danger_zones(symbol: str, period: str = "180d", interval: str = "1d") -> Optional[Dict[str, Any]]:
    df = _fetch_ohlcv(symbol, period=period, interval=interval)
    if df is None or df.empty:
        return None

    try:
        atr = average_true_range(df)
        latest_price = float(df['close'].iloc[-1])

        sr = pivot_support_resistance(df)
        hv = high_volume_events(df)

        danger_windows = []
        for z in sr['zones']:
            dist = min(abs(latest_price - z['level']) / z['level'], 1.0)
            if dist < 0.01:
                danger_windows.append({
                    "zone": z,
                    "reason": "price near pivot",
                    "distance_pct": dist * 100
                })

        recent_atr = float(df.tail(14)['high'].sub(df.tail(14)['low']).abs().mean())
        long_atr = float(df.tail(60)['high'].sub(df.tail(60)['low']).abs().mean()) if len(df) >= 60 else recent_atr
        vol_spike = recent_atr > long_atr * 1.6

        payload = {
            "symbol": symbol,
            "ts": datetime.utcnow().isoformat() + "Z",
            "price": latest_price,
            "atr": atr,
            "volatility_spike": bool(vol_spike),
            "support_resistance": sr['zones'],
            "high_volume_events": hv,
            "danger_windows": danger_windows
        }
        return payload
    except Exception:
        logger.exception("Failed to compute danger zones for %s", symbol)
        return None
