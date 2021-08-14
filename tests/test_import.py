#!/usr/bin/env python3
"""
Testing vapor-import mechanism.
"""
import ast
import json
import pathlib
import sys
import tempfile

import pytest

from vapor.__main__ import CfnTemplate, Resource, import_
from tests.fixtures import COMPLEX_RESOURCE, SIMPLE_JSON, SIMPLE_OUTPUT, SIMPLE_YAML


def test_resource_class_str():
    """Test resource class."""
    resource = Resource(
        "Bucket",
        {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": "test",
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
        "BucketName",
    }


def test_resource_class_invalid_type():
    """Test resource class."""
    resource = Resource(
        "Bucket",
        {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": ast.Name(id="Ref", ctx=ast.Load()),
            },
        },
    )
    with pytest.raises(ValueError) as err:
        _ = resource.astobj.code

    assert str(err.value).startswith("Invalid data type specified")


def test_resource_class_3rd_party():
    """Test resource class."""
    resource = Resource(
        "Bucket",
        {
            "Type": "Vapor::S3::Bucket",
            "Properties": {"BucketName": "test"},
        },
    )
    assert len(resource.astobj.body) == 2
    for assign in resource.astobj.body:
        if isinstance(assign.value, ast.Dict):
            assert len(assign.targets) == 1
            assert assign.targets[0].id == "Meta"
            assert len(assign.value.keys) == 1
            assert assign.value.keys[0].value == "provider"
            assert assign.value.values[0].value == "Vapor"


def test_resource_class_dict():
    """Test resource class."""
    resource = Resource(
        "Bucket",
        {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": "test",
                "VersioningConfiguration": {"Status": "Suspended"},
            },
        },
    )
    body = resource.astobj.body
    assert isinstance(body, list)
    assert len(body) == 2
    assert all(isinstance(item, ast.Assign) for item in body)
    assert {item.targets[0].id for item in body} == {
        "BucketName",
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
                "BucketName": "test",
                "Subnets": ["subnet-abcdefgh", "subnet-01234567", "subnet-89abcdef"],
            },
        },
    )
    body = resource.astobj.body
    assert isinstance(body, list)
    assert len(body) == 2
    assert all(isinstance(item, ast.Assign) for item in body)
    assert {item.targets[0].id for item in body} == {
        "BucketName",
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
                "BucketName": {"Ref": "test"},
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
    assert_ref(call, "test")


def assert_call_fn(call, name):
    """Common assertions in a Fn call."""
    assert isinstance(call.func, ast.Attribute)
    assert isinstance(call.func.value, ast.Name)
    assert call.func.value.id == "Fn"
    assert call.func.attr == name


def assert_ref(obj, target):
    """Common assertions in a Ref call."""
    assert obj.func.id == "Ref"
    assert isinstance(obj.args, list)
    assert len(obj.args) == 1
    assert obj.args[0].value == target


def assert_constant(obj, value):
    """Common assertions in a Constant."""
    assert isinstance(obj, ast.Constant)
    assert obj.value == value


def test_cfn_functions():
    """Test instantiate resource class with complex cfn functions."""
    body = Resource("Bucket", COMPLEX_RESOURCE).astobj.body
    assert isinstance(body, list) and len(body) == 1

    call = body[0].value
    assert isinstance(call, ast.Call)
    assert_call_fn(call, "Join")

    assert isinstance(call.args, list) and len(call.args) == 2
    assert_constant(call.args[0], "/")

    join_list = call.args[1]
    assert isinstance(join_list, ast.List) and len(join_list.elts) == 5
    assert_constant(join_list.elts[0], "private-app-example.com")
    assert_constant(join_list.elts[4], "system-logs")

    assert_call_fn(join_list.elts[1], "Sub")
    assert join_list.elts[1].args[0].value == "${Environment}-suffix"

    select_call = join_list.elts[2]
    assert_call_fn(select_call, "Select")
    const, split_call = select_call.args
    assert_constant(const, "3")

    assert_call_fn(split_call, "Split")
    assert len(split_call.args) == 2
    assert_constant(split_call.args[0], "-")
    assert isinstance(split_call.args[1], ast.Call)
    assert_ref(split_call.args[1], "Namespace")

    select_call = join_list.elts[3]
    assert_call_fn(select_call, "Select")
    assert len(select_call.args) == 2
    assert_constant(select_call.args[0], "0")

    getazs_call = select_call.args[1]
    assert_call_fn(getazs_call, "GetAZs")
    assert len(getazs_call.args) == 1
    assert isinstance(getazs_call.args[0], ast.Call)
    assert_ref(getazs_call.args[0], "AWS::Region")


def test_template_object():
    """test the template object"""
    cfn = CfnTemplate(SIMPLE_JSON)
    assert len(cfn.resources) == 1 and cfn.resources[0].logical_name == "Bucket"
    assert cfn.services == "S3"

    astobj = cfn.stack_ast
    assert isinstance(astobj, ast.ClassDef)
    assert astobj.name == "VaporStack"
    assert len(astobj.bases) == 1 and astobj.bases[0].id == "Stack"

    assert {item.targets[0].id for item in astobj.body} == {
        "Resources",
        "AWSTemplateFormatVersion",
    }


def test_render():
    """Test render/import_."""
    with tempfile.TemporaryDirectory() as dirname:
        tmpdir = pathlib.Path(dirname)
        filename = tmpdir / "test.json"
        with open(filename, "w") as fobj:
            fobj.write(json.dumps(SIMPLE_JSON))

        sys.argv = ["vapor-import", filename.as_posix()]
        import_()

        content = ""
        for name in tmpdir.iterdir():
            if name.suffix == ".py":
                content = name.read_text()
                break

        assert content != ""

    lines = lambda content: [l.strip() for l in content.splitlines() if l.strip()]
    assert lines(content) == lines(SIMPLE_OUTPUT.format(filename=filename.name))


def test_render_yaml():
    """Test render/import_."""
    with tempfile.TemporaryDirectory() as dirname:
        tmpdir = pathlib.Path(dirname)
        filename = tmpdir / "test.yml"
        with open(filename, "w") as fobj:
            fobj.write(SIMPLE_YAML)

        sys.argv = ["vapor-import", filename.as_posix()]
        import_()

        content = ""
        for name in tmpdir.iterdir():
            if name.suffix == ".py":
                content = name.read_text()
                break

        assert content != ""

    lines = lambda content: [l.strip() for l in content.splitlines() if l.strip()]
    assert lines(content) == lines(SIMPLE_OUTPUT.format(filename=filename.name))


def test_render_invalid_suffix():
    """Test import_ with invalid suffix"""
    with tempfile.TemporaryDirectory() as dirname:
        tmpdir = pathlib.Path(dirname)
        filename = tmpdir / "test.ml"
        filename.write_text("test")

        sys.argv = ["vapor-import", filename.as_posix()]
        with pytest.raises(ValueError) as err:
            import_()
        assert str(err.value).startswith("Please provide a Cloudformation template")
