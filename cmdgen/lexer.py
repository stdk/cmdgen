from preprocessor import preprocess

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

class CustomLexer(object):
    def __init__(self,lexer):
        self.lexer = lexer
        self.token_gen = None
        self.debug = False
        self.errors = None

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
        self.errors = []
        self.lexer.errors = self.errors
        self.token_gen = self.generator(self.lexer.token)

        ps = preprocess(s)

        return self.lexer.input(ps)

    def token(self):
        token = self.token_gen.next()
        if self.debug and token is not None:
            import sys
            print >> sys.stderr, token
        return token

lexer = CustomLexer(lex.lex())