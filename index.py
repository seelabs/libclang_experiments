import clang.cindex as ci

from collections import defaultdict

from exception import Thrower, ThrowTree
from function import FunctionCall, FunctionDecl, FunctionNode
from util import translation_units, write_tree


class ProgramIndexes:
    def __init__(self, build_dir: str, output_parse_tree: bool):
        # Key is the usr
        # This is the callgraph
        self.function_nodes = defaultdict(FunctionNode)  # Dict[FunctionNode]

        # List of places that throw exceptions
        self.throwers = []  # List[Thrower]

        for tu in translation_units(build_dir):
            if output_parse_tree:
                write_tree(tu.cursor)
            self._populate_function_nodes(tu.cursor)

    def _populate_function_nodes(self,
                                 cursor: ci.Cursor,
                                 in_function: str = '',
                                 in_try_block: bool = False):
        if cursor.kind.name == 'CXX_TRY_STMT':
            pass
        if cursor.kind.name == 'FUNCTION_DECL':
            usr = cursor.get_usr()
            assert self.function_nodes[usr].decl is None
            self.function_nodes[usr].decl = FunctionDecl(usr, cursor.location)
            in_function = usr
        if cursor.kind.name == 'CALL_EXPR':
            usr = cursor.referenced.get_usr()
            self.function_nodes[in_function].calls.append(
                FunctionCall(usr, cursor.location, in_try_block))
            self.function_nodes[usr].callers.append(
                FunctionCall(in_function, cursor.location, in_try_block))
        if cursor.kind.name == 'CXX_TRY_STMT':
            in_try_block = True
        if cursor.kind.name == 'CXX_THROW_EXPR':
            self.throwers.append(
                Thrower(in_function, cursor.location, in_try_block))
        old_in_try_block = in_try_block
        old_in_function = in_function
        for child in cursor.get_children():
            self._populate_function_nodes(child, in_function, in_try_block)
        in_function = old_in_function
        in_try_block = old_in_try_block

    def call_graph_report(self):
        for usr, fn in self.function_nodes.items():
            print(f'Node: {usr}:')
            for c in fn.callers:
                print(f'caller:  {c.usr} : {c.in_try_block}')
            for c in fn.calls:
                print(f'calls:  {c.usr} : {c.in_try_block}')

    def throw_tree_report(self):
        for t in self.throwers:
            tree = ThrowTree(t, self.function_nodes)
            print(f'throw: {tree.root.loc}')
            for l in tree.leaves:
                print(f'catch: {l}')
