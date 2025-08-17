import asyncio
import datetime
import time
from collections import deque

import pandas as pd

from config import (
    CONFIG,
    STOP_LOSS_PCT,
    TRADE_QTY,
    EXIT_AFTER_BARS,
)
from lighter_client import LighterClient
from indicators import compute_rsi, compute_bollinger, get_csi, compute_csc, check_signal


async def fetch_history(client: LighterClient, total_bars: int) -> pd.DataFrame:
    limit = 1000
    end = None
    frames = []
    while len(frames) * limit < total_bars:
        df = await client.fetch_candles(count_back=limit, end_time=end)
        if df.empty:
            break
        frames.append(df)
        end = int(df["timestamp"].iloc[0].value / 1e6) - 1
    full = pd.concat(frames).drop_duplicates("timestamp").sort_values("timestamp")
    return full.reset_index(drop=True)


async def trading_loop():
    client = LighterClient()
    df = await fetch_history(client, CONFIG["total_bars"])
    entry_history = deque(maxlen=100)
    open_positions = []

    while True:
        now = datetime.datetime.utcnow()
        if now.minute % 5 == 0 and now.second < 5:
            latest_df = await client.fetch_candles(count_back=2)
            if len(latest_df) < 2:
                await asyncio.sleep(1)
                continue
            candle = latest_df.iloc[-2]
            df = pd.concat([df, candle.to_frame().T]).drop_duplicates("timestamp").tail(CONFIG["total_bars"])

            df = compute_bollinger(df)
            df = get_csi(df)
            df = compute_csc(df, CONFIG["min_cluster"], CONFIG["bull_quant"], CONFIG["bear_quant"])
            df = compute_rsi(df)
            df["signal"] = [None] + [check_signal(df.iloc[i], df.iloc[i - 1]) for i in range(1, len(df))]

            last = df.iloc[-2]
            signal = last["signal"]
            if signal in ["buy", "sell"]:
                entry_time = datetime.datetime.utcnow()
                if not any((entry_time - t).total_seconds() < 300 and s == signal for t, s in entry_history):
                    stop_price = last["close"] * (1 - STOP_LOSS_PCT if signal == "buy" else 1 + STOP_LOSS_PCT)
                    side = "sell" if signal == "sell" else "buy"
                    try:
                        await client.create_market_order(side, TRADE_QTY, last["close"])
                        entry_history.append((entry_time, signal))
                        open_positions.append({
                            "type": "long" if signal == "buy" else "short",
                            "entry_price": last["close"],
                            "stop_price": stop_price,
                            "entry_time": entry_time,
                        })
                    except Exception as e:
                        print("Order error", e)

            current_price = last["close"]
            to_remove = []
            for pos in open_positions:
                elapsed = (datetime.datetime.utcnow() - pos["entry_time"]).total_seconds()
                hit_stop = (
                    current_price <= pos["stop_price"] if pos["type"] == "long" else current_price >= pos["stop_price"]
                )
                if hit_stop or elapsed >= EXIT_AFTER_BARS * 5 * 60:
                    try:
                        await client.create_market_order(
                            "sell" if pos["type"] == "long" else "buy",
                            TRADE_QTY,
                            current_price,
                        )
                    except Exception as e:
                        print("Close error", e)
                    to_remove.append(pos)
            for p in to_remove:
                open_positions.remove(p)

        await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(trading_loop())
