#!/usr/bin/env python3
"""
Testing hooks.
"""
import json
import os
from types import SimpleNamespace

import pytest
from moto import mock_cloudformation
from moto.cloudformation import cloudformation_backend

# vapor generates modules on demand.
# pylint: disable=E0611
from vapor import S3, Stack
from vapor.hooks import check_template_with_cfn_lint


os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

TEMPLATE = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Resources": {
        "Bucket": {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": "test",
                "VersioningConfiguration": {"Status": "Suspended"},
            },
        }
    },
}

class Bucket(S3.Bucket):
    """test S3 resource"""

    # This is our DSL, user don't have to define methods.
    # pylint: disable=R0903
    BucketName = "test"
    VersioningConfiguration = {"Status": "Suspended"}


class S3Stack(Stack):
    """Test stack"""

    Resources = [Bucket]
    Description = "Minimal stack with a single S3 bucket."


def test_cfn_lint():
    """test running cfn-lint"""
    good_template = TEMPLATE.copy()
    fake_stack = SimpleNamespace()
    fake_stack.region = "us-east-1"
    fake_stack.name = "test-cfn"
    fake_stack.json = json.dumps(good_template)

    # This should be fine.
    check_template_with_cfn_lint(fake_stack, True, True)

    bad_template = TEMPLATE.copy()
    bad_template["Resources"]["Bucket"]["Properties"]["Invalid"] = True
    fake_stack.json = json.dumps(bad_template)
    with pytest.raises(SystemExit) as wrapper_exit:
        check_template_with_cfn_lint(fake_stack, True, True)
        assert wrapper_exit.type == SystemExit
        assert wrapper_exit.value.code == 2


@mock_cloudformation
def test_rollback_cleaner():
    """Test the rollback cleanup hook."""
    stack = S3Stack()

    # using an internal method to create the stack while not creating resources.
    # pylint: disable=E1101,W0212
    stack._Stack__create_changeset()
    backend_stack = list(cloudformation_backend.stacks.values())[0]
    backend_stack.status = "ROLLBACK_COMPLETE"
    stack.pre_deploy(dryrun=False, wait=True)
    assert stack.status == "DOES_NOT_EXIST"
