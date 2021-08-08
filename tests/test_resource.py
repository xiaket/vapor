#!/usr/bin/env python3
"""
Testing Resource model.

We will define an S3 resource and check it's properties.
"""
import pytest

# vapor generates modules on demand.
# pylint: disable=E0611
from vapor import S3, Ref
from vapor.models import replace_fn


class Bucket(S3.Bucket):
    """Test S3 resource"""

    # This is our DSL, user don't have to define methods.
    # pylint: disable=R0903
    BucketName = "test"
    VersioningConfiguration = {"Status": "Suspended"}


def test_resource_attrs():
    """Test S3 resource attrs."""
    resource = Bucket()
    # Checking class attributes.
    assert resource.BucketName == "test"
    assert resource.VersioningConfiguration == {"Status": "Suspended"}

    # Checking dynamic attributes.
    assert resource.resource_type == "AWS::S3::Bucket"
    assert resource.logical_name == "Bucket"
    assert resource.properties == {
        "BucketName": "test",
        "VersioningConfiguration": {"Status": "Suspended"},
    }
    assert resource.template == {
        "Properties": {
            "BucketName": "test",
            "VersioningConfiguration": {"Status": "Suspended"},
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
    assert resource.VersioningConfiguration == {"Status": "Suspended"}

    # Checking dynamic attributes.
    assert resource.logical_name == "S3Bucket"
    assert resource.resource_type == "AWS::S3::Bucket"
    assert resource.properties == {
        "BucketName": "test-again",
        "VersioningConfiguration": {"Status": "Suspended"},
    }
    assert resource.template == {
        "Properties": {
            "BucketName": "test-again",
            "VersioningConfiguration": {"Status": "Suspended"},
        },
        "Type": "AWS::S3::Bucket",
    }


def test_replace_fn():
    """test the replace_fn function."""
    node = {
        "DictProp": {
            "Key": Ref("ParamA"),
            "ListValues": ["ValueA", 12, Ref("ParamB"), 35.3],
        },
        "ListProp": [
            "Value1",
            {"Key1": "Value2", "Key2": Ref("ParamC")},
            Ref("ParamD"),
        ],
        "NormalProp": Ref("ParamE"),
        "IntProp": 42,
        "FloatType": 3.14,
    }
    replaced = replace_fn(node)
    assert replaced == {
        "DictProp": {
            "Key": {"Ref": "ParamA"},
            "ListValues": ["ValueA", 12, {"Ref": "ParamB"}, 35.3],
        },
        "FloatType": 3.14,
        "IntProp": 42,
        "ListProp": [
            "Value1",
            {"Key1": "Value2", "Key2": {"Ref": "ParamC"}},
            {"Ref": "ParamD"},
        ],
        "NormalProp": {"Ref": "ParamE"},
    }

    with pytest.raises(ValueError):
        replace_fn({"class": Bucket()})
