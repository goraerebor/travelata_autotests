import numpy as np
import pandas as pd
from scipy.stats import zscore

from config import BB_PERIOD, BB_STD, CONFIG


def compute_rsi(df: pd.DataFrame, period: int = 450) -> pd.DataFrame:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period, min_periods=1).mean()
    avg_loss = loss.rolling(period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    df["RSI"] = df["RSI"].fillna(method="bfill")
    return df


def compute_bollinger(df: pd.DataFrame) -> pd.DataFrame:
    df["ma"] = df["close"].rolling(BB_PERIOD).mean()
    df["std"] = df["close"].rolling(BB_PERIOD).std()
    df["upper"] = df["ma"] + BB_STD * df["std"]
    df["lower"] = df["ma"] - BB_STD * df["std"]
    return df


def get_csi(df: pd.DataFrame) -> pd.DataFrame:
    body = (df["close"] - df["open"]).abs()
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    body_ratio = body / rng
    direction = np.where(df["close"] > df["open"], 1, -1)
    vol_score = df["volume"] / df["volume"].rolling(50).max()
    range_z = zscore(df["high"] - df["low"]).clip(-3, 3)

    tr = pd.DataFrame({
        "hl": df["high"] - df["low"],
        "hc": (df["high"] - df["close"].shift(1)).abs(),
        "lc": (df["low"] - df["close"].shift(1)).abs(),
    }).max(axis=1)

    atr = tr.rolling(14).mean().bfill()
    df["CSI"] = direction * (0.5 * body_ratio + 0.3 * vol_score + 0.2 * range_z) / atr
    return df


def compute_csc(df: pd.DataFrame, min_cluster: int, bull_q: float, bear_q: float) -> pd.DataFrame:
    bull_thr = df["CSI"].quantile(bull_q)
    bear_thr = df["CSI"].quantile(bear_q)
    df["sentiment"] = np.where(
        df["CSI"] >= bull_thr,
        "bull",
        np.where(df["CSI"] <= bear_thr, "bear", "neutral"),
    )
    df["cluster_id"] = pd.Series(dtype="object")
    curr_type, curr_start, length = None, None, 0
    for i, s in df["sentiment"].items():
        if s == curr_type and s in ["bull", "bear"]:
            length += 1
        else:
            if curr_type in ["bull", "bear"] and length >= min_cluster:
                df.loc[curr_start : i - 1, "cluster_id"] = f"{curr_type}_{curr_start}"
            if s in ["bull", "bear"]:
                curr_type, curr_start, length = s, i, 1
            else:
                curr_type, length = None, 0
    if curr_type in ["bull", "bear"] and length >= min_cluster:
        df.loc[curr_start : df.index[-1], "cluster_id"] = f"{curr_type}_{curr_start}"
    return df


def check_signal(row: pd.Series, prev_row: pd.Series):
    if np.isnan(row["lower"]) or np.isnan(prev_row["CSI"]) or np.isnan(row["CSI"]):
        return None
    cluster = row["cluster_id"]
    if not isinstance(cluster, str):
        return None
    long_cond = (
        row["close"] < row["lower"]
        and row["CSI"] > 0
        and row["CSI"] > prev_row["CSI"]
        and cluster.startswith("bull")
        and row["RSI"] < CONFIG["rsi"]
    )
    short_cond = (
        row["close"] > row["upper"]
        and row["CSI"] < 0
        and row["CSI"] < prev_row["CSI"]
        and cluster.startswith("bear")
        and row["RSI"] > (100 - CONFIG["rsi"])
    )
    if long_cond:
        return "buy"
    if short_cond:
        return "sell"
    return None
