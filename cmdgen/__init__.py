from .lexer import lexer
from .parser import parser,SyntaxError
from .cli import XMLGenerator,CLIContext

import itertools

__all__ = [
    'parse_into_options',
    'parse'
]

def parse_into_options(s, env=None, mode=None, verbose=False):
    '''
    >>> parse_into_options('test\\n[a|b|c]\\nd|e')
    Line 3 column 2 -> syntax error at '|'
    []
    >>> parse_into_options('command test !')
    Warning: Line 1 column 14: illegal character '!' skipped
    ['command test']
    >>> parse_into_options('test {[a} b]')
    Line 1 column 9 -> syntax error at '}'
    []
    >>> parse_into_options('a b c [1')
    Syntax error: not enough tokens to complete parsing
    []
    >>> parse_into_options('$a  =   test     ;\\n\\n\\n   \\n\\n    123  $ ')
    Line 6 column 11 -> syntax error at ' '
    []
    >>> parse_into_options('   a   b  c ')
    ['a b c']
    >>> parse_into_options('ping [domain {a|b}|ipv6 addr|ipv4 addr]')
    ['ping domain', 'ping domain a', 'ping domain b', 'ping ipv6 addr', 'ping ipv4 addr']
    >>> parse_into_options('[a|b|c] d {f|g|h}')
    ['a d', 'a d f', 'a d g', 'a d h', 'b d', 'b d f', 'b d g', 'b d h', 'c d', 'c d f', 'c d g', 'c d h']
    >>> parse_into_options('cmd [{[a] b} c]')
    ['cmd c', 'cmd a b c']
    >>> parse_into_options('test {x} {y} -te-st-')
    ['test -te-st-', 'test y -te-st-', 'test x -te-st-', 'test x y -te-st-']
    >>> parse_into_options('$var=a b c; $var')
    ['a b c']
    >>> parse_into_options('  $mode = [ipv4|ipv6];\\n$conf = [normal|broken];\\n $key_args = {mode $mode} {conf $conf};\\ncmd $key_args')
    ['cmd', 'cmd conf normal', 'cmd conf broken', 'cmd mode ipv4', 'cmd mode ipv4 conf normal', 'cmd mode ipv4 conf broken', 'cmd mode ipv6', 'cmd mode ipv6 conf normal', 'cmd mode ipv6 conf broken']
    >>> parse_into_options('single int 1 2 -3')
    ['single int 1 2 -3']
    >>> parse_into_options('int range 1~2 4~3')
    ['int range 1 3', 'int range 1 4', 'int range 2 3', 'int range 2 4']
    >>> parse_into_options('ip address 192.168.19.1~3 /[16|24]')
    ['ip address 192.168.19.1 /16', 'ip address 192.168.19.1 /24', 'ip address 192.168.19.2 /16', 'ip address 192.168.19.2 /24', 'ip address 192.168.19.3 /16', 'ip address 192.168.19.3 /24']
    >>> parse_into_options('$mode = [ipv4|ipv6] ; (** mode definition **) \\n $conf = [normal|broken]; (* ///(* conf **))/\\\\)\\\\ definition **)\\n$key_args={mode $mode} {conf $conf}; (**** multi\\nline\\n comment  *****)\\ncmd $key_args')
    ['cmd', 'cmd conf normal', 'cmd conf broken', 'cmd mode ipv4', 'cmd mode ipv4 conf normal', 'cmd mode ipv4 conf broken', 'cmd mode ipv6', 'cmd mode ipv6 conf normal', 'cmd mode ipv6 conf broken']
    >>> parse_into_options('ping server.[a|b][1|2]')
    ['ping server.a1', 'ping server.a2', 'ping server.b1', 'ping server.b2']
    >>> parse_into_options('permit 00:11:22~23:33:44~45:55')
    ['permit 00:11:22:33:44:55', 'permit 00:11:22:33:45:55', 'permit 00:11:23:33:44:55', 'permit 00:11:23:33:45:55']
    >>> parse_into_options('punctuation,is..good,,1~3')
    ['punctuation,is..good,,1', 'punctuation,is..good,,2', 'punctuation,is..good,,3']
    >>> parse_into_options('delimiter[ |-|+]test')
    ['delimiter test', 'delimiter-test', 'delimiter+test']
    >>> parse_into_options('line\\nbreak\\nused')
    ['line break used']
    >>> parse_into_options(' \\n \\n $a \\n = \\n extra \\n ; \\n $a whitespaces')
    ['extra whitespaces']
    >>> parse_into_options('whitespaces[ must| should|-hell]')
    ['whitespaces must', 'whitespaces should', 'whitespaces-hell']
    >>> parse_into_options('white{-a-| b }space')
    ['whitespace', 'white-a-space', 'white b space']
    >>> parse_into_options(' \\n \\n $a \\n = \\n extra \\n \\n ; \\n $$a whitespaces \\n \\n with error')
    Line 8 column 3 -> syntax error at '$'
    []
    >>> parse_into_options('delete dhcpv6 pool [<pool_name 12> | all]')
    ['delete dhcpv6 pool <pool_name 12>', 'delete dhcpv6 pool all']
    >>> parse_into_options('config dhcp_relay {hops <int 1-16> | time <sec 0-65535>}(1)')
    ['config dhcp_relay hops <int 1-16>', 'config dhcp_relay time <sec 0-65535>', 'config dhcp_relay hops <int 1-16> time <sec 0-65535>']
    >>> parse_into_options('config dhcpv6 pool excluded_address <pool_name 12> [add begin <ipv6addr> end <ipv6addr> | delete [begin <ipv6addr> end <ipv6addr> | all]]')
    ['config dhcpv6 pool excluded_address <pool_name 12> add begin <ipv6addr ipv6addr> end <ipv6addr ipv6addr>', 'config dhcpv6 pool excluded_address <pool_name 12> delete begin <ipv6addr ipv6addr> end <ipv6addr ipv6addr>', 'config dhcpv6 pool excluded_address <pool_name 12> delete all']
    '''

    program,errors = parse(s,mode=mode,verbose=verbose)

    for error in errors:
        print error

    if program is None:
        return []

    return program.get_options(env=env)

