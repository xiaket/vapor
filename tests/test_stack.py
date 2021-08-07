#!/usr/bin/env python3
"""
Testing Stack model.

We will test stack attrs and cfn apis.
"""
import os
from unittest.mock import MagicMock

import boto3
import pytest
from moto import mock_cloudformation

# vapor generates modules on demand.
# pylint: disable=E0611
from vapor import S3, Stack


os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


class Bucket(S3.Bucket):
    """test S3 resource"""

    # This is our DSL, user don't have to define methods.
    # pylint: disable=R0903
    BucketName = "test"
    VersioningConfiguration = {"Status": "Suspended"}


class NewBucket(Bucket):
    """test S3 resource."""

    # This is our DSL, user don't have to define methods.
    # pylint: disable=R0903
    BucketName = "new-bucket-in-test"


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
        "Resources": {"Bucket": stack.Resources[0]().template},
    }

    # Resources cannot be empty.
    alt_stack = type("AnotherTestStack", (Stack,), {})()
    with pytest.raises(ValueError):
        print(alt_stack.template)


@mock_cloudformation
def test_stack_status():
    """Test stack status that comes from boto calls."""
    cfn = boto3.client("cloudformation")
    stack = S3Stack()
    cfn.create_stack(StackName=stack.name, TemplateBody=stack.json)
    assert stack.status == "CREATE_COMPLETE"
    assert stack.exists is True

    # This naming convention maps to cloudformation template elements.
    # pylint: disable=C0103
    stack.Resources = [Bucket, NewBucket]
    cfn.update_stack(
        StackName=stack.name,
        TemplateBody=stack.json,
    )

    assert stack.status == "UPDATE_COMPLETE"
    assert stack.exists is True

    cfn.delete_stack(StackName=stack.name)


@mock_cloudformation
def test_stack_create_changeset_new_stack():
    """Test create_change_set call with new stack."""
    cfn = boto3.client("cloudformation")
    stack = S3Stack()

    # testing this private method.
    # pylint: disable=E1101,W0212
    create_stack, name = stack._Stack__create_changeset()
    assert create_stack is True

    # At this time, the stack is created and it's in `REVIEW_IN_PROGRESS` state
    assert stack.exists is True
    assert stack.status == "REVIEW_IN_PROGRESS"

    response = cfn.describe_change_set(ChangeSetName=name, StackName=stack.name)
    assert response["Status"] == "CREATE_COMPLETE"
    assert len(response["Changes"]) == 1
    change = response["Changes"][0]["ResourceChange"]
    assert change["Action"] == "Add"
    assert change["LogicalResourceId"] == "Bucket"

    # Cleanup
    cfn.delete_change_set(ChangeSetName=name, StackName=stack.name)
    cfn.delete_stack(StackName=stack.name)


@mock_cloudformation
def test_stack_create_changeset_update():
    """Test create_change_set call."""
    cfn = boto3.client("cloudformation")
    stack = S3Stack()
    cfn.create_stack(StackName=stack.name, TemplateBody=stack.json)

    # modify bucket attribute
    stack.Resources[0].VersionControlConfiguration = {"Status": "Disabled"}

    # testing this private method.
    # pylint: disable=E1101,W0212
    create_stack, name = stack._Stack__create_changeset()
    assert create_stack is False
    response = cfn.describe_change_set(ChangeSetName=name, StackName=stack.name)
    assert response["Status"] == "CREATE_COMPLETE"
    assert len(response["Changes"]) == 1
    change = response["Changes"][0]["ResourceChange"]
    assert change["Action"] == "Modify"
    assert change["LogicalResourceId"] == "Bucket"

    # Cleanup
    cfn.delete_change_set(ChangeSetName=name, StackName=stack.name)
    cfn.delete_stack(StackName=stack.name)


@mock_cloudformation
def test_stack_create_changeset_complex_update():
    """Test create_change_set call with modification and addition."""
    cfn = boto3.client("cloudformation")
    stack = S3Stack()
    stack._Stack__deploy(dryrun=False, wait=True)

    # Change existing bucket while adding a new one
    Bucket.BucketName = "change-of-name"
    stack.Resources = [Bucket, NewBucket]

    # testing this private method.
    # pylint: disable=E1101,W0212
    create_stack, name = stack._Stack__create_changeset()
    assert create_stack is False
    response = cfn.describe_change_set(ChangeSetName=name, StackName=stack.name)
    assert response["Status"] == "CREATE_COMPLETE"
    assert len(response["Changes"]) == 2
    add_change = [
        change
        for change in response["Changes"]
        if change["ResourceChange"]["Action"] == "Add"
    ][0]
    modify_change = [
        change
        for change in response["Changes"]
        if change["ResourceChange"]["Action"] == "Modify"
    ][0]
    assert add_change["ResourceChange"]["LogicalResourceId"] == "NewBucket"
    assert modify_change["ResourceChange"]["LogicalResourceId"] == "Bucket"

    # Cleanup
    cfn.delete_change_set(ChangeSetName=name, StackName=stack.name)
    cfn.delete_stack(StackName=stack.name)


