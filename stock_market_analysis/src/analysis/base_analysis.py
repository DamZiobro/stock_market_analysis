from abc import ABC, abstractmethod
from typing import TypeVar

import pandas as pd


Self = TypeVar("Self", bound="BaseAnalysis")


class BaseAnalysis(ABC):
    """Base class for post run analysis."""

    @abstractmethod
    def apply(self: Self, data: pd.DataFrame):
        """Apply analysis to the stock data."""
