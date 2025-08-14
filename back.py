import asyncio
import pandas as pd

from config import CONFIG, STOP_LOSS_PCT
from lighter_client import LighterClient
from indicators import (
    compute_rsi,
    compute_bollinger,
    get_csi,
    compute_csc,
    check_signal,
)


async def fetch_history(client: LighterClient, total_bars: int = 100000) -> pd.DataFrame:
    limit = 1000
    end = None
    dfs = []
    while len(dfs) * limit < total_bars:
        df = await client.fetch_candles(count_back=limit, end_time=end)
        if df.empty:
            break
        dfs.append(df)
        end = int(df["timestamp"].iloc[0].value / 1e6) - 1
    full = pd.concat(dfs).drop_duplicates("timestamp").sort_values("timestamp")
    return full.reset_index(drop=True)


async def run_backtest():
    client = LighterClient()
    df = await fetch_history(client)
    df = compute_rsi(df)
    df = compute_bollinger(df)
    df = get_csi(df)
    df = compute_csc(df, CONFIG["min_cluster"], CONFIG["bull_quant"], CONFIG["bear_quant"])

    signals = [None]
    for i in range(1, len(df)):
        signals.append(check_signal(df.iloc[i], df.iloc[i - 1]))
    df["signal"] = signals

    in_position = False
    entry_price = entry_idx = None
    pos_type = None
    trades = []

    for i in range(1, len(df)):
        row = df.iloc[i]
        sig = row["signal"]
        if not in_position and sig in ["buy", "sell"]:
            in_position = True
            entry_idx = i
            entry_price = row["close"]
            pos_type = "long" if sig == "buy" else "short"
            stop_price = (
                entry_price * (1 - STOP_LOSS_PCT)
                if pos_type == "long"
                else entry_price * (1 + STOP_LOSS_PCT)
            )
        elif in_position:
            exit_idx = entry_idx + 15
            hit_stop = (
                row["low"] <= stop_price if pos_type == "long" else row["high"] >= stop_price
            )
            if hit_stop or i >= exit_idx:
                exit_price = stop_price if hit_stop else row["close"]
                pnl = (
                    (exit_price - entry_price) / entry_price * 100
                    if pos_type == "long"
                    else (entry_price - exit_price) / entry_price * 100
                )
                trades.append(
                    {
                        "entry_time": df.iloc[entry_idx]["timestamp"],
                        "exit_time": row["timestamp"],
                        "side": pos_type,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_%": pnl,
                        "reason": "stop_loss" if hit_stop else "time_exit",
                    }
                )
                in_position = False

    tdf = pd.DataFrame(trades)
    tdf.to_csv("trades_complete.csv", sep=";", index=False)
    print(tdf.tail(10))
    print("Total PnL:", round(tdf["pnl_%"].sum(), 2), "%")


if __name__ == "__main__":
    asyncio.run(run_backtest())
