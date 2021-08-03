#!/usr/bin/env python3
"""
Testing Resource model.

We will define an S3 resource and check it's properties.
"""
# vapor generates modules on demand.
# pylint: disable=E0611
from vapor import S3


class Bucket(S3.Bucket):
    """Test S3 resource"""

    # This is our DSL, user don't have to define methods.
    # pylint: disable=R0903
    BucketName = "test"
    VersionControlConfiguration = {"Status": "Enabled"}


def test_resource_attrs():
    """Test S3 resource attrs."""
    resource = Bucket()
    # Checking class attributes.
    assert resource.BucketName == "test"
    assert resource.VersionControlConfiguration == {"Status": "Enabled"}

    # Checking dynamic attributes.
    assert resource.resource_type == "AWS::S3::Bucket"
    assert resource.logical_name == "Bucket"
    assert resource.properties == {
        "BucketName": "test",
        "VersionControlConfiguration": {"Status": "Enabled"},
    }
    assert resource.template == {
        "Properties": {
            "BucketName": "test",
            "VersionControlConfiguration": {"Status": "Enabled"},
        },
        "Type": "AWS::S3::Bucket",
    }


def test_resurce_inheritance():
    """Test S3 resource attrs with class inheritance and overwrite."""
    # Define a class that inherit Bucket and overwrite the BucketName.
    resource = type(
        "S3Bucket",
        (Bucket,),
        {"BucketName": "test-again"},
    )()
    # Checking class attributes.
    assert resource.BucketName == "test-again"
    assert resource.VersionControlConfiguration == {"Status": "Enabled"}

    # Checking dynamic attributes.
    assert resource.logical_name == "S3Bucket"
    assert resource.resource_type == "AWS::S3::Bucket"
    assert resource.properties == {
        "BucketName": "test-again",
        "VersionControlConfiguration": {"Status": "Enabled"},
    }
    assert resource.template == {
        "Properties": {
            "BucketName": "test-again",
            "VersionControlConfiguration": {"Status": "Enabled"},
        },
        "Type": "AWS::S3::Bucket",
    }
