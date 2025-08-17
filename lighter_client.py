import time
from typing import Optional

import pandas as pd

from lighter.configuration import Configuration
from lighter.api_client import ApiClient
from lighter.api import CandlestickApi
from lighter.signer_client import SignerClient

from config import (
    BASE_URL,
    PRIVATE_KEY,
    ACCOUNT_INDEX,
    API_KEY_INDEX,
    MARKET_ID,
    RESOLUTION,
)

_INTERVAL_MS = {
    "1m": 60_000,
    "5m": 5 * 60_000,
    "1h": 60 * 60_000,
}


class LighterClient:
    """Wrapper around official lighter-sdk APIs."""

    def __init__(self):
        cfg = Configuration(host=BASE_URL)
        self.api_client = ApiClient(cfg)
        self.candle_api = CandlestickApi(self.api_client)
        self.signer = SignerClient(
            url=BASE_URL,
            private_key=PRIVATE_KEY,
            api_key_index=API_KEY_INDEX,
            account_index=ACCOUNT_INDEX,
        )

    async def fetch_candles(self, count_back: int = 1000, end_time: Optional[int] = None) -> pd.DataFrame:
        """Download OHLCV candlesticks."""
        if end_time is None:
            end_time = int(time.time() * 1000)
        interval = _INTERVAL_MS[RESOLUTION]
        start = end_time - count_back * interval
        resp = await self.candle_api.candlesticks(
            market_id=MARKET_ID,
            resolution=RESOLUTION,
            start_timestamp=start,
            end_timestamp=end_time,
            count_back=count_back,
            set_timestamp_to_end=True,
        )
        data = [
            [c.timestamp, c.open, c.high, c.low, c.close, c.volume]
            for c in resp.candlesticks
        ]
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    async def create_market_order(self, side: str, base_amount: float, avg_price: float):
        """Place market order via SignerClient."""
        is_ask = side.lower() == "sell"
        client_order_index = int(time.time() * 1000)
        tx, tx_hash, error = await self.signer.create_market_order(
            market_index=MARKET_ID,
            client_order_index=client_order_index,
            base_amount=str(base_amount),
            avg_execution_price=str(avg_price),
            is_ask=is_ask,
            reduce_only=False,
        )
        if error:
            raise RuntimeError(error)
        return tx_hash
