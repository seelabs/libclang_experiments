import clang.cindex as ci

from util import IndexContext, Location


class FunctionDecl:
    def __init__(self, usr: str, loc: ci.SourceLocation):
        self.usr = usr  # Unified Symbol Resolution (USR) for the function
        self.loc = Location(loc)


class FunctionCall:
    def __init__(self, usr: str, context: IndexContext):
        self.usr = usr
        self.loc = Location(context.top_cursor().location)
        self.try_block_stack = context.try_block_stack.copy()


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
