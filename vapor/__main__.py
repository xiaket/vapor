#!/usr/bin/env python3
"""
Cli interface for vapor
"""
import ast
import json
import sys
from datetime import datetime
from functools import cached_property
from pathlib import Path

import jinja2
from cfn_flip import to_json


TEMPLATE = '''
#!/usr/bin/env python3
"""
Generated stack definition for {{ original_file_name }}.
"""
from vapor import Stack, Ref, Fn, {{ template.services }}

{% for resource in template.resources %}
{{ resource.code }}


{% endfor %}

# Please change the name of the class
{{ template.stack_code }}

'''


class CfnTemplate:
    """Represents a Cloudformation template."""

    def __init__(self, data):
        """Represents a Cloudformation template."""
        self.data = data

    @property
    def resources(self):
        """A list of Resource instances."""
        return [Resource(name, data) for name, data in self.data["Resources"].items()]

    @property
    def services(self):
        """Services from the resources."""
        return ", ".join(sorted({resource.service for resource in self.resources}))

    @cached_property
    def stack_ast(self):
        """
        Return the ast object of the Stack instance.
        This is later used to construct the python source code.
        """
        assert "Resources" in self.data

        body = []
        resources = ast.Assign(
            targets=[ast.Name(id="Resources", ctx=ast.Store())],
            value=ast.List(
                elts=[
                    ast.Name(id=name, ctx=ast.Load()) for name in self.data["Resources"]
                ],
                ctx=ast.Load(),
            ),
            lineno=0,
        )
        body.append(resources)

        optionals = [
            "AWSTemplateFormatVersion",
            "Conditions",
            "Mappings",
            "Metadata",
            "Outputs",
            "Parameters",
            "Rules",
            "Transform",
        ]
        for name in optionals:
            if name not in self.data:
                continue

            kwargs = {
                "targets": [ast.Name(id=name, ctx=ast.Store())],
                "value": parse_node(self.data[name]),
                "lineno": 0,
            }
            node = ast.Assign(**kwargs)
            body.append(node)

        return ast.ClassDef(
            name="VaporStack",
            bases=[ast.Name(id="Stack", ctx=ast.Load())],
            keywords=[],
            body=body,
            decorator_list=[],
        )

    @property
    def stack_code(self):
        """Python code as string constructed from ast."""
        return ast.unparse(self.stack_ast)


def parse_fn(func, node):
    """Parse an Fn::Something construct."""
    if isinstance(node, list):
        args = [parse_node(item) for item in node]
    else:
        args = [parse_node(node)]
    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="Fn", ctx=ast.Load()), attr=func, ctx=ast.Load()
        ),
        args=args,
        keywords=[],
    )


def parse_node(node):
    """Turn a python object back to ast object."""
    if isinstance(node, list):
        return ast.List(elts=[parse_node(item) for item in node], ctx=ast.Load())
    if isinstance(node, dict):
        if len(node) == 1:
            key = list(node)[0]
            if key == "Ref":
                return ast.Call(
                    func=ast.Name(id="Ref", ctx=ast.Load()),
                    args=[ast.Constant(value=node[key])],
                    keywords=[],
                )
            if key.startswith("Fn::"):
                func = key.split("::")[1]
                return parse_fn(func, node[key])
        keys = []
        values = []
        for key, value in node.items():
            keys.append(ast.Constant(value=key))
            values.append(parse_node(value))
        return ast.Dict(keys=keys, values=values)
    if isinstance(node, (str, int, float)):
        return ast.Constant(value=node)
    raise ValueError(f"Invalid data type specified in the code: {node}")


class Resource:
    """Represents a resource in Cloudformation template."""

    def __init__(self, logical_name, data):
        self.logical_name = logical_name
        self.data = data

    @cached_property
    def astobj(self):
        """
        Return the ast object of the resource instance.
        This is later used to construct the python source code.
        """
        resource_type = self.data["Type"].split("::")[-1]
        body = []
        provider = self.data["Type"].split("::")[0]
        # It looks like a bug in python 3.9 that if the lineno is not added
        # to the assign node, we will bump into an AttributeError.
        if provider != "AWS":
            body.append(
                ast.Assign(
                    targets=[ast.Name(id="Meta", ctx=ast.Store())],
                    value=ast.Dict(
                        keys=[ast.Constant(value="provider")],
                        values=[ast.Constant(value=provider)],
                    ),
                    lineno=0,
                )
            )
        for key, value in self.data["Properties"].items():
            kwargs = {
                "targets": [ast.Name(id=key, ctx=ast.Store())],
                "value": parse_node(value),
                "lineno": 0,
            }
            node = ast.Assign(**kwargs)
            body.append(node)
        return ast.ClassDef(
            name=self.logical_name,
            bases=[
                ast.Attribute(
                    value=ast.Name(id=self.service, ctx=ast.Load()),
                    attr=resource_type,
                    ctx=ast.Load(),
                )
            ],
            decorator_list=[],
            keywords=[],
            body=body,
        )

    @property
    def code(self):
        """Python code as string constructed from ast."""
        return ast.unparse(self.astobj)

    @property
    def service(self):
        """Service of this resource, think of S3, EC2, SSM."""
        return self.data["Type"].split("::")[1]


def render(filename, data):
    """Render the dict into a vapor python script."""
    template = jinja2.Template(TEMPLATE)
    cfn = CfnTemplate(data)
    return template.render(
        original_file_name=filename,
        template=cfn,
    )


def import_():
    """Convert existing cloudformation templates into vapor files."""
    for filename in sys.argv[1:]:
        pathobj = Path(filename)
        with pathobj.open(encoding="utf-8") as fobj:
            if pathobj.suffix in [".yml", ".yaml"]:
                content = fobj.read().strip()
                data = to_json(content)
            elif pathobj.suffix == ".json":
                data = fobj.read()
            else:
                raise ValueError(
                    "Please provide a Cloudformation template file that ends in .json/.yml"
                )
            data = json.loads(data)

        newname = f"{pathobj.stem}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.py"
        fileobj = pathobj.with_name(newname)
        if fileobj.exists():
            raise RuntimeError(f"Destination file exists: {fileobj.as_posix()}")
        output = render(pathobj.name, data)
        fileobj.write_text(output, encoding="utf-8")
