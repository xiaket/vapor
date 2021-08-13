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


def assert_call_fn(call, name):
    """Common assertions in a Fn call test."""
    assert isinstance(call.func, ast.Attribute)
    assert isinstance(call.func.value, ast.Name)
    assert call.func.value.id == "Fn"
    assert call.func.attr == name


def assert_constant(obj, value):
    """Common assertions in a Constant test."""
    assert isinstance(obj, ast.Constant)
    assert obj.value == value


def test_cfn_functions():
    """Test instantiate resource class with complex cfn functions."""
    resource = Resource(
        "Bucket",
        {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "Bucketame": {
                    "Fn::Join": [
                        "/",
                        [
                            "private-app-example.com",
                            {"Fn::Sub": "${Environment}-suffix"},
                            {
                                "Fn::Select": [
                                    "3",
                                    {"Fn::Split": ["-", {"Ref": "Namespace"}]},
                                ]
                            },
                            {
                                "Fn::Select": [
                                    "0",
                                    {"Fn::GetAZs": {"Ref": "AWS::Region"}},
                                ]
                            },
                            "system-logs",
                        ],
                    ]
                }
            },
        },
    )
    assert resource.logical_name == "Bucket"
    body = resource.astobj.body
    assert isinstance(body, list)
    assert len(body) == 1
    assert isinstance(body[0].value, ast.Call)

    call = body[0].value
    assert_call_fn(call, "Join")
    assert isinstance(call.args, list)
    assert len(call.args) == 2
    assert_constant(call.args[0], "/")

    join_list = call.args[1]
    assert isinstance(join_list, ast.List)
    assert len(join_list.elts) == 5
    assert_constant(join_list.elts[0], "private-app-example.com")
    assert_constant(join_list.elts[4], "system-logs")

    assert_call_fn(join_list.elts[1], "Sub")
    assert join_list.elts[1].args[0].value == "${Environment}-suffix"

    select_call = join_list.elts[2]
    assert_call_fn(select_call, "Select")
    assert len(select_call.args) == 2
    assert_constant(select_call.args[0], "3")

    split_call = select_call.args[1]
    assert_call_fn(split_call, "Split")
    assert len(split_call.args) == 2
    assert_constant(split_call.args[0], "-")
    assert isinstance(split_call.args[1], ast.Call)
    assert split_call.args[1].func.id == "Ref"
    assert split_call.args[1].args[0].value == "Namespace"

    select_call = join_list.elts[3]
    assert_call_fn(select_call, "Select")
    assert len(select_call.args) == 2
    assert_constant(select_call.args[0], "0")

    getazs_call = select_call.args[1]
    assert_call_fn(getazs_call, "GetAZs")
    assert len(getazs_call.args) == 1
    assert isinstance(getazs_call.args[0], ast.Call)
    assert getazs_call.args[0].func.id == "Ref"
    assert getazs_call.args[0].args[0].value == "AWS::Region"
