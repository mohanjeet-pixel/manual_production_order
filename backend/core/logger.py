import logging
import os
from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)

_fmt = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def _file_handler(filename: str) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        f"logs/{filename}",
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    handler.setFormatter(_fmt)
    return handler


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_file_handler("app.log"))
        console = logging.StreamHandler()
        console.setFormatter(_fmt)
        logger.addHandler(console)
    return logger
