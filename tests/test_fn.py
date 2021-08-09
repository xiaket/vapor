#!/usr/bin/env python3
"""
Testing models that maps to Cloudformation functions.
"""
import pytest

from vapor.fn import replace_fn, Ref, Fn


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
        replace_fn({"class": set([])})


def test_base64():
    """Test Fn.Base64 function."""
    assert Fn.Base64("AWS CloudFormation").render() == {
        "Fn::Base64": "AWS CloudFormation"
    }


def test_cidr():
    """Test Fn.Cidr function."""
    assert Fn.Cidr("192.168.0.0/24", "6", "5").render() == {
        "Fn::Cidr": ["192.168.0.0/24", "6", "5"]
    }


def test_and():
    """Test Fn.And function."""
    assert Fn.And(
        Fn.Equals("sg-mysggroup", Ref("ASecurityGroup")),
        {"Condition": "SomeOtherCondition"},
    ).render() == {
        "Fn::And": [
            {"Fn::Equals": ["sg-mysggroup", {"Ref": "ASecurityGroup"}]},
            {"Condition": "SomeOtherCondition"},
        ],
    }


def test_equal():
    """Test Fn.Equals function."""
    assert Fn.Equals(Ref("EnvironmentType"), "prod").render() == {
        "Fn::Equals": [{"Ref": "EnvironmentType"}, "prod"]
    }


def test_if():
    """Test Fn.If function."""
    assert Fn.If(
        "CreateNewSecurityGroup",
        Ref("NewSecurityGroup"),
        Ref("ExistingSecurityGroup"),
    ).render() == {
        "Fn::If": [
            "CreateNewSecurityGroup",
            {"Ref": "NewSecurityGroup"},
            {"Ref": "ExistingSecurityGroup"},
        ]
    }
    assert Fn.If(
        "IsPublic",
        Fn.If(
            "IsPrelive",
            "prelive.example.com",
            "prod.example.com",
        ),
        Ref("AWS::NoValue"),
    ).render() == {
        "Fn::If": [
            "IsPublic",
            {
                "Fn::If": [
                    "IsPrelive",
                    "prelive.example.com",
                    "prod.example.com",
                ]
            },
            {"Ref": "AWS::NoValue"},
        ]
    }


def test_not():
    """Test Fn.Not function."""
    assert Fn.Not(Fn.Equals(Ref("EnvironmentType"), "prod")).render() == {
        "Fn::Not": [{"Fn::Equals": [{"Ref": "EnvironmentType"}, "prod"]}]
    }


def test_or():
    """Test Fn.Or function."""
    assert Fn.Or(
        Fn.Equals("sg-mysggroup", Ref("ASecurityGroup")),
        {"Condition": "SomeOtherCondition"},
    ).render() == {
        "Fn::Or": [
            {"Fn::Equals": ["sg-mysggroup", {"Ref": "ASecurityGroup"}]},
            {"Condition": "SomeOtherCondition"},
        ],
    }


def test_find_in_map():
    """Test Fn.FindInMap function."""
    assert Fn.FindInMap("RegionMap", Ref("AWS::Region"), "HVM64").render() == {
        "Fn::FindInMap": ["RegionMap", {"Ref": "AWS::Region"}, "HVM64"],
    }


def test_getatt():
    """Test Fn.GetAtt function."""
    assert Fn.GetAtt("myELB", "DNSName").render() == {
        "Fn::GetAtt": ["myELB", "DNSName"],
    }


def test_getazs():
    """Test Fn.GetAZs function."""
    assert Fn.GetAZs(Ref("AWS::Region")).render() == {
        "Fn::GetAZs": {"Ref": "AWS::Region"}
    }
    assert Fn.GetAZs("").render() == {"Fn::GetAZs": ""}


def test_importvalue():
    """Test Fn.ImportValue function."""
    assert Fn.ImportValue(
        Fn.Sub("${NetworkStackNameParameter}-SecurityGroupID")
    ).render() == {
        "Fn::ImportValue": {"Fn::Sub": "${NetworkStackNameParameter}-SecurityGroupID"}
    }


def test_join():
    """Test Fn.Join function."""
    assert Fn.Join(":", ["a", "b", "c"]).render() == {
        "Fn::Join": [":", ["a", "b", "c"]]
    }
    assert Fn.Join(":", ["arn:aws:iam", Ref("AWS::AccountId"), "root"]).render() == {
        "Fn::Join": [":", ["arn:aws:iam", {"Ref": "AWS::AccountId"}, "root"]]
    }
    assert Fn.Join(
        "/",
        [
            "/private/app/example.com",
            Ref("Environment"),
            Fn.Select("3", Fn.Split("-", Ref("Namespace"))),
            "system/logs",
        ],
    ).render() == {
        "Fn::Join": [
            "/",
            [
                "/private/app/example.com",
                {"Ref": "Environment"},
                {"Fn::Select": ["3", {"Fn::Split": ["-", {"Ref": "Namespace"}]}]},
                "system/logs",
            ],
        ]
    }


def test_select():
    """Test Fn.Select function."""
    assert Fn.Select("1", ["apples", "grapes", "oranges", "mangoes"]).render() == {
        "Fn::Select": ["1", ["apples", "grapes", "oranges", "mangoes"]]
    }


def test_split():
    """Test Fn.Split function."""
    assert Fn.Split("|", "a|b|c").render() == {"Fn::Split": ["|", "a|b|c"]}


def test_sub():
    """Test Fn.Sub function."""
    assert Fn.Sub(
        "${HostName}.${Domain}",
        {"Domain": Ref("RootDomainName"), "HostName": Ref("HostName")},
    ).render() == {
        "Fn::Sub": [
            "${HostName}.${Domain}",
            {"Domain": {"Ref": "RootDomainName"}, "HostName": {"Ref": "HostName"}},
        ]
    }

    assert Fn.Sub(
        "arn:aws:ec2:${AWS::Region}:${AWS::AccountId}:vpc/${vpc}"
    ).render() == {"Fn::Sub": "arn:aws:ec2:${AWS::Region}:${AWS::AccountId}:vpc/${vpc}"}

    with pytest.raises(ValueError):
        Fn.Sub(Ref("This substring"))


def test_transform():
    """Test Fn.Transform function."""
    assert Fn.Transform(
        {"Name": "AWS::Include", "Parameters": {"Location": Ref("InputValue")}}
    ).render() == {
        "Fn::Transform": {
            "Name": "AWS::Include",
            "Parameters": {"Location": {"Ref": "InputValue"}},
        }
    }

    with pytest.raises(ValueError):
        Fn.Transform(
            {"name": "AWS::Include", "Parameters": {"Location": Ref("InputValue")}}
        )
