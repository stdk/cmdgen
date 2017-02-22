from cmd_lexer import lexer
from cmd_parser import parser,SyntaxError

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

    # lexer.lineno = ExtendedLineNo(1,0)
    # lexer.input(ps)
    # while True:
    #     tok = lexer.token()
    #     if not tok: 
    #         break      # No more input
    #     print(tok)

    try:
        program = parser.parse(s,lexer=lexer)
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