# app/services/market_weather.py

from datetime import datetime
import logging
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# OPTIONAL DEPENDENCIES
# ---------------------------------------------------------
try:
    import yfinance as yf
    _HAS_YFINANCE = True
except Exception:
    _HAS_YFINANCE = False

try:
    from app.trading.alpaca_client import fetch_ohlcv_alpaca
    _HAS_ALPACA = True
except Exception:
    _HAS_ALPACA = False

# ------------------------------
# RISK MODELS (NEW)
# ------------------------------
try:
    from app.services.liquidity_vacuum import liquidity_vacuum_score
except Exception:
    liquidity_vacuum_score = None

try:
    from app.services.market_storm import storm_probability
except Exception:
    storm_probability = None

try:
    from app.services.danger_zones import compute_dzi
except Exception:
    compute_dzi = None


# ---------------------------------------------------------
# OHLCV FETCHER
# ---------------------------------------------------------
def _fetch_ohlcv(symbol: str, period: str = "60d", interval: str = "1d") -> Optional[pd.DataFrame]:
    try:
        if _HAS_YFINANCE:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval, auto_adjust=False)
            if df is None or df.empty:
                return None
            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            })
            return df[["open", "high", "low", "close", "volume"]]

        elif _HAS_ALPACA:
            return fetch_ohlcv_alpaca(symbol, timeframe=interval, limit=500)

        else:
            logger.warning("No market data provider available (yfinance or alpaca).")
            return None

    except Exception:
        logger.exception("Failed to fetch OHLCV for %s", symbol)
        return None


# ---------------------------------------------------------
# TECHNICAL INDICATORS
# ---------------------------------------------------------
def average_true_range(df: pd.DataFrame, n: int = 14) -> float:
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1).fillna(df["close"])

    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr = tr.rolling(n).mean()
    return float(atr.dropna().iloc[-1]) if not atr.dropna().empty else float(tr.iloc[-1])


def momentum_score(df: pd.DataFrame, short: int = 7, long: int = 30) -> float:
    short_ma = df["close"].rolling(short).mean().iloc[-1]

    if len(df) >= long:
        long_ma = df["close"].rolling(long).mean().iloc[-1]
    else:
        long_ma = df["close"].rolling(max(1, len(df) // 2)).mean().iloc[-1]

    if long_ma == 0:
        return 0.0

    return float((short_ma - long_ma) / long_ma)


def volatility_score(df: pd.DataFrame) -> float:
    returns = df["close"].pct_change().dropna()
    if returns.empty:
        return 0.0
    return float(returns.rolling(14).std().iloc[-1])


def liquidity_proxy(df: pd.DataFrame) -> float:
    v = df["volume"].iloc[-20:].mean() if len(df) >= 20 else df["volume"].mean()
    p = df["close"].iloc[-1]
    try:
        if p is None or p == 0:
            return 0.0
        return float(v / p)
    except Exception:
        return 0.0


# ---------------------------------------------------------
# MAIN ENGINE — MARKET WEATHER + RISK MODELS
# ---------------------------------------------------------
def compute_market_weather(symbol: str, period: str = "60d", interval: str = "1d") -> Optional[Dict[str, Any]]:
    df = _fetch_ohlcv(symbol, period=period, interval=interval)
    if df is None or df.empty:
        return None

    try:
        # ---------------------------------------
        # BASE WEATHER METRICS
        # ---------------------------------------
        atr = average_true_range(df)
        vol = volatility_score(df)
        mom = momentum_score(df)
        liq = liquidity_proxy(df)
        price = float(df["close"].iloc[-1])

        # Normalizers
        vol_norm = min(1.0, vol / 0.05)
        liq_norm = min(1.0, liq / 1e6)
        mom_norm = max(-1.0, min(1.0, mom * 5))

        # base weather score
        score = (
            (1 - vol_norm) * 0.5
            + min(1.0, liq_norm) * 0.3
            + (0.1 + mom_norm * 0.1)
        )
        safety_score = int(max(0, min(1.0, score)) * 100)

        if safety_score < 30:
            rec = "avoid"
        elif safety_score < 55:
            rec = "caution"
        elif safety_score < 75:
            rec = "ok"
        else:
            rec = "bullish"

        # Base output
        snapshot = {
            "symbol": symbol,
            "ts": datetime.utcnow().isoformat() + "Z",
            "price": price,
            "atr": atr,
            "volatility": vol,
            "momentum": mom,
            "liquidity": liq,
            "safety_score": safety_score,
            "recommendation": rec,
            "meta": {
                "vol_norm": vol_norm,
                "liq_norm": liq_norm,
                "mom_norm": mom_norm,
                "period": period,
                "interval": interval,
            },
        }

        # ---------------------------------------------------------
        # NEW — LIQUIDITY VACUUM
        # ---------------------------------------------------------
        if liquidity_vacuum_score:
            last_volumes = df["volume"].tail(30).tolist()
            snapshot["vacuum"] = liquidity_vacuum_score(last_volumes)
        else:
            snapshot["vacuum"] = None

        # ---------------------------------------------------------
        # NEW — MARKET STORM PROBABILITY
        # ---------------------------------------------------------
        if storm_probability:
            last_prices = df["close"].tail(50).tolist()
            snapshot["storm_probability"] = storm_probability(
                last_prices,
                loss_threshold_pct=0.05,
                horizon_bars=5,
            )
        else:
            snapshot["storm_probability"] = None

        # ---------------------------------------------------------
        # NEW — DANGER ZONE INDEX (DZI)
        # ---------------------------------------------------------
        if compute_dzi:
            snapshot["dzi_score"] = float(compute_dzi(symbol))
        else:
            snapshot["dzi_score"] = None

        # ---------------------------------------------------------
        # NEW — FINAL RISK AGGREGATION
        # ---------------------------------------------------------
        try:
            vac_component = snapshot["vacuum"]["vacuum_score"] if snapshot["vacuum"] else 0
            storm_component = (
                snapshot["storm_probability"]["storm_probability"]
                if snapshot["storm_probability"]
                else 0
            )
            dzi_component = snapshot["dzi_score"] or 0

            final_storm_score = (
                0.4 * storm_component
                + 0.3 * vac_component
                + 0.3 * dzi_component
            )

            snapshot["final_risk_score"] = float(min(1.0, max(0.0, final_storm_score)))

        except Exception:
            snapshot["final_risk_score"] = None
            logger.exception("Failed computing final risk score for %s", symbol)

        return snapshot

    except Exception:
        logger.exception("Failed to compute market weather for %s", symbol)
        return None
