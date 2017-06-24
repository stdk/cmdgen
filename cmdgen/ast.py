import itertools

from .cli import *

__all__ = [
    'Program',
    'Definitions',
    'Definition',
    'Delimiter',
    'Primitive',
    'Variable',
    'Parameter',
    'StringParameter',
    'IntParameter',
    'Range',
    'Options',
    'Sequence',
]

import sys

DEBUG = False
DEBUG_FUNCTIONS = ['evaluate']

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
    def __init__(self,definitions,sequence=None):
        self.definitions = definitions
        self.sequence = sequence

    def __str__(self):
        return '%s <-> %s' % (self.definitions,self.sequence)
    __repr__ = __str__

    @debug_available
    def get_options(self,env=None):
        if self.sequence is None:
            return []

        current_env = self.definitions
        if env is not None:
            current_env = self.definitions.copy()
            current_env.update(env)

        options = self.sequence.evaluate(env=current_env).get_options()
        return [' '.join(i.split()) for i in options]

    @debug_available
    def convert_to_cli(self,env=None,level=None):
        if self.sequence is None:
            return []

        current_env = self.definitions
        if env is not None:
            current_env = self.definitions.copy()
            current_env.update(env)
        options = self.sequence.evaluate(env=current_env).convert_to_cli()
        return [CLICommand(option,level) for option in options]

class Definitions(object):
    def __init__(self,env=None):
        if env is None:
            env = {}
        self.env = env

    @staticmethod
    def list_of_strings_to_ast(options_list):
        options = [Sequence([Primitive(s) for s in option.split()])
                   for option in options_list]
        return Options([i.simplify() for i in options])

    @classmethod
    def from_string_options(cls,options_dict):
        env = { key: cls.list_of_strings_to_ast(options_dict[key])
                for key in options_dict }
        for key in env:
            env[key].name = key
        return Definitions(env)

    def copy(self):
        return Definitions(env=self.env)

    def add_definition(self,definition):
        self.env[definition.name] = definition.evaluate(env=self.env).simplify()


    def update(self,definitions):
        self.env.update(definitions.env)

    def __getitem__(self,key):
        return self.env[key]

    def __contains__(self,key):
        return key in self.env

    def __str__(self):
        return str(self.env)
    __repr__ = __str__

class Definition(object):
    def __init__(self,name,value):
        self.name = name
        self.value = value

    @debug_available
    def evaluate(self,env=None):
        result = self.value.evaluate(env)
        result.name = self.name
        return result

    # @debug_available
    # def get_options(self,env):
    #     return self.value.get_options(env)

    # @debug_available
    # def convert_to_cli(self,env):
    #     contents = self.value.convert_to_cli(env)
    #     singular = extract_singular_element(contents,check_type=CLICommandParam)
    #     if singular is not None:
    #         t = singular.type
    #         if type(t) == CLIEnum:
    #             t.name = self.name

    #     return contents

    def __str__(self):
        return 'Definition[$%s = %s]' % (self.name,self.value)
    __repr__ = __str__

class ASTNode(object):
    name = None

    def simplify(self):
        return self

    def __str__(self):
        return 'ASTNode'

    @debug_available
    def evaluate(self,env=None):
        return self

    @debug_available
    def get_options(self,env=None):
        return []

    @debug_available
    def convert_to_cli(self,env=None):
        return []

class Delimiter(ASTNode):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return '!'
    __repr__ = __str__

    @debug_available
    def get_options(self,env=None):
        return [self.value]

    @debug_available
    def convert_to_cli(self, env=None):
        return [[CLIDelimiter()]]

class Primitive(ASTNode):
    def __init__(self,value):
        self.name = value
        self.value = value

    def __str__(self):
        return self.value
    __repr__ = __str__

    @debug_available
    def get_options(self,env=None):
        return [self.value]

    @debug_available
    def convert_to_cli(self, env=None):
        return [[CLINode(self.value)]]

class VariableError(Exception):
    def __init__(self, name):
        msg = 'Variable(%s) not found' % (name,)
        super(VariableError, self).__init__(msg)

class Variable(ASTNode):
    def __init__(self,name):
        self.name = name

    def __str__(self):
        return '$%s' % (self.name,)
    __repr__ = __str__

    @debug_available
    def evaluate(self,env):
        if env is None or self.name not in env:
            raise VariableError(self.name)
        return env[self.name]

    # @debug_available
    # def get_options(self,env=None):
    #     if env is None or self.name not in env:
    #         raise VariableError(self.name)
    #     return env[self.name].get_options(env)

    # @debug_available
    # def convert_to_cli(self,env=None):
    #     if env is None or self.name not in env:
    #         raise VariableError(self.name)
    #     return env[self.name].convert_to_cli(env)

class Range(ASTNode):
    @staticmethod
    def to_int(s):
        try:
            return int(s)
        except ValueError:
            return 0

    def __init__(self,start,end):
        self.start,self.end = sorted((Range.to_int(start),Range.to_int(end)))

    def __str__(self):
        return 'Range(%d~%d)' % (self.start,self.end)
    __repr__ = __str__

    @debug_available
    def get_options(self,env=None):
        return [str(i) for i in xrange(self.start,self.end+1)]

    @debug_available
    def convert_to_cli(self,env=None):
        return [[CLINode(str(i))] for i in xrange(self.start,self.end+1)]

