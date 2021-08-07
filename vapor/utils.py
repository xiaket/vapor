#!/usr/bin/env python3
"""
Utility functions used in vapor.
"""
import logging
import sys


class ColorFormatter(logging.Formatter):
    """Logging Formatter with color."""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    log_format = "[%(asctime)s] %(message)s <%(filename)s:%(lineno)d>"

    FORMATS = {
        logging.DEBUG: grey + log_format + reset,
        logging.INFO: grey + log_format + reset,
        logging.WARNING: yellow + log_format + reset,
        logging.ERROR: red + log_format + reset,
        logging.CRITICAL: bold_red + log_format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def get_logger(name):
    """create a colorful logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(logging.DEBUG)

    handler.setFormatter(ColorFormatter())
    logger.addHandler(handler)
    return logger
