#!/usr/bin/env python

import argparse
import sys

from typing import Dict, List, Set

from index import ProgramIndexes

if (sys.version_info.major != 3 or sys.version_info.minor < 7):
    print('This script requires python version 3.7 or greater')
    sys.exit(1)


def main(build_dir: str, generate_parse_tree: bool, generate_call_graph: bool,
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
    main(args.input, args.parse_tree, args.call_graph, args.throw_tree)
