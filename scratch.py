#!/usr/bin/env python

import argparse
import clang.cindex as ci
import sys
import os

if (sys.version_info.major != 3 or sys.version_info.minor < 7):
    print('This script requires python version 3.7 or greater')
    sys.exit(1)

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set


class Location:
    '''
    Substitute for ci.SourceLocation, which can't be used because of lifetime issues.
    The lifetime of ci.SourceLocation is tied to the translation unit
    '''
    def __init__(self, loc: ci.SourceLocation):
        self.file = loc.file.name if loc.file else ""
        self.line = loc.line
        self.column = loc.column

    def __str__(self):
        if not self.file:
            return ""
        base = os.path.basename(self.file)
        return f'{base}:{self.line}:{self.column}'


class FunctionDecl:
    def __init__(self, usr: str, loc: ci.SourceLocation):
        self.usr = usr  # Unified Symbol Resolution (USR) for the function
        self.loc = Location(loc)


class FunctionCall:
    def __init__(self, usr: str, loc: ci.SourceLocation, in_try_block: bool):
        self.usr = usr
        self.loc = Location(loc)
        self.in_try_block = in_try_block


class FunctionNode:
    '''
    Represent a node in a function callgraph
    '''

    # can't use dataclass because defaults aren't working
    # decl: FunctionDecl
    # callers: List[FunctionCall] = field(default_factory=list)
    # calls: List[FunctionCall] = field(default_factory=list)
    def __init__(self):
        self.decl = None
        self.callers = []
        self.calls = []


class Thrower:
    '''
    Represents places that throw exceptions
    '''
    def __init__(self, fun_usr: str, loc: ci.SourceLocation,
                 in_try_block: bool):
        self.fun_usr = fun_usr  # Containing function USR
        self.loc = Location(loc)
        self.in_try_block = in_try_block


def translation_units(build_dir: str):
    '''
    Generator to iterate though all the translation units in a project
    '''
    # TODO: Don't hard code the clang library path
    home = '/home/swd'
    lib_file = f'{home}/apps/clang-latest/lib/libclang.so'
    ci.Config.set_library_file(lib_file)
    comp_db = ci.CompilationDatabase.fromDirectory(build_dir)
    for c in comp_db.getAllCompileCommands():
        index = ci.Index.create()
        tu = index.parse(c.filename, args=filter_compile_args(c.arguments))
        yield tu


def write_tree(cursor: ci.Cursor, indent: int = 0):
    print(
        f'{indent*" "}{cursor.kind}:{cursor.type.spelling}:{Location(cursor.location)}'
    )
    for child in cursor.get_children():
        write_tree(child, indent + 1)


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
            tree = ThrowTree(t, self)
            print(f'throw: {tree.root.loc}')
            for l in tree.leaves:
                print(f'catch: {l}')


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
    def __init__(self, root: Thrower, pi: ProgramIndexes):
        self.root = ThrowTreeNode(root.loc)
        self.leaves = []
        self.program_index = pi

        if root.in_try_block:
            # TODO append catch block, not current loc
            self.leaves.append[root.loc]
            return
        callers = pi.function_nodes[root.fun_usr].callers
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
            self._set_children(
                child_node,
                self.program_index.function_nodes[caller.usr].callers,
                visited | {caller.usr})


def filter_compile_args(args: List[str]):
    '''
    Filter out compiler args that will confuse the parser
    '''
    # Here is a sample of typical args:
    # ['/home/swd/apps/gcc-latest/bin/g++', '--driver-mode=g++', '-DFMT_LOCALE', '-DGFLAGS_IS_A_DLL=0',
    #  '-DJSON_USE_IMPLICIT_CONVERSIONS=1', '-isystem', '/home/swd/projs/common/boost-latest',
    # '-pthread', '-std=gnu++17',
    # '-o', 'CMakeFiles/main.dir/src/main.cpp.o', '-c', '/home/swd/projs/libclang_experiments/sample_proj/src/main.cpp']
    # remove the `-c`- and subsequent arg

    r = []
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a == '-c':
            skip_next = True
            continue
        r.append(a)
    return r


def find_try_blocks(fun: FunctionDecl) -> List[ci.SourceLocation]:
    '''
    If this function ever threw, find all the try blocks where the exception may
    be caught (or report the exception will never be caught)
    '''
    # TODO
    # TODO Write a function that returns the stack trace from the throw to the catch
    pass


def throw_set(fun: FunctionDecl) -> Set[str]:
    '''
    Find all the exceptions this function may throw (including exceptions from
    called functions)
    '''
    pass
    # TODO


def do_it(build_dir: str, generate_parse_tree: bool, generate_call_graph: bool,
          generate_throw_tree: bool):

    program_indexes = ProgramIndexes(build_dir, generate_parse_tree)

    if generate_call_graph:
        program_indexes.call_graph_report()

    if generate_throw_tree:
        program_indexes.throw_tree_report()


def parse_args():
    parser = argparse.ArgumentParser(description=(
        "Generate reports on a C++ program's exception attributes"))
    parser.add_argument(
        '--input',
        '-i',
        help=('directory containing compile commands'),
    )
    parser.add_argument(
        '--parse_tree',
        '-p',
        default=False,
        action='store_true',
        help=('generate parse tree'),
    )
    parser.add_argument(
        '--throw_tree',
        '-t',
        default=False,
        action='store_true',
        help=('generate throw trees'),
    )
    parser.add_argument(
        '--call_graph',
        '-c',
        default=False,
        action='store_true',
        help=('generate call-graph'),
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if not args.input:
        print('Must specify input')
        sys.exit(1)
    if not (args.parse_tree or args.call_graph or args.throw_tree):
        print('Must specify at least one report')
        sys.exit(1)
    do_it(args.input, args.parse_tree, args.call_graph, args.throw_tree)
