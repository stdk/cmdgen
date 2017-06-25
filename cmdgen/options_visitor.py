import itertools
from .dispatch import dispatch
from .ast import *

__all__ = [
    'OptionsVisitor'
]

class OptionsVisitor(object):
    def __init__(self):
        pass

    @dispatch(on_arg_index=1)
    def visit(self,node):
        print 'default visitor in',type(self),'for',type(node)

    @visit.when(Program)
    def visit(self,program,env=None):
        if program.sequence is None:
            return []

        current_env = program.definitions
        if env is not None:
            current_env = program.definitions.copy()
            current_env.update(env)

        options = self.visit(program.sequence.evaluate(env=current_env))
        return [' '.join(i.split()) for i in options]

    @visit.when(Primitive)
    def visit(self, primitive):
        return [primitive.value]

    @visit.when(Delimiter)
    def visit(self, delimiter):
        return [delimiter.value]

    @visit.when(Range)
    def visit(self,range_node):
        return [str(i) for i in xrange(range_node.start,range_node.end+1)]

    @visit.when(Parameter)
    def visit(self, parameter):
        return [str(parameter)]

    @visit.when(StringParameter)
    def visit(self, parameter):
        return [str(parameter)]

    @visit.when(IntParameter)
    def visit(self, parameter):
        return [str(parameter)]

    @visit.when(Options)
    def visit(self, options_node):
        options = [self.visit(i) for i in options_node.contents]
        if options_node.optional:
            options = [['']] + options
        return list(itertools.chain(*options))

    @visit.when(MinReqOptions)
    def visit(self, options_node):
        options = [self.visit(i) for i in options_node.contents]

        result = []
        for i in range(options_node.min_options,len(options)+1):
            for j in itertools.combinations(options,i):
                result += [' '.join(k) for k in itertools.product(*j)]
        return result

    @visit.when(Sequence)
    def visit(self, sequence):
        options = [self.visit(i) for i in sequence.contents]
        if len(options) > 1:
            return [sequence.separator.join(i)
                    for i in itertools.product(*options)]
        else:
            return options[0]