def parse(s, mode=None, verbose=False):
    program = None
    errors = []

    current_lexer = lexer.clone(mode=mode,verbose=verbose)
    try:
        program = parser.parse(s,lexer=current_lexer)
    except SyntaxError as e:
        errors.append(str(e))
    finally:
        errors = current_lexer.errors + errors

    return program,errors

class InputHandler(object):
    def __init__(self,mode=None,verbose=False,cli=False):
        self.mode = mode
        self.verbose = verbose
        self.cli = cli
        self.env = {}
        
        self.interactive_seen = []
        self.interactive_options = {}
        
        self.interactive_commands = {
            'clear': self.interactive_clear,
            'show': self.interactive_show,
            'xml': self.interactive_xml,
            'set': self.interactive_set
        }
        
    def interactive_clear(self,*args):
        self.interactive_seen = []
        self.interactive_options = {}
        
    def interactive_show(self,*args):
        print 'options:', self.interactive_options
        for program in self.interactive_seen:
            print 'CMD:',program
            
            for option in program.get_options(env=self.env):
                print option
            
            if self.cli:
                commands = program.convert_to_cli()
                for command in commands:
                    print command
    
    def interactive_xml(self,out_folder=None,*args):
        if out_folder is None:
            out_folder = 'out'
        all_seen_commands = itertools.chain(*(p.convert_to_cli() for p in self.interactive_seen))

        generator = XMLGenerator(out_folder=out_folder,**self.interactive_options)
        generator.generate(list(all_seen_commands))
        
    def interactive_set(self,*args):
        def update_option(key,value=None,*args):
            if value is None and key in self.interactive_options:
                del self.interactive_options[key]
            else:
                self.interactive_options[key] = value
    
        [update_option(*arg.split('=')) for arg in args]

    def load_definitions(self, filename):
        print 'Loading definition from %s...' % (filename,)
        program, errors = parse(open(filename,'r').read())
        for error in errors:
            print error
            
        if program is None:
            print 'Loading failed'
            return
            
        self.env = program.environment
        
    def handle_interactive_command(self, s):
        if s.startswith('!'):
            args = s[1:].split()
            if args[0] in self.interactive_commands:
                self.interactive_commands[args[0]](*args[1:])
            else:
                print 'Unknown command'
            return True

    def process_specific_input(self, s):
        program, errors = parse(s,mode=self.mode,verbose=self.verbose)
        for error in errors:
            print error
            
        if program is None:
            return

        self.interactive_seen.append(program)

        for option in program.get_options(env=self.env):
            print option

        if self.cli:
            commands = program.convert_to_cli()
            for command in commands:
                print command            

    def process_interactive_input(self, s):
        if self.handle_interactive_command(s):
            return
    
        return self.process_specific_input(s)


def main():
    import sys
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-m','--mode',type=str,
                            help='Select syntax mode: old, new. Defaults to new')
    arg_parser.add_argument('-i','--input',type=str,
                            help='get input from specified source instead of interactive mode: accepts filename or - for stdin')
    arg_parser.add_argument('-v','--verbose',action='store_true',
                            help='verbose lexer mode')
    arg_parser.add_argument('-c','--cli',action='store_true',
                            help='Enable convertion of commands into CLI nodes')
    arg_parser.add_argument('-t','--test',action='store_true',
                            help='perform self-testing procedure')
    arg_parser.add_argument('-d','--definitions',type=str,
                            help='load definitions from a given file')
    args = arg_parser.parse_args()

    if args.test == True:
        import doctest
        doctest.run_docstring_examples(parse_into_options,globals())
        print 'Tests completed'
        sys.exit(0)

    input_handler = InputHandler(mode=args.mode,
                                 verbose=args.verbose,
                                 cli=args.cli)
                                 
    specific_input = None
    if args.input == '-':
        specific_input = sys.stdin.read()
    elif args.input is not None:
        specific_input = open(args.file).read()

    if args.definitions is not None:
        input_handler.load_definitions(args.definitions)
        
    if specific_input is not None:
        input_handler.process_specific_input(specific_input)
    else:
        while True:
            try:
                s = raw_input('# ')
                if not s:
                    continue
                while s[-1] == '\\':
                    s = s[:-1] + '\n' + raw_input('>')
            except (EOFError,KeyboardInterrupt):
                break
            input_handler.process_interactive_input(s)