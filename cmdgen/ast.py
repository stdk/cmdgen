import itertools

__all__ = [
    'Program',
    'DefinitionList',
    'Definition',
    'Command',
    'Node',
    'Variable',
    'Range',
    'NodeOptions',
    'NodeSequence',
]

DEBUG=False

def debug_available(method):
    if DEBUG:
        def inner(self):
            result = method(self)
            print self.__class__.__name__,'<',self,'>',result
            return result
        return inner
    return method

class Program(object):
    def __init__(self,definitions,command):
        self.definitions = definitions
        self.environment = definitions.contents if definitions else {}
        self.command = command

    def __str__(self):
        return str(self.command)
    __repr__ = __str__

    @debug_available
    def get_options(self):        
        return self.command.get_options(self.environment)

class DefinitionList(object):
    def __init__(self,definition):
        self.contents = {
            definition.name: definition.evaluate({})
        }

    def update(self,definition):
        self.contents.update({
            definition.name: definition.evaluate(self.contents)
        })

    def __str__(self):
        return ' '.join(i for i in self.contents)
    __repr__ = __str__

class Definition(object):
    def __init__(self,name,value):
        self.name = name
        self.value = value

    def evaluate(self,environment):
        return self.value.get_options(environment)

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
        return self.contents.get_options(environment)

class Node(object):
    def __init__(self,contents,optional=False,primitive=False):
        self.contents = contents
        self.optional = optional
        self.primitive = primitive

    def __str__(self):
        if self.primitive:
            return str(self.contents)
        return '%s%s%s' % ('[' if self.optional else '{',
                           self.contents,
                           ']' if self.optional else '}')
    __repr__ = __str__
    
    @debug_available
    def get_options(self,environment=None):
        if self.primitive:
            return [self.contents]
        return ([''] if self.optional else []) + self.contents.get_options(environment)

class Variable(object):
    def __init__(self,name):
        self.name = name

    @debug_available
    def get_options(self,environment=None):
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

class NodeOptions(object):
    def __init__(self,contents):
        self.contents = contents
    
    def __add__(self,other):
        return NodeOptions(self.contents+other.contents)
    
    def __str__(self):
        return '|'.join([str(i) for i in self.contents])
    __repr__ = __str__

    @debug_available
    def get_options(self,environment=None):
        return sum([i.get_options(environment) for i in self.contents],[])
    
class NodeSequence(object):
    space = Node(' ',primitive=True)

    def __init__(self,contents,separator=None):        
        self.contents = contents
        if separator is None:
            separator = ''
        self.separator = separator
    
    def append(self,*elements):
        self.contents += elements
        return self

    def append_whitespace(self):
        if self.contents[-1] != self.space:
            self.contents.append(self.space)
        return self
    
    def __str__(self):
        return self.separator.join([str(i) for i in self.contents])
    __repr__ = __str__ 
    
    @debug_available
    def get_options(self,environment=None):
        options = [i.get_options(environment) for i in self.contents]
        if len(options) > 1:
            return [' '.join(self.separator.join(i).split())
                    for i in itertools.product(*options)]
        else:
            return options[0]