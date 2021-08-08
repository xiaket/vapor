#!/usr/bin/env python3
"""
Testing models that maps to Cloudformation functions.
"""
import pytest

from vapor.fn import replace_fn, Ref


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
