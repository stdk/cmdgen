#!/usr/bin/python

import itertools
from preprocessor import preprocess

DEBUG=False

# states = (
#     ('comment','exclusive'),
#)

tokens = ('ID','NODE','NUMBER','ASSIGN','SEMICOLON','WHITESPACE')
literals = ('|','{','}','[',']','$','~')

t_ID         = r'[a-zA-Z_][a-zA-Z0-9_]*'
t_NODE       = r'[:/+-.]+'
t_NUMBER     = r'-?[0-9]+'

def t_ASSIGN(t):
    r'[ \t\n]*=[ \t\n]*'
    t.lexer.lineno.process(t)
    return t

def t_SEMICOLON(t):
    r'[ \t\n]*;[ \t\n]*'
    t.lexer.lineno.process(t)
    return t

t_WHITESPACE = r'[ \t]+'

t_ignore = ''

def t_newline(t):
    r'\n+'
    t.lexer.lineno.process(t)
    t.type = 'WHITESPACE'
    return t

def t_error(t):
    args = (t.lineno.lineno,t.lexpos - t.lineno.startpos + 1,t.value[0])
    print "Warning: Line %d column %d: illegal character '%s' skipped" % args
    t.lexer.skip(1)    

import ply.lex as lex

class ExtendedLineNo(object):
    def __init__(self,lineno,startpos):
        self.lineno = lineno
        self.startpos = startpos
    def process(self,token):
        count = token.value.count('\n')
        if count > 0:
            self.lineno += count
            self.startpos = (token.lexer.lexpos 
                             + token.value.rfind('\n') + 1
                             - len(token.value))
    def __int__(self):
        return self.lineno
    def __str__(self):
        return str((self.lineno,self.startpos))

class CustomLexer(object):
    def __init__(self,lexer):
        self.lexer = lexer
        self.token_gen = None

    def generator(self,get_token):
        initial_state = True
        whitespace_before = False

        while True:
            token = get_token()

            if token is None:
                yield None
                break

            is_whitespace = token.type == 'WHITESPACE'

            if initial_state:
                if is_whitespace:
                    continue
                else:
                    initial_state = False
            
            if whitespace_before:
                if is_whitespace:
                    continue
                else:
                    whitespace_before = False

            if is_whitespace:
                whitespace_before = True                    

            yield token


    def input(self,s):
        self.lexer.lineno = ExtendedLineNo(1,0)
        self.token_gen = self.generator(self.lexer.token)
        return self.lexer.input(s)

    def token(self):
        return self.token_gen.next()

# Build the lexer
lexer = CustomLexer(lex.lex())

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

def p_program(p):
    'program : definition_list command'
    p[0] = Program(p[1],p[2])

def p_program_short(p):
    'program : command'
    p[0] = Program(None,p[1])

def p_definition_list_single(p):
    'definition_list : definition'
    p[0] = DefinitionList(p[1])

def p_definition_list(p):
    'definition_list : definition_list definition'
    p[1].update(p[2])
    p[0] = p[1]

def p_definition(p):
    'definition : "$" ID ASSIGN node_sequence SEMICOLON'
    p[0] = Definition(p[2],p[4])

def p_command(p):
    'command : node_sequence'
    p[0] = Command(p[1])

def p_node_sequence_single(p):
    'node_sequence : node'
    p[0] = NodeSequence([p[1]])

def p_node_sequence_single_whitespace(p):
    'node_sequence : whitespace_list'
    p[0] = NodeSequence([NodeSequence.space])

def p_node_sequence_normal(p):
    'node_sequence : node_sequence node'
    p[0] = p[1].append(p[2])

def p_node_sequence_whitespace(p):
    'node_sequence : node_sequence whitespace_list'
    p[0] = p[1].append_whitespace()

def p_whitespace_list_single(p):
    'whitespace_list : WHITESPACE'
    p[0] = Node(' ',primitive=True)

def p_whitespace_list(p):
    'whitespace_list : whitespace_list WHITESPACE'
    p[0] = p[1]

def p_node_id(p):
    'node : ID'    
    p[0] = Node(p[1],primitive=True)

def p_node_node(p):
    'node : NODE'
    p[0] = Node(p[1],primitive=True)

def p_node_number(p):
    'node : NUMBER'    
    p[0] = Node(p[1],primitive=True)

def p_node_range(p):
    'node : NUMBER "~" NUMBER'
    p[0] = Range(p[1],p[3])

def p_node_variable(p):
    'node : "$" ID'    
    p[0] = Variable(p[2])    
    
def p_node_optional_group(p):
    'node : "[" node_options "]"'
    p[0] = Node(p[2],optional=True)
    
def p_node_mandatory_group(p):
    'node : "{" node_options "}"'
    p[0] = Node(p[2])

def p_node_options_single(p):
    'node_options : node_sequence'
    p[0] = NodeOptions([p[1]])    
    
def p_node_options(p):
    'node_options : node_options "|" node_sequence'
    p[0] = p[1] + NodeOptions([p[3]])

