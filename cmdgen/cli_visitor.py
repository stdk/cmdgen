import itertools
from .dispatch import dispatch
from .ast import *
from .cli import *

__all__ = [
    'CLIVisitor'
]

def extract_singular_element(lst,check_type=None):
    if len(lst) == 1 and len(lst[0]) == 1:
        e = lst[0][0]
        if check_type is None:
            return e
        elif type(e) == check_type:
            return e
    return None

class CLIVisitor(object):
    def __init__(self,level=15):
        self.level = level

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
        return [CLICommand(option,self.level) for option in options]

    def try_replace_with_key_param(self,sequence):
        types = [type(i) for i in sequence]
        if types != [CLINode,CLIDelimiter,CLICommandParam]:
            return sequence

        node,_,param = sequence

        if param.positional is False:
            return sequence

        if param.optional is True:
            return sequence

        altered_param = param.copy()
        altered_param.positional = False
        altered_param.key_name = node.name

        return [altered_param]

    @visit.when(Primitive)
    def visit(self, primitive):
        return [[CLINode(primitive.value)]]

    @visit.when(Delimiter)
    def visit(self, delimiter):
        return [[CLIDelimiter()]]

    @visit.when(Range)
    def visit(self,range_node):
        return [[CLINode(str(i))] for i in xrange(range_node.start,range_node.end+1)]

    @visit.when(Parameter)
    def visit(self, parameter):
        return [[CLICommandParam(parameter.name,CLICustomType(parameter.type_name))]]

    @visit.when(StringParameter)
    def visit(self, parameter):
        return [[CLICommandParam(parameter.name,CLIString(parameter.max_length))]]

    @visit.when(IntParameter)
    def visit(self, parameter):
        return [[CLICommandParam(parameter.name,CLIInt(parameter.start,parameter.end))]]

    @visit.when(Options)
    def visit(self, options_node):
        if len(options_node.contents) > 1 and all(type(i)==Primitive for i in options_node.contents):
            t = CLIEnum(options_node.name,[i.value for i in options_node.contents])
            return [[CLICommandParam(None,t,optional=options_node.optional)]]
        
        options = [self.visit(i) for i in options_node.contents]
        
        if options_node.optional:
            if len(options) == 1:
                param = extract_singular_element(options[0],check_type=CLICommandParam)
                if param is not None:
                    altered_param = param.copy()
                    altered_param.optional = True
                    return [[altered_param]]

            options = [[]] + options

        result = list(itertools.chain(*options))
        
        if len(result) > 1:
            if all(len(element)==1 for element in result):
                flat_elements = [element[0] for element in result]
                if all(type(element)==CLICommandParam for element in flat_elements):
                    t = CLIChoiceType(options_node.name,[i.type for i in flat_elements])
                    return [[CLICommandParam(flat_elements[0].name,t,optional=options_node.optional)]]
            
        return result

    @visit.when(MinReqOptions)
    def visit(self, options_node):
        options = [self.visit(i) for i in options_node.contents]

        result = []
        for i in range(options_node.min_options,len(options)+1):
            for j in itertools.combinations(options,i):
                result += [CLIDelimiter.join(k) for k in itertools.product(*j)]
        return result

    def join_node_runs(self,sequence):
        def try_join_nodes(key,group):
            if key == CLINode:
                return [reduce(lambda a,b:a+b,group)]
            if key == CLIDelimiter:
                return [group.next()]
            return list(group)
        
        joined_sequences = (
            try_join_nodes(key,group) 
            for key,group 
            in itertools.groupby(sequence,lambda x:type(x))
        )
        
        return list(itertools.chain(*joined_sequences))
        
    @visit.when(Sequence)
    def visit(self, sequence):
        options = [self.visit(i) for i in sequence.contents]

        if len(options) > 1:
            sequences = [self.join_node_runs(itertools.chain(*i))
                         for i in itertools.product(*options)]
            

            return [self.try_replace_with_key_param(s) for s in sequences]
        else:
            return options[0]