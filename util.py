import clang.cindex as ci

import os

from typing import List


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


def _filter_compile_args(args: List[str]):
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
        tu = index.parse(c.filename, args=_filter_compile_args(c.arguments))
        yield tu


def write_tree(cursor: ci.Cursor, indent: int = 0):
    print(
        f'{indent*" "}{cursor.kind}:{cursor.type.spelling}:{Location(cursor.location)}'
    )
    for child in cursor.get_children():
        write_tree(child, indent + 1)
