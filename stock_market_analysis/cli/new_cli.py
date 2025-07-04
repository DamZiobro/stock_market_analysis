"""Interface for command line tool."""

import importlib
from typing import Optional

import click
import pandas as pd
from joblib import Parallel, delayed

from stock_market_analysis.src.analysis.filtering import FilterBy
from stock_market_analysis.src.analysis.sorting import SortBy
from stock_market_analysis.src.backtest.backtest_service import BacktestService
from stock_market_analysis.src.logger import logger
from stock_market_analysis.src.services.bb_rsi_service import BBAndRSIAndMAService
from stock_market_analysis.src.services.bb_service import BBBaseService
from stock_market_analysis.src.services.four_ps_service import FourPSService
from stock_market_analysis.src.services.macd_rsi_service import MACD3DaysRSIService
from stock_market_analysis.src.services.macd_service import MACDBaseService
from stock_market_analysis.src.services.rsi_service import RSIBaseService
from stock_market_analysis.src.services.sup_res_service import SupportResistanceService
from stock_market_analysis.src.services.ten_days_service import TenDaysLowsHighsService
from stock_market_analysis.src.services.trend_based_service import TrendBasedService
from stock_market_analysis.src.utils.utils import parse_filters_input, parse_sort_input


PATH_TO_FTSE_CSV = "stock_market_analysis/data/all_uk_indexed.csv"


@click.group()
def tech_analysis():
    """CLI command group."""


@tech_analysis.command()
def version():
    """Return version of this tool."""
    click.echo(importlib.metadata.version("stock_market_analysis"))


@tech_analysis.command()
@click.option("--ticker", help="Stock ticker symbol to analyze.", default=None)
@click.option(
    "--file",
    help=f"File containing list of tickers to analyze. Defaults to: {PATH_TO_FTSE_CSV}",
    default=PATH_TO_FTSE_CSV,
)
@click.option(
    "--period",
    default="1y",
    help="Data period (e.g., '1y', '6mo', or '2023-01-01:2024-01-01')",
)
@click.option("--output", default="csv", help="Output format: csv, json, plot")
@click.option("--save", default=False, help="Save output to file?")
@click.option(
    "--service",
    default="RSIBase",
    help="Selected technical analysis ex. RSIAnalysis",
)
@click.option(
    "--limit",
    default=100,
    help="Limit maximum number of output rows.",
)
@click.option(
    "--order-by",
    default="",
    help="Output data sorting order ex. 'Date[desc],macd,rsi'",
)
@click.option(
    "--filters",
    default="",
    help="Filter by criteria. ex 'rsi_meaning=oversold,macd_raw_signal=buy'",
)
@click.option(
    "--backtest",
    default=False,
    help="Should backtesting be triggered?",
)
@click.option(
    "--backtest-amounts",
    default="4000,4000,3000,3000,3000,3000",
    help="Amounts to initially by shares for backtesting.",
)
def analyze(  # noqa: PLR0913, PLR0915
    ticker: Optional[str],
    file: Optional[click.Path],
    period: Optional[str],
    output: Optional[str],
    save: Optional[bool],
    service: Optional[str],
    limit: Optional[int],
    order_by: Optional[str],
    filters: Optional[str],
    backtest: Optional[bool],
    backtest_amounts: Optional[str],
):
    """CLI command to analyze stock based on ticker, output format, and period."""
    filters_dict = parse_filters_input(filters)

    tickers_df = pd.read_csv(file)

    # if filters can be apply before analysis (ex. filters based on CSV columns),
    # apply them to save analysis time
    before_analysis_filters = {
        key: filters_dict[key] for key in tickers_df.columns if key in filters_dict
    }
    print(f"{before_analysis_filters=}")
    tickers_df = FilterBy(filters=before_analysis_filters).apply(tickers_df)

    tickers = [ticker] if ticker is not None else tickers_df["Ticker"].tolist()

    if not tickers:
        msg = "Input filtering criteria selected 0 tickers to analyse."
        raise ValueError(msg)

    if service == "RSIBase":
        service_obj = RSIBaseService()  # type: ignore
    elif service == "MACDBase":
        service_obj = MACDBaseService()  # type: ignore
    elif service == "MACD3DaysRSI":
        service_obj = MACD3DaysRSIService()  # type: ignore
    elif service == "BBBase":
        service_obj = BBBaseService()  # type: ignore
    elif service == "BBAndRSI":
        service_obj = BBAndRSIAndMAService()  # type: ignore
    elif service == "TrendBased":
        service_obj = TrendBasedService()  # type: ignore
    elif service == "FourPS":
        service_obj = FourPSService()  # type: ignore
    elif service == "SupportResistance":
        service_obj = SupportResistanceService()  # type: ignore
    elif service == "TenDays":
        service_obj = TenDaysLowsHighsService()  # type: ignore
    else:
        msg = f"Unsupported service: {service}"
        raise ValueError(msg)

    # prepare filtering and sorting of output data
    service_obj.post_run_analysis_list.append(FilterBy(filters=filters_dict))

    sort_columns, sort_orders = parse_sort_input(order_by)
    service_obj.post_run_analysis_list.append(
        SortBy(columns=sort_columns, orders_asc=sort_orders)
    )

    results = Parallel(n_jobs=-1)(
        delayed(service_obj.run)(ticker, period) for ticker in tickers
    )
    logger.info("Contactenating results of the service: %s", service)
    result_df = pd.concat(results)

    # add StockIndex to result_df
    result_df = (
        result_df.reset_index()
        .merge(
            tickers_df[["Ticker", "Stock_Index"]],
            on="Ticker",
            how="left",
        )
        .set_index("Date")
    )

    logger.info("Triggering post-run service: %s", service)
    result_df = service_obj.post_run_analysis(result_df)

    # convert datetime-based index into 'Date' column
    result_df = result_df.reset_index().rename(columns={"index": "Date"})
    result_df = result_df.reset_index(drop=True)

    output_file = None
    if save:
        extension = "png" if output == "plot" else output
        output_file = f"{ticker}_rsi_analysis.{extension}"
    logger.info("Outting data of the service (max_rows=%d): %s", limit, service)

    # filter only selected 'limit' N number of rows
    limited_df = result_df.tail(limit)
    service_obj.output_data(limited_df, output, output_file)  # type: ignore

    if backtest and backtest_amounts:
        logger.info("=========================================================")
        logger.info(
            "Triggering backtesting with initial amounts: %s and period: %s",
            str(backtest_amounts),
            period,
        )
        int_amounts = [int(a) for a in backtest_amounts.split(",")]
        max_stock_amount = 5000
        min_stock_amount = 2000
        backtest_service = BacktestService(
            result_df, int_amounts, max_stock_amount, min_stock_amount, period
        )
        backtest_service.run()

        # Output the results
        logger.info("=================================")
        logger.info("BACKTEST LOG:")
        backtest_df = backtest_service.get_backtest_log()
        backtest_service.output_data(backtest_df, output, output_file)  # type: ignore

        logger.info("=================================")
        logger.info("PORTFOLIO VALUE:")
        portfolio_df = backtest_service.get_portfolio()
        backtest_service.output_data(portfolio_df, output, output_file)  # type: ignore
        print("=================================")
        return
