#!/usr/bin/python

tokens = ('TEXT',)

states = (
    ('comment','exclusive'),
)

def to_text(t):
    t.type = 'TEXT'
    return t

def to_whitespace(t):
    t.type = 'TEXT'
    t.value = ' '*len(t.value)
    return to_text(t)

def t_TEXT_begin_comment(t):
    r'\(+\*'
    t.lexer.push_state('comment')
    t.value = '('*(len(t.value)-2) + '  '
    return to_text(t)

def t_TEXT_normal1(t):
    r'[^(\n]+'
    return to_text(t)

def t_TEXT_normal2(t):
    r'\(+[^*\n]'
    return to_text(t)

def t_comment_TEXT_begin(t):
    r'\(+\*'
    t.lexer.push_state('comment')
    return to_whitespace(t)

def t_comment_TEXT_end(t):
    r'\*+\)'
    t.lexer.pop_state()
    return to_whitespace(t)

def t_comment_TEXT_skip_unimportant(t):
    r'[^(*\n]+'
    return to_whitespace(t)

def t_comment_TEXT_skip_false_end(t):
    r'\*+[^)*\n]'
    return to_whitespace(t)

def t_comment_TEXT_skip_false_begin(t):
    r'\(+[^*\n]'
    return to_whitespace(t)

t_ignore = ''
t_comment_ignore = ''

def t_newline(t):
    r'\n+'
    return to_text(t)

def t_comment_newline(t):
    r'\n+'
    return to_text(t)

def t_error(t):
    print 'Error1'

def t_comment_error(t):
    print 'Error2'

# Build the lexer
import ply.lex as lex
lexer = lex.lex()

def tokenize(s):
    lexer.input(s)
    while True:
        token = lexer.token()
        #print token
        if token is None: 
            break
        yield token.value

#'$mode = {ipv4|ipv6}; (** mode definition **)\\n$conf = {normal|broken}; (* ///(* conf **))/\\\\)\\\\ definition **)\\n$key_args = [mode $mode] [conf $conf]; (**** multi\\nline\\n comment  *****)\\ncmd $key_args'

def preprocess(s):
    '''
    >>> src = """$mode = {ipv4|ipv6}; (** mode definition **)
    ... $conf = {normal|broken}; (* ///(((*** conf **))/\)\ definition **)
    ... $key_args = [mode $mode] [conf $conf]; (+ ((**** multi /\/\/
    ... line * * * * ( ) ( ) ( * )
    ...  comment  *****)))
    ... cmd $key_args"""
    >>> print '\\n'.join([i.rstrip() for i in preprocess(src).splitlines()])
    $mode = {ipv4|ipv6};
    $conf = {normal|broken};
    $key_args = [mode $mode] [conf $conf]; (+ (
    <BLANKLINE>
                    ))
    cmd $key_args
    '''
    return ''.join(tokenize(s))
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '-n':
        print preprocess(sys.stdin.read())
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
            print preprocess(s)
