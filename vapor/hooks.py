#!/usr/bin/env python3
"""Default hooks provided by vapor."""
import json
import sys

from cfnlint.config import ConfigFileArgs
from cfnlint.core import get_rules, get_exit_code, get_formatter
from cfnlint.decode.cfn_json import CfnJSONDecoder
from cfnlint.runner import Runner
from jsonschema.exceptions import ValidationError

from .utils import get_logger


logger = get_logger(__name__)


def cleanup_rollback_complete(self, dryrun, wait):
    """Predeploy hook to delete last failed deployment."""
    if self.status == "ROLLBACK_COMPLETE":
        logger.info("Deleting stack in ROLLBACK_COMPLETE state.")
        if not dryrun:
            self.delete(dryrun, wait)


def read_cfnlint_config(default_region):
    """Read configuration files for cfn-lint."""
    try:
        config = ConfigFileArgs()
    except ValidationError as err:
        logger.error("Error parsing config file: %s", str(err))
        sys.exit(1)

    # set default values for certain attrs
    defaults = {
        "append_rules": [],
        "ignore_checks": [],
        "include_checks": [],
        "configure_rules": {},
        "include_experimental": False,
        "mandatory_checks": [],
        "custom_rules": "",
        "regions": [default_region],
        "mandatory_rules": [],
    }
    for key, value in defaults.items():
        if not hasattr(config, key):
            setattr(config, key, value)

    return config


def check_template_with_cfn_lint(self, _dryrun, _wait):
    """Predeploy hook to check template with cfn-lint."""
    config = read_cfnlint_config(default_region=self.region)
    filename = f"{self.name}.json"

    # these attrs are set in read_cfnlint_config if not defined from config file.
    # pylint: disable=E1101
    rules = get_rules(
        config.append_rules,
        config.ignore_checks,
        config.include_checks,
        config.configure_rules,
        config.include_experimental,
        config.mandatory_checks,
        config.custom_rules,
    )
    matches = Runner(
        rules,
        filename,
        json.loads(self.json, cls=CfnJSONDecoder),
        config.regions,
        mandatory_rules=config.mandatory_rules,
    ).run()
    exit_code = get_exit_code(matches)
    if exit_code != 0:
        formatter = get_formatter("parseable")
        print(formatter.print_matches(matches, rules, filename))
        sys.exit(exit_code)
