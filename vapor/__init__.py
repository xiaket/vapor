#!/usr/bin/env python3
"""
finder to create dynamic modules.
"""
import sys

from importlib.machinery import ModuleSpec

from .models import ResourceBase, StackBase, Resource
from .fn import Ref, Fn
from .stack import Stack


class AWSFinder:
    """
    This class Follows the python module loading protocol and will serve as a virtual
    module.

    Ref: PEP-302
    """

    @classmethod
    def find_spec(cls, name, path, target=None):
        """
        If we are importing vapor things, create a module for it.
        """
        # This is just following protocol
        # pylint: disable=W0613
        if name.startswith("vapor."):
            _, service = name.split(".", 1)
            return ModuleSpec(service, cls())
        return None

    def create_module(self, _):
        """Do nothing specific here."""
        # This is just following protocol
        # pylint: disable=R0201
        return None

    def exec_module(self, module):
        """Create a dynamic class and return it."""
        # This is just following protocol
        # pylint: disable=R0201
        def _getattr(name):
            cls = type(name, (Resource,), {"_module": module})
            return cls

        module.__getattr__ = _getattr


sys.meta_path += [AWSFinder]
