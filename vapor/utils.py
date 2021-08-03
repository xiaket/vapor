#!/usr/bin/env python3
"""
Utility functions used in vapor.
"""
import logging
import re
import sys


def format_name(name):
    """
    Generate a stack name from class name by converting camel case to dash case.
    Adapted from https://stackoverflow.com/questions/1175208/.

    This function is our best effort to provide a good stack name in Cloudformation.
    However, if you want to have fine-grained control, please specify the name field in
    DeployOptions in your Stack class.

    example: format_name("TestStack") == "test-stack"
    """
    name = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1-\2", name).lower()


class ColorFormatter(logging.Formatter):
    """Logging Formatter with color."""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(asctime)s] %(message)s <%(filename)s:%(lineno)d>"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(logging.DEBUG)

    handler.setFormatter(ColorFormatter())
    logger.addHandler(handler)
    return logger


def format_changes(changes):
    """
    Format changes so it will look better.

    ref on changeset:

    https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets-view.html
    """
    parts = []
    for change in changes:
        change_ = change["ResourceChange"]
        line = (
            f"[{change_['Action'].upper()}] "
            f"{change_['LogicalResourceId']}({change_['ResourceType']})"
        )
        if "Details" in change_ and change_["Details"]:
            line += f":\n\t{change_['Details']}"
        parts.append(line)
    return "\n".join(parts)
