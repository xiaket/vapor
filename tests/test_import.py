#!/usr/bin/env python3
"""
Testing vapor-import mechanism.
"""
import ast

from vapor.__main__ import Resource


def test_resource_class_str():
    """Test resource class."""
    resource = Resource(
        "Bucket",
        {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "Bucketame": "test",
            },
        },
    )
    assert resource.logical_name == "Bucket"
    astobj = resource.astobj
    assert astobj.name == "Bucket"
    assert isinstance(astobj, ast.ClassDef)
    assert len(astobj.bases) == 1

    base = astobj.bases[0]
    assert isinstance(base, ast.Attribute)
    assert base.attr == "Bucket"
    assert base.value.id == "S3"

    body = astobj.body
    assert isinstance(body, list)
    assert len(body) == 1
    assert all(isinstance(item, ast.Assign) for item in body)
    assert {item.targets[0].id for item in body} == {
        "Bucketame",
    }


def test_resource_class_dict():
    """Test resource class."""
    resource = Resource(
        "Bucket",
        {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "Bucketame": "test",
                "VersioningConfiguration": {"Status": "Suspended"},
            },
        },
    )
    body = resource.astobj.body
    assert isinstance(body, list)
    assert len(body) == 2
    assert all(isinstance(item, ast.Assign) for item in body)
    assert {item.targets[0].id for item in body} == {
        "Bucketame",
        "VersioningConfiguration",
    }
    assert {type(item.value) for item in body} == {ast.Dict, ast.Constant}


def test_resource_class_list():
    """Test resource class."""
    resource = Resource(
        "Bucket",
        {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "Bucketame": "test",
                "Subnets": ["subnet-abcdefgh", "subnet-01234567", "subnet-89abcdef"],
            },
        },
    )
    body = resource.astobj.body
    assert isinstance(body, list)
    assert len(body) == 2
    assert all(isinstance(item, ast.Assign) for item in body)
    assert {item.targets[0].id for item in body} == {
        "Bucketame",
        "Subnets",
    }
    assert {type(item.value) for item in body} == {ast.List, ast.Constant}


def test_resource_class_ref():
    """Test resource class."""
    resource = Resource(
        "Bucket",
        {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "Bucketame": {"Ref": "test"},
            },
        },
    )
    assert resource.logical_name == "Bucket"
    body = resource.astobj.body
    assert isinstance(body, list)
    assert len(body) == 1
    assert isinstance(body[0].value, ast.Call)

    call = body[0].value
    assert isinstance(call.func, ast.Name)
    assert call.func.id == "Ref"
    assert isinstance(call.args, list)
    assert len(call.args) == 1
    assert call.args[0].value == "test"
