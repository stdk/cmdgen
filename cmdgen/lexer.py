from preprocessor import preprocess
from itertools import chain

tokens = ('ID','NODE','NUMBER','ASSIGN','SEMICOLON','WHITESPACE',
          'VARIABLE_ROLE_BRACE','MANDATORY_BRACE_BEGIN','MANDATORY_BRACE_END','OPTIONAL_BRACE_BEGIN','OPTIONAL_BRACE_END')
literals = ('|','<','>','(',')','$','~','-')

t_ID         = r'[a-zA-Z_][a-zA-Z0-9_]*'
t_NODE       = r'[:/+.,]+'
t_NUMBER     = r'[0-9]+'

t_VARIABLE_ROLE_BRACE = r'[\{\}\[\]]'

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
    t.lexer.errors.append("Warning: Line %d column %d: illegal character '%s' skipped" % args)
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

class TokenIterator(object):
    def __init__(self,get_token):
        self.get_token = get_token
        self.token = None
        self.next()

    def peek(self):
        return self.token        

    def next(self):
        token = self.token
        self.token = self.get_token()
        return token

class CustomLexer(object):
    mode_braces = {
        'new': {
            '[': 'MANDATORY_BRACE_BEGIN',
            ']': 'MANDATORY_BRACE_END',
            '{': 'OPTIONAL_BRACE_BEGIN',
            '}': 'OPTIONAL_BRACE_END',
        },            
        'old': {
            '{': 'MANDATORY_BRACE_BEGIN',
            '}': 'MANDATORY_BRACE_END',
            '[': 'OPTIONAL_BRACE_BEGIN',
            ']': 'OPTIONAL_BRACE_END',
        }
    }

    def __init__(self,lexer,mode=None,verbose=False):
        self.lexer = lexer
        self.token_gen = None
        self.verbose = verbose
        self.errors = None

        self.mode = 'new' if mode is None else mode
        self.token_type_for_brace = self.mode_braces[self.mode]

    def clone(self,mode=None,verbose=False):
        return CustomLexer(self.lexer.clone(),mode=mode,verbose=verbose)

    def skip_whitespaces(self,token_iterator):
        while True:
            token = token_iterator.peek()
            if token is None or token.type != 'WHITESPACE':
                break
            token_iterator.next()

    def normal_state(self,token_iterator):
        while True:
            token = token_iterator.peek()
            if token is None:
                break
            
            if token.type == 'VARIABLE_ROLE_BRACE':
                token.type = self.token_type_for_brace[token.value]

            yield token

            if token.type == 'WHITESPACE':
                self.skip_whitespaces(token_iterator)
            else:
                token_iterator.next()

            if token.type == '<':
                for t in  self.ignore_whitespace_state(token_iterator):
                    yield t

    def ignore_whitespace_state(self,token_iterator):
        while True:
            token = token_iterator.peek()
            if token is None or token.type == '>':
                break

            if token.type != 'WHITESPACE':
                yield token

            token_iterator.next()

    def generator(self,get_token):
        token_iterator = TokenIterator(get_token)

        self.skip_whitespaces(token_iterator)

        for token in self.normal_state(token_iterator):
            yield token

        yield None

    def input(self,s):
        self.lexer.lineno = ExtendedLineNo(1,0)
        self.errors = []
        self.lexer.errors = self.errors
        self.token_gen = self.generator(self.lexer.token)

        ps = preprocess(s)

        return self.lexer.input(ps)

    def token(self):
        token = self.token_gen.next()
        if self.verbose and token is not None:
            import sys
            print >> sys.stderr, token
        return token

lexer = CustomLexer(lex.lex())