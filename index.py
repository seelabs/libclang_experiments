import clang.cindex as ci

from collections import defaultdict

from exception import Catcher, Thrower, ThrowTree, TryCatch
from function import FunctionCall, FunctionDecl, FunctionNode
from util import IndexContext, translation_units, write_tree


class ProgramIndexes:
    def __init__(self, build_dir: str, output_parse_tree: bool):
        # Key is the usr
        # This is the callgraph
        self.function_nodes = defaultdict(FunctionNode)  # Dict[FunctionNode]

        # List of places that throw exceptions
        self.throwers = []  # List[Thrower]
        self.context = IndexContext()

        for tu in translation_units(build_dir):
            assert self.context.is_empty()
            if output_parse_tree:
                write_tree(tu.cursor)
            self._populate_function_nodes(tu.cursor)

    def _populate_function_nodes(self, cursor: ci.Cursor):
        self.context.push_cursor(cursor)

        if self.context.has_thrower():
            self.context.top_thrower().set_exception_type(self.context)

        if cursor.kind.name == 'FUNCTION_DECL':
            usr = cursor.get_usr()
            assert self.function_nodes[usr].decl is None
            self.function_nodes[usr].decl = FunctionDecl(usr, cursor.location)
            self.context.push_function(usr)
        if cursor.kind.name == 'CALL_EXPR':
            usr = cursor.referenced.get_usr()
            # TODO function calls can happen outside of functions
            # For example, in a global init, or in a lamba in a global init.
            self.function_nodes[self.context.top_function()].calls.append(
                FunctionCall(usr, self.context))
            self.function_nodes[usr].callers.append(
                FunctionCall(self.context.top_function(), self.context))
        if cursor.kind.name == 'VAR_DECL' and self.context.parent_cursor(
        ).kind.name == 'CXX_CATCH_STMT':
            self.context.top_try_block().set_top_catcher_exception_type(cursor)
        if cursor.kind.name == 'CXX_TRY_STMT':
            self.context.push_try_block(TryCatch(self.context))
        if cursor.kind.name == 'CXX_CATCH_STMT':
            self.context.top_try_block().add_catcher(Catcher(self.context))
        if cursor.kind.name == 'CXX_THROW_EXPR':
            thrower = Thrower(self.context)
            self.context.push_thrower(thrower)
            self.throwers.append(thrower)

        for child in cursor.get_children():
            self._populate_function_nodes(child)

        if cursor.kind.name == 'FUNCTION_DECL':
            self.context.pop_funtion()
        if cursor.kind.name == 'CXX_TRY_STMT':
            self.context.pop_try_block()
        if cursor.kind.name == 'CXX_THROW_EXPR':
            self.context.pop_thrower()
        self.context.pop_cursor()

    def call_graph_report(self):
        for usr, fn in self.function_nodes.items():
            print(f'Node: {usr}:')
            for c in fn.callers:
                print(f'caller:  {c.usr} : {c.try_block_stack}')
            for c in fn.calls:
                print(f'calls:  {c.usr} : {c.try_block_stack}')

    def throw_tree_report(self):
        for t in self.throwers:
            tree = ThrowTree(t, self.function_nodes)
            print(f'throw: {tree.root.loc} : {t.exception_type}')
            for l in tree.leaves:
                print(f'catch: {l}')
