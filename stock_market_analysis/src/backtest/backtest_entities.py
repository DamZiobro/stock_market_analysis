from typing import Literal, Optional

import pandas as pd
from pydantic import BaseModel, Field, PositiveInt


class TransactionLog(BaseModel):
    """Logs a stock transaction."""

    class Config:  # noqa: D106
        arbitrary_types_allowed = True

    date: pd.Timestamp
    ticker: str
    transaction: Literal["buy", "sell"]
    hold_shares_number: PositiveInt
    transaction_amount: float
    yield_amount: Optional[float] = Field(0.0)
    yield_percent: Optional[float] = Field(0.0)


class Holding(BaseModel):
    """Represents a stock currently held."""

    ticker: str
    buy_price: float
    shares: PositiveInt
    total_investment: float
