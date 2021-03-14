import clang.cindex as ci

from typing import Dict, List, Set

from function import FunctionCall, FunctionNode
from util import Location


class Thrower:
    '''
    Represents places that throw exceptions
    '''
    def __init__(self, fun_usr: str, loc: ci.SourceLocation,
                 in_try_block: bool):
        self.fun_usr = fun_usr  # Containing function USR
        self.loc = Location(loc)
        self.in_try_block = in_try_block


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

        if root.in_try_block:
            # TODO append catch block, not current loc
            self.leaves.append[root.loc]
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
            if caller.in_try_block:
                self.leaves.append(caller.loc)
                continue
            self._set_children(child_node,
                               self.function_nodes[caller.usr].callers,
                               visited | {caller.usr})
