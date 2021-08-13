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
                            {"Ref": "Environment"},
                            {
                                "Fn::Select": [
                                    "3",
                                    {"Fn::Split": ["-", {"Ref": "Namespace"}]},
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
    assert isinstance(call.func, ast.Attribute)
    assert isinstance(call.func.value, ast.Name)
    assert call.func.value.id == "Fn"
    assert call.func.attr == "Join"
    assert isinstance(call.args, list)
    print(ast.dump(call, indent=2))
    assert len(call.args) == 2
    assert isinstance(call.args[0], ast.Constant)
    assert call.args[0].value == "/"

    join_list = call.args[1]
    assert isinstance(join_list, ast.List)
    assert len(join_list.elts) == 4
    assert isinstance(join_list.elts[0], ast.Constant)
    assert join_list.elts[0].value == "private-app-example.com"
    assert isinstance(join_list.elts[3], ast.Constant)
    assert join_list.elts[3].value == "system-logs"

    assert isinstance(join_list.elts[1], ast.Call)
    assert join_list.elts[1].func.id == "Ref"
    assert join_list.elts[1].args[0].value == "Environment"

    select_call = join_list.elts[2]
    assert isinstance(select_call, ast.Call)
    assert isinstance(select_call.func, ast.Attribute)
    assert select_call.func.value.id == "Fn"
    assert select_call.func.attr == "Select"
    assert len(select_call.args) == 2
    assert select_call.args[0].value == "3"

    split_call = select_call.args[1]
    assert isinstance(split_call, ast.Call)
    assert isinstance(split_call.func, ast.Attribute)
    assert split_call.func.value.id == "Fn"
    assert split_call.func.attr == "Split"
    assert len(split_call.args) == 2
    assert split_call.args[0].value == "-"
    assert isinstance(split_call.args[1], ast.Call)
    assert split_call.args[1].func.id == "Ref"
    assert split_call.args[1].args[0].value == "Namespace"
