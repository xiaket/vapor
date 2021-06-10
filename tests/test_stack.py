#!/usr/bin/env python3
"""
Testing Stack model.

We will test stack attrs and cfn apis.
"""
import os

import pytest

# vapor generates modules on demand.
# pylint: disable=E0611
from vapor import S3, Stack


os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


class Bucket(S3.Bucket):
    """Test S3 resource"""

    # This is our DSL, user don't have to define methods.
    # pylint: disable=R0903
    BucketName = "test"
    VersionControlConfiguration = {"Status": "Enabled"}


class S3Stack(Stack):
    """Test stack"""
    Resources = [Bucket]
    Description = "Minimal stack with a single S3 bucket."


def test_stack_name():
    """Test stack name that comes from class name and DeployOptions."""
    stack = S3Stack()
    assert stack.name == "s3-stack"

    alt_stack = type(
        "AnotherTestStack",
        (Stack,),
        {"Resources": [Bucket]},
    )()
    assert alt_stack.name == "another-test-stack"

    alt_stack = type(
        "AnotherTestStack",
        (Stack,),
        {"Resources": [Bucket], "DeployOptions": {"name": "test"}},
    )()
    assert alt_stack.name == "test"


def test_stack_template():
    """Test stack template."""
    stack = S3Stack()
    assert stack.template == {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": [
            Bucket().template
        ],
    }

    # Resources cannot be empty.
    alt_stack = type("AnotherTestStack", (Stack,), {})()
    with pytest.raises(ValueError):
        print(alt_stack.template)