@mock_cloudformation
def test_stack_create_empty_changeset():
    """Test create empty changeset."""
    cfn = boto3.client("cloudformation")
    stack = S3Stack()
    cfn.create_stack(StackName=stack.name, TemplateBody=stack.json)
    assert stack.status == "CREATE_COMPLETE"
    assert stack.exists is True

    # testing this private method.
    # pylint: disable=E1101,W0212
    create_stack, name = stack._Stack__create_changeset()
    assert create_stack is False
    response = cfn.describe_change_set(ChangeSetName=name, StackName=stack.name)
    assert response["Status"] == "CREATE_COMPLETE"
    assert response.get("Changes", []) == []

    # Cleanup
    cfn.delete_change_set(ChangeSetName=name, StackName=stack.name)
    cfn.delete_stack(StackName=stack.name)


@mock_cloudformation
def test_stack_wait_changeset():
    """Test wait changeset call."""
    stack = S3Stack()

    # testing this private method.
    # pylint: disable=E1101,W0212
    create_stack, name = stack._Stack__create_changeset()
    assert create_stack is True

    # testing this private method.
    # pylint: disable=E1101,W0212
    changes = stack._Stack__wait_changeset(name)
    assert changes == [
        {
            "ResourceChange": {
                "Action": "Add",
                "LogicalResourceId": "Bucket",
                "ResourceType": "AWS::S3::Bucket",
            },
            "Type": "Resource",
        }
    ]


@mock_cloudformation
def test_stack_dunder_deploy_dryrun():
    """Test stack deploy with dryrun."""
    stack = S3Stack()

    # Dry run should work.
    # testing this private method.
    # pylint: disable=E1101,W0212
    stack._Stack__deploy(dryrun=True, wait=False)
    assert stack.exists is False


@mock_cloudformation
def test_stack_dunder_deploy_wetrun():
    """Test stack deploy with wetrun."""
    cfn = boto3.client("cloudformation")
    stack = S3Stack()

    # testing this private method.
    # pylint: disable=E1101,W0201,W0212,C0103
    stack._Stack__wait_stack = MagicMock(return_value=None)
    # pylint: disable=E1101,W0212
    stack._Stack__deploy(dryrun=False, wait=True)
    assert stack.status == "CREATE_COMPLETE"
    stack._Stack__wait_stack.assert_called()

    # cleanup
    cfn.delete_stack(StackName=stack.name)


@mock_cloudformation
def test_stack_dunder_deploy_empty_update():
    """Test stack deploy with empty updates."""
    cfn = boto3.client("cloudformation")
    stack = S3Stack()

    cfn.create_stack(StackName=stack.name, TemplateBody=stack.json)
    assert stack.status == "CREATE_COMPLETE"
    assert stack.exists is True

    stack.client.execute_change_set = MagicMock(return_value=None)
    stack.client.delete_change_set = MagicMock(return_value=None)
    # testing this private method.
    # pylint: disable=E1101,W0212
    stack._Stack__deploy(dryrun=False, wait=False)

    # These two methods shouldn't have been called
    # because the changeset is empty.
    stack.client.execute_change_set.assert_not_called()
    stack.client.delete_change_set.assert_not_called()

    # cleanup
    cfn.delete_stack(StackName=stack.name)


@mock_cloudformation
def test_stack_dunder_deploy_update():
    """Test stack deploy with updates."""
    cfn = boto3.client("cloudformation")
    stack = S3Stack()
    cfn.create_stack(StackName=stack.name, TemplateBody=stack.json)

    # Add a bucket into the stack
    stack.Resources = [Bucket, NewBucket]

    assert stack.status == "CREATE_COMPLETE"
    # Testing private method in class
    # pylint: disable=E1101,W0212
    stack._Stack__deploy(dryrun=False, wait=True)
    assert stack.status == "UPDATE_COMPLETE"

    # cleanup
    cfn.delete_stack(StackName=stack.name)
