#!/usr/bin/env python
"""
Convert typedefs to usings.

Use libclang to walk the AST of a file and convert:
`typedef type alias;`
into:
`using alias = type;`
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import clang.cindex
import os

INPUT_FILENAME = None
REWRITES = []


def rewrite_typedefs(node):
    in_file = (node.location and node.location.file and
               node.location.file.name == INPUT_FILENAME)
    if in_file and node.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
        # Look into why clang is giving int (in error)for some types
        typedef_type_words = node.underlying_typedef_type.spelling.split()
        # ripple puts const at the end of decls
        if typedef_type_words[0] == 'const' and typedef_type_words[
                1] != 'typename':
            typedef_type_words[0], typedef_type_words[1] = (
                typedef_type_words[1], typedef_type_words[0])
        if typedef_type_words[0] not in ['int', 'enum', 'struct', 'class']:
            # remove spaces from ref and pointer chars
            typedef_type_spelling = ''
            for t in typedef_type_words:
                if t not in ['*', '&']:
                    typedef_type_spelling += ' '
                typedef_type_spelling += t
            new_line = 'using {} = {};'.format(node.spelling.strip(),
                                               typedef_type_spelling.strip())
            REWRITES.append(
                [node.extent.start.line - 1, node.extent.start.column - 1,
                 node.extent.end.line - 1, node.extent.end.column - 1,
                 new_line])
    for child in node.get_children():
        rewrite_typedefs(child)


def rewrite(lines, start_col, end_col, nl):
    l = lines[0]
    if len(lines) == 1:
        return [l[:start_col] + nl + l[end_col + 1:]]
    else:
        result = [''] * len(lines)
        result[0] = l[:start_col] + nl
        result[-1] = lines[-1][end_col + 1:]
        return result


def parse_args():
    parser = argparse.ArgumentParser(description=('Convert typedef to using'))
    parser.add_argument(
        '--input',
        '-i',
        help=('input'), )
    parser.add_argument(
        '--output',
        '-o',
        help=('output'), )
    return parser.parse_args()


def run_main():
    global INPUT_FILENAME
    args = parse_args()
    INPUT_FILENAME = args.input
    index = clang.cindex.Index.create()
    src_home = 'Users/determan/projs/ripple/four'
    clang_args = [
        '-frtti', '-std=c++11', '-DOPENSSL_NO_SSL2',
        '-DDEPRECATED_IN_MAC_OS_X_VERSION_10_7_AND_LATER', '-DHAVE_USLEEP=1',
        '-DDEBUG', '-D_DEBUG', '-DBOOST_ASIO_HAS_STD_ARRAY',
        '-D_FILE_OFFSET_BITS=64', '-DBEAST_COMPILE_OBJECTIVE_CPP=1',
        '-I/usr/local/Cellar/openssl/1.0.1j_1/include',
        '-I/Users/determan/projs/common/boost_1_57_0',
        '-I/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/include/c++/v1'
    ]
    clang_args += ['-I{}/{}'.format(src_home, i)
                   for i in ['src', 'src/beast', 'build/proto', 'src/soci/src']
                   ]
    tu = index.parse(INPUT_FILENAME, args=clang_args)
    rewrite_typedefs(tu.cursor)
    with open(INPUT_FILENAME) as src:
        cpp_source = src.readlines()
    for sl, sc, el, ec, nl in REWRITES:
        cpp_source[sl:el + 1] = rewrite(cpp_source[sl:el + 1], sc, ec, nl)

    # cleanup the cases libclang messed up
    result = []
    for l in cpp_source:
        s = l.split()
        if len(s) > 0:
            last_char = s[-1][-1]
            first_char = s[0][0]
        if (len(s) > 0 and s[0] == 'typedef' and last_char == ';' and
                first_char != '(' and first_char != '/'):
            indent = len(l) - len(l.lstrip())
            result.append(' ' * indent + 'using {} = {};\n'.format(s[
                -1][:-1].strip(), ' '.join(s[1:-1]).strip()))
        else:
            result.append(l)

    cpp_source = result
    if args.output:
        with open(args.output, 'w') as dst:
            dst.write(''.join(cpp_source))
    else:
        print(''.join(cpp_source))


if __name__ == '__main__':
    run_main()