class SyntaxError(Exception):
    format = "Line %d column %d -> syntax error at '%s'"

    def __init__(self,p=None):
        if p:
            msg = self.format % (p.lineno.lineno,p.lexpos - p.lineno.startpos + 1,p.value)
        else:
            msg = 'Syntax error: not enough tokens to complete parsing'
        super(self.__class__, self).__init__(msg)
   
def p_error(p):
    raise SyntaxError(p)

import ply.yacc as yacc
parser = yacc.yacc()

def parse(s):
    '''
    >>> parse('test\\n{a|b|c}\\nd|e')
    Line 3 column 2 -> syntax error at '|'
    []
    >>> parse('command test !')
    Warning: Line 1 column 14: illegal character '!' skipped
    ['command test']
    >>> parse('test {[a} b]')
    Line 1 column 9 -> syntax error at '}'
    []
    >>> parse('a b c [1')
    Syntax error: not enough tokens to complete parsing
    []
    >>> parse('$a  =   test     ;\\n\\n\\n   \\n\\n    123  $ ')
    Line 6 column 11 -> syntax error at ' '
    []
    >>> parse('   a   b  c ')
    ['a b c']
    >>> parse('ping {domain [a|b]|ipv6 addr|ipv4 addr}')
    ['ping domain', 'ping domain a', 'ping domain b', 'ping ipv6 addr', 'ping ipv4 addr']
    >>> parse('{a|b|c} d [f|g|h]')
    ['a d', 'a d f', 'a d g', 'a d h', 'b d', 'b d f', 'b d g', 'b d h', 'c d', 'c d f', 'c d g', 'c d h']
    >>> parse('cmd {[{a} b] c}')
    ['cmd c', 'cmd a b c']
    >>> parse('test [x] [y] -te-st-')
    ['test -te-st-', 'test y -te-st-', 'test x -te-st-', 'test x y -te-st-']
    >>> parse('$var=a b c; $var')
    ['a b c']
    >>> parse('  $mode = {ipv4|ipv6};\\n$conf = {normal|broken};\\n $key_args = [mode $mode] [conf $conf];\\ncmd $key_args')
    ['cmd', 'cmd conf normal', 'cmd conf broken', 'cmd mode ipv4', 'cmd mode ipv4 conf normal', 'cmd mode ipv4 conf broken', 'cmd mode ipv6', 'cmd mode ipv6 conf normal', 'cmd mode ipv6 conf broken']
    >>> parse('single int 1 2 -3')
    ['single int 1 2 -3']
    >>> parse('int range 1~2 4~3')
    ['int range 1 3', 'int range 1 4', 'int range 2 3', 'int range 2 4']
    >>> parse('ip address 192.168.19.1~3 /{16|24}')
    ['ip address 192.168.19.1 /16', 'ip address 192.168.19.1 /24', 'ip address 192.168.19.2 /16', 'ip address 192.168.19.2 /24', 'ip address 192.168.19.3 /16', 'ip address 192.168.19.3 /24']
    >>> parse('$mode = {ipv4|ipv6} ; (** mode definition **) \\n $conf = {normal|broken}; (* ///(* conf **))/\\\\)\\\\ definition **)\\n$key_args=[mode $mode] [conf $conf]; (**** multi\\nline\\n comment  *****)\\ncmd $key_args')
    ['cmd', 'cmd conf normal', 'cmd conf broken', 'cmd mode ipv4', 'cmd mode ipv4 conf normal', 'cmd mode ipv4 conf broken', 'cmd mode ipv6', 'cmd mode ipv6 conf normal', 'cmd mode ipv6 conf broken']
    >>> parse('ping server.{a|b}{1|2}')
    ['ping server.a1', 'ping server.a2', 'ping server.b1', 'ping server.b2']
    >>> parse('permit 00:11:22~23:33:44~45:55')
    ['permit 00:11:22:33:44:55', 'permit 00:11:22:33:45:55', 'permit 00:11:23:33:44:55', 'permit 00:11:23:33:45:55']
    >>> parse('punctuation,is..good,,1~3')
    ['punctuation,is..good,,1', 'punctuation,is..good,,2', 'punctuation,is..good,,3']
    >>> parse('delimiter{ |-|+}test')
    ['delimiter test', 'delimiter-test', 'delimiter+test']
    >>> parse('line\\nbreak\\nused')
    ['line break used']
    >>> parse(' \\n \\n $a \\n = \\n extra \\n ; \\n $a whitespaces')
    ['extra whitespaces']
    >>> parse(' \\n \\n $a \\n = \\n extra \\n \\n ; \\n $$a whitespaces \\n \\n with error')
    Line 8 column 3 -> syntax error at '$'
    []
    '''

    ps = preprocess(s)

    # lexer.lineno = ExtendedLineNo(1,0)
    # lexer.input(ps)
    # while True:
    #     tok = lexer.token()
    #     if not tok: 
    #         break      # No more input
    #     print(tok)

    try:
        program = parser.parse(ps,lexer=lexer)
        return program.get_options()
    except SyntaxError as e:
        print e

    return []

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '-n':
        for option in parse(sys.stdin.read()):
            print option
    else:
        import doctest
        doctest.testmod()

        while True:
            try:
                s = raw_input('# ')
            except (EOFError,KeyboardInterrupt):
                break
            if not s:
                continue
            for option in parse(s):
                print option