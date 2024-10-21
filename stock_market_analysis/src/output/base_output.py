from abc import ABC, abstractmethod
from typing import Optional, TypeVar

import pandas as pd


Self = TypeVar("Self", bound="BaseOutput")


class BaseOutput(ABC):
    """Render and save data in selected output format."""

    @abstractmethod
    def render(self: Self, df: pd.DataFrame, filename: Optional[str] = None) -> None:
        """Render DataFrame as selected output (implemented in derived class)."""
