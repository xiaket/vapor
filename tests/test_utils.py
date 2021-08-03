#!/usr/bin/env python3
"""
Testing helpers in utils.py
"""
import logging

from vapor.utils import format_changes, format_name, get_logger, ColorFormatter


def test_format_name():
    """three typical cases."""
    assert format_name("TestStack") == "test-stack"
    assert format_name("TestAPIStack") == "test-api-stack"
    assert format_name("TestS3Stack") == "test-s3-stack"
    assert format_name("TestCloudformationS3Stack") == "test-cloudformation-s3-stack"


def test_color_logger(caplog, capsys):
    logger_name = "unit"
    logger = get_logger(logger_name)

    levels = ["info", "warning", "error", "critical"]
    for level in levels:
        getattr(logger, level)(level)

    records = caplog.record_tuples
    lines = capsys.readouterr().out.splitlines()

    for i, level in enumerate(levels):
        logging_level = getattr(logging, level.upper())
        assert records[i] == (logger_name, logging_level, level)
        expected_color = ColorFormatter.FORMATS[logging_level][:8]
        assert lines[i].startswith(expected_color)


def test_format_changes():
    change1 = {
        "ResourceChange": {
            "ResourceType": "AWS::EC2::Instance",
            "PhysicalResourceId": "i-1abc23d4",
            "Action": "Create",
            "LogicalResourceId": "MyEC2Instance",
            "Replacement": "False"
        },
        "Type": "Resource"
    }
    line1 = "[CREATE] MyEC2Instance(AWS::EC2::Instance)"
    formatted = format_changes([change1])
    assert formatted == line1

    change2 = {
        "ResourceChange": {
            "ResourceType": "AWS::EC2::Instance",
            "PhysicalResourceId": "i-1abc23d4",
            "Action": "Modify",
            "LogicalResourceId": "EC2",
            "Replacement": "False"
        },
        "Type": "Resource"
    }
    line2 = "[MODIFY] EC2(AWS::EC2::Instance)"
    formatted = format_changes([change1, change2])
    assert formatted == "\n".join([line1, line2])
