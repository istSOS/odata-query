"""
NodeVisitor based on cpython/ast.py:
Copyright 2008 by Armin Ronacher, Python License.
https://github.com/python/cpython/blob/master/Lib/ast.py
"""
from dataclasses import fields
from typing import Any, Iterator, Tuple

from . import ast


def iter_dataclass_fields(node) -> Iterator[Tuple[str, Any]]:
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    for field in fields(node):
        yield field.name, getattr(node, field.name)


class NodeVisitor:
    """
    A node visitor base class that walks the abstract syntax tree and calls a
    visitor function for every node found.  This function may return a value
    which is forwarded by the `visit` method.
    This class is meant to be subclassed, with the subclass adding visitor
    methods.
    By default the visitor functions for the nodes are ``'visit_'`` +
    class name of the node. If no visitor function exists for a node
    (return value `None`) the `generic_visit` visitor is used instead.
    """

    def visit(self, node: ast._Node):
        """Visit a node."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast._Node):
        """Called if no explicit visitor function exists for a node."""
        for field, value in iter_dataclass_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast._Node):
                        self.visit(item)
            elif isinstance(value, ast._Node):
                self.visit(value)


class NodeTransformer(NodeVisitor):
    """
    A visitor that can change the tree as it passes over it.
    """

    def generic_visit(self, node: ast._Node) -> ast._Node:
        new_kwargs = {}

        for field, value in iter_dataclass_fields(node):
            if isinstance(value, list):
                new_val = []
                for item in value:
                    if isinstance(item, ast._Node):
                        new_val.append(self.visit(item))
                    else:
                        new_val.append(item)
            elif isinstance(value, ast._Node):
                new_val = self.visit(value)
            else:
                new_val = value

            new_kwargs[field] = new_val

        return type(node)(**new_kwargs)  # type: ignore
