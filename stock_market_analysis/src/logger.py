"""Logger configuration."""
import logging
from logging import Logger


def setup_logger(
    name: str = "stock_market_analysis", level: int = logging.INFO
) -> Logger:
    """Configure and returns a logger with a specified name and level.

    Args:
    ----
        name (str): The name of the logger.
        level (int): The logging level, e.g., logging.INFO.

    Returns:
    -------
        Logger: A configured logger instance.

    The logger will output messages in the format: "2021-01-01 12:00:00,INFO,Sample message"
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False
    return logger

logger = setup_logger()
