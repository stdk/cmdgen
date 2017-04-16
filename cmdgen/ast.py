import itertools

from .cli import *

__all__ = [
    'Program',
    'DefinitionList',
    'Definition',
    'Command',
    'Delimiter',
    'PrimitiveNode',
    'Node',
    'Variable',
    'Parameter',
    'StringParameter',
    'IntParameter',
    'Range',
    'NodeOptions',
    'NodeSequence',
]

import sys

DEBUG = False
DEBUG_FUNCTIONS = ['get_options']

def debug_available(method):
    if DEBUG and method.__name__ in DEBUG_FUNCTIONS:
        def inner(self,*args,**kwargs):
            result = method(self,*args,**kwargs)
            print self.__class__.__name__,'<',self,'>',result
            return result
        return inner
    return method

def extract_singular_element(lst,check_type=None):
    if len(lst) == 1 and len(lst[0]) == 1:
        e = lst[0][0]
        if check_type is None:
            return e
        elif type(e) == check_type:
            return e

    return None

class Program(object):
    def __init__(self,definitions,command=None):
        self.definitions = definitions
        self.command = command

    def __str__(self):
        return str(self.command)
    __repr__ = __str__
    
    @debug_available
    def get_options(self,env=None):        
        if self.command is None:
            return []
    
        env = {} if env is None else env.copy()
        env.update(self.definitions.cmd_environment)
        return self.command.get_options(env)

    @debug_available
    def convert_to_cli(self,env=None,level=None):
        if self.command is None:
            return []

        env = {} if env is None else env.copy()
        env.update(self.definitions.cli_environment)
        return self.command.convert_to_cli(environment=env,level=level)

class DefinitionList(object):
    def __init__(self,cmd_environment=None,cli_environment=None):
        if cmd_environment is None:
            cmd_environment = {}
        if cli_environment is None:
            cli_environment = {}

        self.cmd_environment = cmd_environment
        self.cli_environment = cli_environment

    def copy(self):
        return DefinitionList(
            self.cmd_environment.copy(),
            self.cli_environment.copy()
        )
        
    def update(self,definition):
        self.cmd_environment[definition.name] = definition.get_options(self.cmd_environment)
        self.cli_environment[definition.name] = definition.convert_to_cli(self.cli_environment)

    def __str__(self):
        return ' '.join(i for i in self.contents)
    __repr__ = __str__

class Definition(object):
    def __init__(self,name,value):
        self.name = name
        self.value = value

    def get_options(self,environment):
        return self.value.get_options(environment)

    def convert_to_cli(self,environment):
        contents = self.value.convert_to_cli(environment)
        singular = extract_singular_element(contents,check_type=CLICommandParam)
        if singular is not None:
            t = singular.type
            if type(t) == CLIEnum:
                t.name = self.name

        return contents

    def __str__(self):
        return '$%s = %s ;' % (self.name,self.value)
    __repr__ = __str__

class Command(object):
    def __init__(self,contents):
        self.contents = contents
    
    def __str__(self):
        return '%s' % (self.contents,)
    __repr__ = __str__ 
    
    @debug_available
    def get_options(self,environment=None):
        options = self.contents.get_options(environment)
        return [' '.join(i.split()) for i in options]

    @debug_available
    def convert_to_cli(self, environment=None, level=None):
        options = self.contents.convert_to_cli(environment)
        return [CLICommand(option,level) for option in options]

class Delimiter(object):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return self.value
    __repr__ = __str__

    @debug_available
    def get_options(self,environment=None):
        return [self.value]

    def convert_to_cli(self, environment=None):
        return [[CLIDelimiter()]]

class PrimitiveNode(object):
    def __init__(self,name):
        self.name = name

    def __str__(self):
        return self.name
    __repr__ = __str__

    @debug_available
    def get_options(self,environment=None):
        return [self.name]

    @debug_available
    def convert_to_cli(self, environment=None):
        return [[CLINode(self.name)]]

class Node(object):
    def __init__(self,contents,optional=False):
        self.contents = contents
        self.optional = optional

    def __str__(self):
        return '%s(%s)' % ('OPT' if self.optional else '',
                           self.contents)                          
                          
    __repr__ = __str__
    
    @debug_available
    def get_options(self,environment=None):
        options = self.contents.get_options(environment)
        return ([''] if self.optional else []) + options

    def convert_to_cli(self, environment=None):
        options = self.contents.convert_to_cli(environment)
        param = extract_singular_element(options,check_type=CLICommandParam)
        if param is not None:
            altered_param = param.copy()
            altered_param.optional = True
            return [[altered_param]]            
        
        return ([[]] if self.optional else []) + options

class Variable(object):
    def __init__(self,name):
        self.name = name

    def __str__(self):
        return '$%s' % (self.name,)
    __repr__ = __str__

    @debug_available
    def get_options(self,environment=None):
        if environment is None:
            return ['']
        return environment[self.name]

    @debug_available
    def convert_to_cli(self,environment=None):
        if environment is None:
            return ['']
        return environment[self.name]

