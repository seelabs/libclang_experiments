import clang.cindex as ci

from typing import Dict, List, Set

from function import FunctionCall, FunctionNode
from util import IndexContext, Location


class Thrower:
    '''
    Represents places that throw exceptions
    '''
    def __init__(self, context: IndexContext):
        self.fun_usr = context.top_function()  # Containing function USR
        self.loc = Location(context.top_cursor().location)
        self.try_block_stack = context.try_block_stack.copy()
        self.exception_type = None

    def set_exception_type(self, context: IndexContext):
        c = context.top_cursor()
        if self.exception_type is None and c.type:
            self.exception_type = c.type.spelling


class Catcher:
    '''
    Represents a catch block
    '''
    def __init__(self, context: IndexContext):
        self.loc = Location(context.top_cursor().location)
        self.exception_type = None  # None means "catch all"

    def set_exception_type(self, c: ci.Cursor):
        self.exception_type = c.type.spelling

    def __repr__(self):
        return f'Catcher: {self.loc} {self.exception_type}'

    def _matches_thrower(self, thrower: Thrower) -> bool:
        if exception_type is None:
            return True
        if thrower.exception_type is None:
            pass  # TODO Get the exeception type for a re-throw
        # TODO: See if the throw type matches the catch type
        return True

    # throwers is a stack to it can handle re-throws
    # throwers with a exception_type of None are re-throws
    def matches(self, throwers: List[Thrower]) -> bool:
        for t in reversed(throwers):
            if t.exception_type is not None:
                return self._matches_thrower(t)
        assert (False)
        # at least one thrower can't be a rethrow


class TryCatch:
    '''
    Represents a try/catch block
    '''
    def __init__(self, context: IndexContext):
        self.loc = Location(context.top_cursor().location)
        self.catchers = []  # List[Catcher]

    def add_catcher(self, c: Catcher):
        self.catchers.append(c)

    def set_top_catcher_exception_type(self, c: ci.Cursor):
        self.catchers[-1].set_exception_type(c)

    def __repr__(self):
        return f'Try block: {self.loc} Catchers: {self.catchers}'


class ThrowTreeNode:
    def __init__(self, loc: ci.SourceLocation):
        self.loc = loc
        self.children = []


class ThrowTree:
    '''
    Given a Thrower, create a tree with a thrower at the root, function calls
    at the inner nodes, and a catch block at the leaves (or a top level
    function - either main or a thread)
    '''
    def __init__(self, root: Thrower, function_nodes: Dict[str, FunctionNode]):
        self.root = ThrowTreeNode(root.loc)
        self.leaves = []
        self.function_nodes = function_nodes

        if root.try_block_stack:
            self.leaves.append(root.try_block_stack)
            return
        callers = function_nodes[root.fun_usr].callers
        self._set_children(self.root, callers, set())

    def _set_children(self, node: ThrowTreeNode, callers: List[FunctionCall],
                      visited: Set[str]):
        if not callers:
            self.leaves.append("uncaught")
        for caller in callers:
            if caller.usr in visited:
                continue
            child_node = ThrowTreeNode(caller.loc)
            node.children.append(child_node)
            if caller.try_block_stack:
                self.leaves.append(caller.try_block_stack)
                continue
            self._set_children(child_node,
                               self.function_nodes[caller.usr].callers,
                               visited | {caller.usr})