class Parameter(ASTNode):
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
    def get_options(self,env=None):
        return [str(self)]

    @debug_available
    def convert_to_cli(self, env=None):
        return [[CLICommandParam(self.name,self.type)]]

class StringParameter(Parameter):
    def __init__(self,name,max_length):
        self.name = name
        self.max_length = Range.to_int(max_length)
        self.type = CLIString(self.max_length)

    def __str__(self):
        return '<%s %s>' % (self.name,self.max_length)
    __repr__ = __str__

class IntParameter(Parameter):
    def __init__(self,name,start,end):
        self.name = name
        self.start = Range.to_int(start)
        self.end = Range.to_int(end)
        self.type = CLIInt(self.start,self.end)

    def __str__(self):
        return '<%s %s-%s>' % (self.name,self.start,self.end)
    __repr__ = __str__

class Options(ASTNode):
    def __init__(self,contents=None,optional=False):
        if contents is None:
            contents = []
        self.contents = contents
        self.optional = optional

    def simplify(self):
        if self.optional is False:
            if len(self.contents) == 1:
                return self.contents[0]
        return self

    def append(self,element):
        self.contents.append(element.simplify())

    def convert_to_min_req_options(self,min_options=None):
        return MinReqOptions(self.contents,min_options=min_options)

    def __len__(self):
        return len(self.contents)

    def __str__(self):
        return '%s[%s]%s' % ('?' if self.optional else '',
                             '|'.join([str(i) for i in self.contents]),
                             '%%%s' % (self.name,) if self.name is not None else '')
    __repr__ = __str__

    @debug_available
    def evaluate(self,env=None):
        return Options([i.evaluate(env) for i in self.contents],
                        optional=self.optional).simplify()

    @debug_available
    def get_options(self,env=None):
        options = [i.get_options(env) for i in self.contents]
        if self.optional:
            options = [['']] + options
        return list(itertools.chain(*options))

    @debug_available
    def convert_to_cli(self, env=None):
        if all(type(i)==Primitive for i in self.contents):
            t = CLIEnum(self.name,[i.value for i in self.contents])
            return [[CLICommandParam(None,t,optional=self.optional)]]

        options = [i.convert_to_cli(env) for i in self.contents]

        if self.optional:
            if len(options) == 1:
                param = extract_singular_element(options[0],check_type=CLICommandParam)
                if param is not None:
                    altered_param = param.copy()
                    altered_param.optional = True
                    return [[altered_param]]

            options = [[]] + options

        return list(itertools.chain(*options))

class MinReqOptions(ASTNode):
    def __init__(self,contents=None,min_options=None):
        if contents is None:
            contents = []
        self.contents = contents

        if ( min_options is None 
             or min_options > len(self.contents)
             or min_options < 1 ):
            min_options = len(self.contents)

        self.min_options = min_options

    def simplify(self):
        if len(self.contents) == 1:
            return self.contents[0]
        return self

    def __str__(self):
        return '[%s](%s)%s' % ('|'.join([str(i) for i in self.contents]),
                             self.min_options,
                             '%%%s' % (self.name,) if self.name is not None else '')
    __repr__ = __str__

    @debug_available
    def evaluate(self,env=None):
        return MinReqOptions([i.evaluate(env) for i in self.contents],
                              min_options=self.min_options).simplify()

    @debug_available
    def get_options(self,env=None):
        options = [i.get_options(env) for i in self.contents]

        result = []
        for i in range(self.min_options,len(options)+1):
            for j in itertools.combinations(options,i):
                result += [' '.join(k) for k in itertools.product(*j)]
        return result

    @debug_available
    def convert_to_cli(self, env=None):
        options = [i.convert_to_cli(env) for i in self.contents]

        result = []
        for i in range(self.min_options,len(options)+1):
            for j in itertools.combinations(options,i):
                result += [CLIDelimiter.join(k) for k in itertools.product(*j)]
        return result

class Sequence(ASTNode):
    def __init__(self,contents,separator=None):
        self.contents = [i.simplify() for i in contents]
        self.separator = ''

    def append(self,*elements):
        self.contents += [i.simplify() for i in elements]
        return self

    def simplify(self):
        if len(self.contents) == 1:
            return self.contents[0]
        return self

    def __str__(self):
        return "'%s'%s" % (' '.join([str(i) for i in self.contents]),
                           '%%%s' % (self.name,) if self.name is not None else '')

    __repr__ = __str__

    @debug_available
    def evaluate(self,env=None):
        return Sequence([i.evaluate(env) for i in self.contents],
                         self.separator).simplify()

    @debug_available
    def get_options(self,env=None):
        options = [i.get_options(env) for i in self.contents]
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
    def convert_to_cli(self, env=None):
        options = [i.convert_to_cli(env) for i in self.contents]

        if len(options) > 1:
            sequences = [list(itertools.chain(*i))
                         for i in itertools.product(*options)]

            return [self.try_replace_with_key_param(s) for s in sequences]
        else:
            return options[0]