class Range(object):
    @staticmethod
    def to_int(s):
        try:
            return int(s)
        except ValueError:
            return 0

    def __init__(self,start,end):
        self.start,self.end = sorted((Range.to_int(start),Range.to_int(end)))

    def __str__(self):
        return '%d~%d' % (self.start,self.end)
    __repr__ = __str__

    @debug_available
    def get_options(self,environment=None):
        return [str(i) for i in xrange(self.start,self.end+1)]

    @debug_available
    def convert_to_cli(self,environment=None):
        return [[CLINode(str(i))] for i in xrange(self.start,self.end+1)]        

class Parameter(object):
    def __init__(self,name,type=None):
        self.name = name
        if type is None:
            self.type = CLICustomType(name)
        else:
            self.type = CLICustomType(type)

    def __str__(self):
        return '<%s %s>' % (self.name,self.type.name)
    __repr__ = __str__

    @debug_available
    def get_options(self,environment=None):
        return [str(self)]

    def convert_to_cli(self, environment=None):
        return [[CLICommandParam(self.name,self.type)]]

class StringParameter(object):
    def __init__(self,name,max_length):
        self.name = name
        self.max_length = Range.to_int(max_length)

    def __str__(self):
        return '<%s %s>' % (self.name,self.max_length)
    __repr__ = __str__

    @debug_available
    def get_options(self,environment=None):
        return [str(self)]

    def convert_to_cli(self, environment=None):
        return [[CLICommandParam(self.name,CLIString(self.max_length))]]

class IntParameter(object):
    def __init__(self,name,start,end):
        self.name = name
        self.start = Range.to_int(start)
        self.end = Range.to_int(end)

    def __str__(self):
        return '<%s %s-%s>' % (self.name,self.start,self.end)
    __repr__ = __str__

    @debug_available
    def get_options(self,environment=None):
        return [str(self)]

    @debug_available
    def convert_to_cli(self, environment=None):
        return [[CLICommandParam(self.name,CLIInt(self.start,self.end))]]

class NodeOptions(object):
    def __init__(self,contents,min_options=None):
        self.contents = self.simplify(contents)
        self.min_options = min_options

    @staticmethod
    def simplify(sequence):
        def extract_if_possible(element):
            if hasattr(element,'__len__') and len(element) == 1:
                return element.contents[0]
            return element

        return [extract_if_possible(i) for i in sequence]

    def __add__(self,other):
        return NodeOptions(self.contents+other.contents)
    
    def __len__(self):
        return len(self.contents)

    def __str__(self):
        return '|'.join([str(i) for i in self.contents])
    __repr__ = __str__

    @debug_available
    def get_options(self,environment=None):
        options = [i.get_options(environment) for i in self.contents]
        
        if self.min_options is not None:
            result = []
            for i in range(self.min_options,len(options)+1):    
                for j in itertools.combinations(options,i):
                    result += [' '.join(k) for k in itertools.product(*j)]
            return result
        
        return list(itertools.chain(*options))
        
    @debug_available
    def convert_to_cli(self, environment=None):
        if self.min_options is None and all(type(i)==PrimitiveNode for i in self.contents):
            t = CLIEnum(None,[i.name for i in self.contents])
            return [[CLICommandParam(None,t)]]

        options = [i.convert_to_cli(environment) for i in self.contents]
        
        if self.min_options is not None:
            result = []
            for i in range(self.min_options,len(options)+1):    
                for j in itertools.combinations(options,i):
                    result += [CLIDelimiter.join(k) for k in itertools.product(*j)]
            return result
        
        return list(itertools.chain(*options))
    
class NodeSequence(object):
    def __init__(self,contents,separator=None):        
        self.contents = contents            
        self.separator = ''
    
    def append(self,*elements):
        self.contents += elements
        return self

    def __len__(self):
        return len(self.contents)

    def __str__(self):
        return self.separator.join([str(i) for i in self.contents])
    __repr__ = __str__ 
    
    @debug_available
    def get_options(self,environment=None):
        options = [i.get_options(environment) for i in self.contents]
        if len(options) > 1:
            return [self.separator.join(i)
                    for i in itertools.product(*options)]
        else:
            return options[0]

    def try_replace_with_key_param(self,sequence):
        if [type(i) for i in sequence] != [CLINode,CLIDelimiter,CLICommandParam]:
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
            
    @debug_available
    def convert_to_cli(self, environment=None):
        options = [i.convert_to_cli(environment) for i in self.contents]

        if len(options) > 1:
            sequences = [list(itertools.chain(*i))
                         for i in itertools.product(*options)]
            
            return [self.try_replace_with_key_param(s) for s in sequences]
        else:
            return options[0]