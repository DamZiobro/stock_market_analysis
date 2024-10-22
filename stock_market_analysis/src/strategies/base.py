from abc import ABC, abstractmethod
from typing import TypeVar

import pandas as pd


Self = TypeVar("Self", bound="BaseStrategy")


class BaseStrategy(ABC):
    """Base class for strategies, allowing plug-in of different indicators."""

    @abstractmethod
    def apply(self: Self, data: pd.DataFrame):
        """Apply strategy to the stock data."""
