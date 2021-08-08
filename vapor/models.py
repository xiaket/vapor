#!/usr/bin/env python3
"""Model definitions in vapor."""
from .fn import replace_fn
from .utils import get_logger


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
        return {
            name: replace_fn(getattr(self, name))
            for name in dir(self)
            if name[0].isupper()
        }
