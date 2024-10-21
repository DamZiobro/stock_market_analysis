from pathlib import Path
from typing import Optional, TypeVar

import pandas as pd
from lightweight_charts import Chart

from stock_market_analysis.src.output.base_output import BaseOutput


Self = TypeVar("Self", bound="PlotOutput")


class PlotOutput(BaseOutput):
    """Outputs data as a plot for visual analysis."""

    def render(
        self: Self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        columns: Optional[list] = None,
    ) -> None:
        """Plot stock data along with selected indicators.

        Args:
        ----
            data (pd.DataFrame): Stock data with indicators.
            columns (list): List of columns to plot.
            filename (str): Optional file name to save the plot.
        """
        if columns is None:
            columns = []

        chart = Chart()
        chart.set(df)

        print(df)

        for column in columns:
            if column in df.columns:
                line_series = chart.create_line(column)
                line_series.set(df[[column]])

        # Render the chart
        if filename:
            chart.save(Path(filename))
        else:
            chart.show(block=True)
