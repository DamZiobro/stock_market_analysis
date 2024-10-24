import pandas as pd
from pydantic import BaseModel, PositiveInt


class TransactionLog(BaseModel):
    """Logs a stock transaction."""

    class Config:  # noqa: D106
        arbitrary_types_allowed = True

    date: pd.Timestamp
    ticker: str
    transaction: str
    close_price: float
    hold_shares_number: int
    transaction_amount: float
    available_cash: float
    total_value: float
    total_yield: float
    total_yield_percent: float


class Holding(BaseModel):
    """Represents a stock currently held."""

    ticker: str
    buy_price: float
    shares: PositiveInt
    total_investment: float
