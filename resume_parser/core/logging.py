import logging
from typing import Optional

from pythonjsonlogger import jsonlogger


def configure_logging(settings: Optional[object] = None) -> None:
    level = logging.INFO
    if settings is not None:
        level = getattr(logging, getattr(settings, "LOG_LEVEL", "INFO"), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(event)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    root.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
