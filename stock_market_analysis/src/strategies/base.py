from typing import TypeVar

import pandas as pd


Self = TypeVar("Self", bound="BaseStrategy")


class BaseStrategy:
    """Base class for strategies, allowing plug-in of different indicators."""

    def apply(self: Self, data: pd.DataFrame):  # noqa: ARG002
        """Apply strategy to the stock data."""
        msg = "Strategy needs to implement 'apply' method."
        raise NotImplementedError(msg)
