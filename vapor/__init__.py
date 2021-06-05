#!/usr/bin/env python3
import json
import sys

from importlib.machinery import ModuleSpec

import yaml


class ResourceBase(type):
    """Metaclass for all cfn resources."""

    def __new__(cls, name, bases, attrs):
        super_new = super().__new__

        # Only perform custom logic for the subclasses of Resource, but not Resource
        # itself.
        parents = [b for b in bases if isinstance(b, ResourceBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        new_class = super_new(cls, name, bases, attrs)
        if "_module" in attrs:
            # We need to pass it down to the subclass
            setattr(new_class, "__module__", attrs["_module"])
            pass

        return new_class


class StackBase(type):
    """Metaclass for all cfn stacks."""

    def __new__(cls, name, bases, attrs):
        super_new = super().__new__

        # Only perform custom logic for the subclasses of Stack, but not Stack itself.
        parents = [b for b in bases if isinstance(b, StackBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        new_class = super_new(cls, name, bases, attrs)
        return new_class


class Resource(metaclass=ResourceBase):
    """Represents a resource defintion in Cloudformation."""

    @property
    def logical_name(self):
        return self.__class__.__name__

    @property
    def resource_type(self):
        # FIXME: need to find the immediate child of Resource and start from there.
        base_class = type(self).__base__
        while True:
            new_base = base_class.__base__
            if new_base.__module__ == "vapor" and new_base.__name__ == "Resource":
                break
            base_class = new_base
        return f"AWS::{base_class.__module__.__name__}::{base_class.__name__}"

    @property
    def template(self):
        return {
            self.logical_name: {
                "Type": self.resource_type,
                "Properties": self.properties,
            }
        }

    @property
    def properties(self):
        return {name: getattr(self, name) for name in dir(self) if name[0].isupper()}


class Stack(metaclass=StackBase):
    """Represents a Cloudformation stack."""

    @property
    def template(self):
        """Internal python representation of a Cloudformation template."""
        tmplt = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": [resource().template for resource in self.Resources],
        }
        optionals = [
            "Conditions",
            "Mappings",
            "Metadata",
            "Outputs",
            "Parameters",
            "Rules",
            "Transform",
        ]
        for name in optionals:
            if hasattr(self, name):
                tmplt[name] = getattr(self, name)

        return tmplt

    @property
    def json(self):
        return json.dumps(self.template, indent=2)

    @property
    def yaml(self):
        return yaml.dump(self.template)


class AWSFinder:
    """
    This class Follows the python module loading protocol and will serve as a virtual
    module.

    Ref: PEP-302
    """

    @classmethod
    def find_spec(cls, name, path, target=None):
        if name.startswith("vapor."):
            vapor, service = name.split(".", 1)
            return ModuleSpec(service, cls())

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        def getattr(name):
            cls = type(name, (Resource,), {"_module": module})
            return cls

        module.__getattr__ = getattr


sys.meta_path += [AWSFinder]
