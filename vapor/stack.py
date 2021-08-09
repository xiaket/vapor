#!/usr/bin/env python3
"""Model definitions in vapor."""
import json
import random
import re
import time
from datetime import datetime

import boto3
import yaml
from botocore.exceptions import ClientError

from .hooks import (
    cleanup_rollback_complete,
    check_template_with_cfn_lint,
)
from .models import StackBase
from .utils import get_logger


logger = get_logger(__name__)


def format_name(name):
    """
    Generate a stack name from class name by converting camel case to dash case.
    Adapted from https://stackoverflow.com/questions/1175208/.

    This function is our best effort to provide a good stack name in Cloudformation.
    However, if you want to have fine-grained control, please specify the name field in
    DeployOptions in your Stack class.

    example: format_name("TestStack") == "test-stack"
    """
    name = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1-\2", name).lower()


def format_changes(changes):
    """
    Format changes so it will look better.

    ref on changeset:

    https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets-view.html
    """
    parts = []
    for change in changes:
        change_ = change["ResourceChange"]
        line = (
            f"[{change_['Action'].upper()}] "
            f"{change_['LogicalResourceId']}({change_['ResourceType']})"
        )
        if "Details" in change_ and change_["Details"]:
            line += f":\n\t{change_['Details']}"
        parts.append(line)
    return "\n".join(parts)


class Stack(metaclass=StackBase):
    """Represents a Cloudformation stack."""

    Hooks = {
        "pre_deploy": [
            cleanup_rollback_complete,
            check_template_with_cfn_lint,
        ],
    }

    def __init__(self):
        self.client = boto3.client("cloudformation")

    @property
    def name(self):
        """Name of the stack."""
        return self.deploy_options.get("name", format_name(self.__class__.__name__))

    @property
    def region(self):
        """Region of the stack."""
        return self.client.meta.region_name

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
        # Disable anchor in yaml

        # pyyaml will try to be smart and add an anchor to the generated yaml file.
        # This "feature" is not desirable.
        yaml.Dumper.ignore_aliases = lambda self, data: True
        return yaml.dump(self.template, Dumper=yaml.Dumper)

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
        create, name = self.__create_changeset()
        action = "Creating" if create else "Updating"
        logger.info(f"{action} {self.name} stack.")

        changes = self.__wait_changeset(name)
        if changes == []:
            logger.info(f"No change in {self.name} stack.")
            return

        logger.info(f"Changes in changeset `{name}`: \n{format_changes(changes)}")

        if not dryrun:
            logger.info(f"Executing changeset `{name}`.")
            self.client.execute_change_set(ChangeSetName=name, StackName=self.name)
            if wait and not dryrun:
                self.__wait_stack()
        else:
            self.client.delete_change_set(ChangeSetName=name, StackName=self.name)
            if create:
                # An empty stack will stay there until we delete it.
                self.client.delete_stack(StackName=self.name)
            logger.info("Skipping deployment as this is a dry run.")

    def pre_deploy(self, dryrun, wait):
        """Allowing the subclass to add additional steps before the deployment."""
        for hook in self.Hooks.get("pre_deploy", []):
            hook(self, dryrun, wait)

    def post_deploy(self, dryrun, wait):
        """Allowing the subclass to add additional steps after the deployment."""
        for hook in self.Hooks.get("post_deploy", []):
            hook(self, dryrun, wait)

    def delete(self, dryrun=True, wait=True):
        """Wrapper around different steps in the stack deletion process."""
        self.pre_delete(dryrun, wait)
        self.__delete(dryrun, wait)
        self.post_delete(dryrun, wait)

    def pre_delete(self, dryrun, wait):
        """Allowing the subclass to add additional steps before the deletion."""
        for hook in self.Hooks.get("pre_delete", []):
            hook(self, dryrun, wait)

    def post_delete(self, dryrun, wait):
        """Allowing the subclass to add additional steps after the deletion."""
        for hook in self.Hooks.get("post_delete", []):
            hook(self, dryrun, wait)

    def __delete(self, dryrun, wait):
        """Delete stack."""
        if dryrun:
            logger.info("Skipping deletion as this is a dry run.")
        else:
            logger.info(f"Deleting stack: `{self.name}`.")
            self.client.delete_stack(StackName=self.name)
            if wait and not dryrun:
                self.__wait_stack()

    def __create_changeset(self):
        """Create a changeset."""
        suffix = bytearray(random.getrandbits(8) for _ in range(4)).hex()
        name = f"{datetime.now().strftime('%F-%H-%M-%S')}-{suffix}"
        parameters = [
            {"ParameterKey": key, "ParameterValue": value}
            for key, value in self.deploy_options.get("parameters", {}).items()
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
            "Capabilities": self.deploy_options.get("capabilities", []),
            "TemplateBody": self.yaml,
        }

        logger.info(f"Creating changeset {name}.")
        self.client.create_change_set(**kwargs)
        return kwargs["ChangeSetType"] == "CREATE", name

    def __wait_changeset(self, name):
        """Wait till a changeset is available and return it's changes."""
        kwargs = {"ChangeSetName": name, "StackName": self.name}

        while True:
            response = self.client.describe_change_set(**kwargs)
            status = response["Status"]
            exec_status = response["ExecutionStatus"]

            if status == "FAILED":
                empty_changeset_reasons = [
                    "didn't contain changes",
                    "No updates are to be performed.",
                ]
                for reason in empty_changeset_reasons:
                    if reason in response["StatusReason"]:
                        return []
                raise RuntimeError(
                    f"Failed to create changeset for {self.name}: {response['StatusReason']}"
                )

            if status == "CREATE_COMPLETE" and exec_status == "AVAILABLE":
                if not response.get("NextToken"):
                    # Don't have lot's of changes, no need for another api call.
                    return response.get("Changes", [])
                changes = response.get("Changes", [])
                # setting NextToken in kwargs.
                kwargs["NextToken"] = response["NextToken"]
                break
            logger.info(
                f"Status of changeset is `{status}`, execution status is `{exec_status}`"
            )
            # Change set should be ready within seconds.
            time.sleep(3)

        while True:
            response = self.client.describe_change_set(**kwargs)
            changes += response.get("Changes", [])
            if not response.get("NextToken"):
                break
            kwargs["NextToken"] = response["NextToken"]
        return changes

    def __wait_stack(self):
        while True:
            current_status = self.status
            if current_status == "DOES_NOT_EXIST":
                # Delete complete
                return

            if current_status.split("_")[-1] in ["FAILED", "COMPLETE"]:
                break
            logger.info(f"Waiting till stack operation completes: {current_status}.")
            time.sleep(5)

        logger.info(f"Stack operation finished: {current_status}")
        bad_statuses = [
            "UPDATE_ROLLBACK_COMPLETE",
            "ROLLBACK_COMPLETE",
        ]
        if current_status in bad_statuses or current_status.endswith("FAILED"):
            raise RuntimeError("Failed to create/update stack.")
