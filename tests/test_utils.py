#!/usr/bin/env python3
"""
Testing helpers in utils.py
"""
from vapor.utils import format_name


def test_format_name():
    """three typical cases."""
    assert format_name("TestStack") == "test-stack"
    assert format_name("TestAPIStack") == "test-api-stack"
    assert format_name("TestS3Stack") == "test-s3-stack"
