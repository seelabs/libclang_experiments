import clang.cindex as ci

from util import Location


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
