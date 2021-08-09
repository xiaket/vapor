#!/usr/bin/env python3
"""
Models that maps to Cloudformation functions.
"""


def replace_fn(node):
    """Iteratively replace all Fn/Ref in the node"""
    if isinstance(node, list):
        return [replace_fn(item) for item in node]
    if isinstance(node, dict):
        return {name: replace_fn(value) for name, value in node.items()}
    if isinstance(node, (str, int, float)):
        return node
    if isinstance(node, Ref):
        return node.render()
    if hasattr(Fn, node.__class__.__name__):
        return node.render()
    raise ValueError(f"Invalid value specified in the code: {node}")


class Ref:
    """Represents a ref function in Cloudformation."""

    # This is our DSL, it's a very thin wrapper around dictionary.
    # pylint: disable=R0903
    def __init__(self, target):
        """Creates a Ref node with a target."""
        self.target = target

    def render(self):
        """Render the node as a dictionary."""
        return {"Ref": self.target}


class Base64:
    """Fn::Base64 function."""

    # pylint: disable=R0903

    def __init__(self, value):
        self.value = value

    def render(self):
        """Render the node with Fn::Base64."""
        return {"Fn::Base64": replace_fn(self.value)}


class Cidr:
    """Fn::Cidr function."""

    # pylint: disable=R0903

    def __init__(self, ipblock, count, cidr_bits):
        self.ipblock = ipblock
        self.count = count
        self.cidr_bits = cidr_bits

    def render(self):
        """Render the node with Fn::Cidr."""
        return {
            "Fn::Cidr": [
                replace_fn(self.ipblock),
                replace_fn(self.count),
                replace_fn(self.cidr_bits),
            ]
        }


class And:
    """Fn::And function."""

    # pylint: disable=R0903

    def __init__(self, *args):
        self.conditions = list(args)

    def render(self):
        """Render the node with Fn::And."""
        return {"Fn::And": replace_fn(self.conditions)}


class Equals:
    """Fn::Equals function."""

    # pylint: disable=R0903

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def render(self):
        """Render the node with Fn::Equals."""
        return {"Fn::Equals": [replace_fn(self.lhs), replace_fn(self.rhs)]}


class If:
    """Fn::If function."""

    # pylint: disable=R0903

    def __init__(self, condition, true_value, false_value):
        self.condition = condition
        self.true_value = true_value
        self.false_value = false_value

    def render(self):
        """Render the node with Fn::If."""
        return {
            "Fn::If": [
                replace_fn(self.condition),
                replace_fn(self.true_value),
                replace_fn(self.false_value),
            ]
        }


class Not:
    """Fn::Not function."""

    # pylint: disable=R0903

    def __init__(self, condition):
        self.condition = condition

    def render(self):
        """Render the node with Fn::Not."""
        return {"Fn::Not": [replace_fn(self.condition)]}


class Or:
    """Fn::Or function."""

    # pylint: disable=R0903

    def __init__(self, *args):
        self.conditions = list(args)

    def render(self):
        """Render the node with Fn::Or."""
        return {"Fn::Or": replace_fn(self.conditions)}


class FindInMap:
    """Fn::FindInMap function."""

    # pylint: disable=R0903

    def __init__(self, map_name, l1key, l2key):
        self.map_name = map_name
        self.l1key = l1key
        self.l2key = l2key

    def render(self):
        """Render the node with Fn::FindInMap."""
        return {
            "Fn::FindInMap": [
                replace_fn(self.map_name),
                replace_fn(self.l1key),
                replace_fn(self.l2key),
            ]
        }


class GetAtt:
    """Fn::GetAtt function."""

    # pylint: disable=R0903

    def __init__(self, logical_name, attr):
        self.logical_name = logical_name
        self.attr = attr

    def render(self):
        """Render the node with Fn::GetAtt."""
        return {"Fn::GetAtt": [replace_fn(self.logical_name), replace_fn(self.attr)]}


class GetAZs:
    """Fn::GetAZs function."""

    # pylint: disable=R0903

    def __init__(self, region):
        self.region = region

    def render(self):
        """Render the node with Fn::GetAZs."""
        return {"Fn::GetAZs": replace_fn(self.region)}


class ImportValue:
    """Fn::ImportValue function."""

    # pylint: disable=R0903

    def __init__(self, export):
        self.export = export

    def render(self):
        """Render the node with Fn::ImportValue."""
        return {"Fn::ImportValue": replace_fn(self.export)}


class Join:
    """Fn::Join function."""

    # pylint: disable=R0903

    def __init__(self, delimiter, elements):
        self.delimiter = delimiter
        self.elements = elements

    def render(self):
        """Render the node with Fn::Join."""
        return {"Fn::Join": [replace_fn(self.delimiter), replace_fn(self.elements)]}


class Select:
    """Fn::Select function."""

    # pylint: disable=R0903

    def __init__(self, index, elements):
        self.index = index
        self.elements = elements

    def render(self):
        """Render the node with Fn::Select."""
        return {"Fn::Select": [replace_fn(self.index), replace_fn(self.elements)]}


class Split:
    """Fn::Split function."""

    # pylint: disable=R0903

    def __init__(self, delimiter, target):
        self.delimiter = delimiter
        self.target = target

    def render(self):
        """Render the node with Fn::Split."""
        return {"Fn::Split": [replace_fn(self.delimiter), replace_fn(self.target)]}


class Sub:
    """Fn::Sub function."""

    # pylint: disable=R0903

    def __init__(self, target, mapping=None):
        if not isinstance(target, str):
            raise ValueError(
                f"The first argument of Fn::Sub must be string: `{target}`"
            )
        if mapping is None:
            self.mapping = {}

        self.target = target
        self.mapping = mapping

    def render(self):
        """Render the node with Fn::Sub."""
        if self.mapping:
            return {"Fn::Sub": [replace_fn(self.target), replace_fn(self.mapping)]}
        return {"Fn::Sub": replace_fn(self.target)}


class Transform:
    """Fn::Transform function."""

    # pylint: disable=R0903

    def __init__(self, construct):
        is_dict = isinstance(construct, dict)
        match_keys = set(construct.keys()) == {"Name", "Parameters"}

        if not is_dict or not match_keys:
            raise ValueError("Invalid Transform construct")

        self.construct = construct

    def render(self):
        """Render the node with Fn::Transform."""
        return {
            "Fn::Transform": {
                "Name": replace_fn(self.construct["Name"]),
                "Parameters": replace_fn(self.construct["Parameters"]),
            }
        }


class Fn:
    """
    This is a container for all functions.

    Rationale is instead of having to import all the functions,
    we just import Fn and use any function as Fn.FuncName
    """

    # pylint: disable=R0903

    Base64 = Base64
    Cidr = Cidr
    And = And
    Equals = Equals
    If = If
    Not = Not
    Or = Or
    FindInMap = FindInMap
    GetAtt = GetAtt
    GetAZs = GetAZs
    ImportValue = ImportValue
    Join = Join
    Select = Select
    Split = Split
    Sub = Sub
    Transform = Transform
