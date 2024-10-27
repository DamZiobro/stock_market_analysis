from abc import ABC, abstractmethod
from typing import TypeVar

import pandas as pd


Self = TypeVar("Self", bound="BaseDataProvider")


class BaseDataProvider(ABC):
    """Fetches stock data from different sources which are implemented in derived classes."""

    @abstractmethod
    def get_data(self: Self, ticker: str, period: str) -> pd.DataFrame:
        """Return dataframe containing data from implemented provider."""
