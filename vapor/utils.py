#!/usr/bin/env python3
"""
Utility functions used in vapor.
"""
import re


def format_name(name):
    """
    Generate a stack name from class name by converting camel case to dash case.
    Adapted from https://stackoverflow.com/questions/1175208/.

    This function is our best effort to provide a good stack name in Cloudformation.
    However, if you want to have fine-grained control, please specify the name field in
    DeployOptions in your Stack class.

    >>> format_name("TestStack") == "test-stack"
    >>> format_name("TestAPIStack") == "test-api-stack"
    >>> format_name("TestS3Stack") == "test-s3-stack"
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', name).lower()
