#!/usr/bin/env python3
"""Model definitions in vapor."""
import json
from datetime import datetime

import boto3
import yaml
from botocore.exceptions import ClientError

from .utils import format_name, get_logger


logger = get_logger(__name__)


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
            "Type": self.resource_type,
            "Properties": self.properties,
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
            "Resources": {kls().logical_name: kls().template for kls in self.Resources},
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

    @property
    def describe_stack_response(self):
        """Return the response from descibe-stacks call."""
        try:
            return self.client.describe_stacks(StackName=self.name)["Stacks"][0]
        except ClientError as error:
            code = error.response["Error"]["Code"]
            message = error.response["Error"]["Message"]
            if code == "ValidationError" and message.endswith("does not exist"):
                return {"StackStatus": "DOES_NOT_EXIST"}
            raise

    @property
    def status(self):
        """Return the status of the stack as a string."""
        return self.describe_stack_response["StackStatus"]

    @property
    def exists(self):
        """Check whether this stack exists."""
        return self.status != "DOES_NOT_EXIST"

    def deploy(self, dryrun=True, wait=True):
        """Wrapper around different steps in the stack deployment process."""
        self.pre_deploy(dryrun, wait)
        self.__deploy(dryrun, wait)
        self.post_deploy(dryrun, wait)

    def __deploy(self, dryrun, wait):
        """Deploy stack changes via changeset."""

    def delete(self, dryrun=True, wait=True):
        """Wrapper around different steps in the stack deletion process."""
        self.__delete(dryrun, wait)

    def post_deploy(self, dryrun, wait):
        """Allowing the subclass to add additional steps after the deletion."""
        logger.info(f"Nothing to be done in post-delete hook. {dryrun=}, {wait=}.")

    def __delete(self, dryrun, wait):
        """Delete stack."""

    def pre_deploy(self, dryrun, wait):
        """Allowing the subclass to add additional steps before the deployment."""
        if self.status == "ROLLBACK_COMPLETE":
            logger.info(f"Deleting stack in ROLLBACK_COMPLETE state.")
            if not dryrun:
                self.delete(dryrun, wait)

    def __create_changeset(self):
        """Create a changeset."""
        name = f"{datetime.now().strftime('%F-%H-%M-%S')}"
        parameters = [
            {"ParameterKey": param, "ParameterValue": self.params[param]}
            for param in self.deploy_options.get("parameters", {})
        ]
        tags = [
            {"Key": tag, "Value": value}
            for tag, value in self.deploy_options.get("tags", {}).items()
        ]
        kwargs = {
            "StackName": self.name,
            "Parameters": parameters,
            "Tags": tags,
            "ChangeSetName": name,
            "ChangeSetType": "UPDATE" if self.exists else "CREATE",
            "Capabilities": self.deploy_options.get("Capabilities", []),
            "TemplateBody": self.yaml,
        }

        logger.info(f"Creating changeset {name}.")
        self.client.create_change_set(**kwargs)
        return kwargs["ChangeSetType"] == "CREATE", name
