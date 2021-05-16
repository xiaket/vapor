#!/usr/bin/env python3
import sys

from importlib.machinery import ModuleSpec


class ModelBase(type):
    """Metaclass for all models."""
    def __new__(cls, name, bases, attrs, **kwargs):
        super_new = super().__new__
        print(f"In ModelBase: {name=}, {bases=}, {attrs=}, {kwargs=}")

        parents = [b for b in bases if isinstance(b, ModelBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)


        module = attrs.pop('__module__')

        new_class = super_new(cls, name, bases, attrs, **kwargs)
        return new_class


class Resource(metaclass=ModelBase):
    def __init__(self, *args, **kwargs):
        print(f"In Resource.__init__: {args=}, {kwargs=}")


def create_cfn_class(*args, **kwargs):
    print(f"In create_cfn_class: {args=}, {kwargs=}")
    class_name = args[0]
    return type(class_name, (Resource,), {})


class AWSFinder:
    @classmethod
    def find_spec(cls, name, path, target=None):
        print(f"In find_spec: {cls=}, Importing {name!r}, {path=}, {target=}")
        assert "." in name
        vapor, service = name.split(".", 1)
        assert vapor == "vapor"
        name = service
        return ModuleSpec(name, cls())

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        """Executing the module means reading the CSV file"""
        module.__getattr__ = create_cfn_class


sys.meta_path += [AWSFinder]
