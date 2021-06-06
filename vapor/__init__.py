#!/usr/bin/env python3
"""
finder to create dynamic modules.
"""
import sys

from importlib.machinery import ModuleSpec

from .models import ResourceBase, StackBase, Resource, Stack


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
