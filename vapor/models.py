#!/usr/bin/env python3
"""Model definitions in vapor."""
import json

import boto3
import yaml

from .utils import format_name


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
            setattr(new_class, "__module__", attrs["_module"].__name__)

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
        """Return the logical of the resource, mapping to the name of the class."""
        return self.__class__.__name__

    @property
    def resource_type(self):
        """Return the type of the resource by analysing the import path."""
        base_class = type(self).__base__
        while True:
            parent = base_class.__base__
            if parent.__module__ == "vapor.models" and parent.__name__ == "Resource":
                break
            base_class = parent
        return f"AWS::{base_class.__module__}::{base_class.__name__}"

    @property
    def template(self):
        """Return the template fragment of the resource."""
        return {
            self.logical_name: {
                "Type": self.resource_type,
                "Properties": self.properties,
            }
        }

    @property
    def properties(self):
        """Return the properties of the resource."""
        return {name: getattr(self, name) for name in dir(self) if name[0].isupper()}


class Stack(metaclass=StackBase):
    """Represents a Cloudformation stack."""

    def __init__(self):
        self.client = boto3.client("cloudformation")

    @property
    def name(self):
        """Name of the stack."""
        return self.deploy_options.get("name", format_name(self.__class__.__name__))

    @property
    def deploy_options(self):
        """Shortcut to DeployOptions dict provided in Subclasses."""
        return getattr(self, "DeployOptions", {})

    @property
    def template(self):
        """Internal python representation of a Cloudformation template."""
        if not hasattr(self, "Resources"):
            raise ValueError("Please define Resources in your stack.")
        # Resources is defined in child classes.
        # pylint: disable=E1101
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
        """Return Cloudformaiton template in json format"""
        return json.dumps(self.template, indent=2)

    @property
    def yaml(self):
        """Return Cloudformaiton template in yaml format"""
        return yaml.dump(self.template)

    def deploy(self):
        """Wrapper around different steps in the stack deployment process."""
        self.pre_deploy()
        self.deploy_stack()
        self.post_deploy()

    def pre_deploy(self):
        """Allowing the subclass to add additional steps before the deployment."""

    def post_deploy(self):
        """Allowing the subclass to add additional steps after the deployment."""

    def deploy_stack(self):
        """Deploy stack changes via changeset."""
