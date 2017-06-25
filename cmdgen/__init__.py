from .lexer import Lexer
from .parser import Parser,SyntaxError
from collections import defaultdict
from .ast import Definitions
from .cli import XMLGenerator,CLIContext
from .options_visitor import OptionsVisitor
from .cli_visitor import CLIVisitor

import itertools

__all__ = [
    'parse_into_options',
    'parse'
]

def parse_into_options(s, env=None, mode=None, verbose=False):
    '''
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
    >>> parse_into_options('$a $b',env={'a':['a','A'], 'b':['b','B']})
    ['a b', 'a B', 'A b', 'A B']
    >>> parse_into_options('$x = +$b; $a$x',env={'a':['a','A'], 'b':['b','B']})
    ['a+b', 'a+B', 'A+b', 'A+B']
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
    >>> parse_into_options('delete dhcpv6 pool [<pool_name 12> | all]')
    ['delete dhcpv6 pool <pool_name 12>', 'delete dhcpv6 pool all']
    >>> parse_into_options('config dhcp_relay {hops <int 1-16> | time <sec 0-65535>}(1)')
    ['config dhcp_relay hops <int 1-16>', 'config dhcp_relay time <sec 0-65535>', 'config dhcp_relay hops <int 1-16> time <sec 0-65535>']
    >>> parse_into_options('config dhcpv6 pool excluded_address <pool_name 12> [add begin <ipv6addr> end <ipv6addr> | delete [begin <ipv6addr> end <ipv6addr> | all]]')
    ['config dhcpv6 pool excluded_address <pool_name 12> add begin <ipv6addr ipv6addr> end <ipv6addr ipv6addr>', 'config dhcpv6 pool excluded_address <pool_name 12> delete begin <ipv6addr ipv6addr> end <ipv6addr ipv6addr>', 'config dhcpv6 pool excluded_address <pool_name 12> delete all']
    '''
    program,errors = parse(s,mode=mode,
                             verbose=verbose,
                             env=env)

    for error in errors:
        print error

    if program is None:
        return []

    return OptionsVisitor().visit(program)

def parse_into_cli(s):
    '''
    >>> parse_into_cli('1 2 3')
    [Command(1_2_3:15):([Node(1), Node(2), Node(3)]:[])]
    >>> parse_into_cli('  $mode = [ipv4|ipv6];\\n$conf = [normal|broken];\\n $key_args = {mode $mode} {conf $conf};\\ncmd $key_args')
    [Command(cmd:15):([Node(cmd)]:[Param?K(mode)(mode_param:Enum(mode:ipv4|ipv6)), Param?K(conf)(conf_param:Enum(conf:normal|broken))])]
    >>> parse_into_cli('$it = [a|b|c]; $x = use $it; $x')
    [Command(:15):([]:[ParamK(use)(it_param:Enum(it:a|b|c))])]
    >>> parse_into_cli('$state_enum=[enable|disable]; config dhcpv6_server ipif <address IpV6address> state $state_enum')
    [Command(config_dhcpv6_server_ipif_state:15):([Node(config), Node(dhcpv6_server), Node(ipif), Param(address:Type(IpV6address)), Node(state)]:[Param(state_enum_param:Enum(state_enum:enable|disable))])]
    '''
    program,errors = parse(s)

    for error in errors:
        print error

    if program is None:
        return []

    return CLIVisitor().visit(program)

def parse(s, mode=None, verbose=False, env=None, definitions=None):
    '''
    >>> parse('test\\n[a|b|c]\\nd|e')
    (None, ["Line 3 column 2 -> syntax error at '|'"])
    >>> parse('command test !')
    ({} <-> 'command ! test !', ["Warning: Line 1 column 14: illegal character '!' skipped"])
    >>> parse('test {[a} b]')
    (None, ["Line 1 column 9 -> syntax error at '}'"])
    >>> parse('a b c [1')
    (None, ['Syntax error: not enough tokens to complete parsing'])
    >>> parse('$a  =   test     ;\\n\\n\\n   \\n\\n    123  $ ')
    (None, ["Line 6 column 11 -> syntax error at ' '"])
    >>> parse(' \\n \\n $a \\n = \\n extra \\n \\n ; \\n $$a whitespaces \\n \\n with error')
    (None, ["Line 8 column 3 -> syntax error at '$'"])
    >>> parse('   a   b  c ')
    ({} <-> 'a ! b ! c !', [])
    >>> parse('ping [domain {a|b}|ipv6 addr|ipv4 addr]')
    ({} <-> 'ping ! ['domain ! ?[a|b]'|'ipv6 ! addr'|'ipv4 ! addr']', [])
    >>> parse('[a|b|c] d {f|g|h}')
    ({} <-> '[a|b|c] ! d ! ?[f|g|h]', [])
    >>> parse('cmd [{[a] b} c]')
    ({} <-> 'cmd ! '?['a ! b'] ! c'', [])
    >>> parse('test {x} {y} -te-st-')
    ({} <-> 'test ! ?[x] ! ?[y] ! - te - st -', [])
    >>> parse('$var=a b c; $var')
    ({'var': 'a ! b ! c'%var} <-> '$var', [])
    >>> parse('  $mode = [ipv4|ipv6];\\n$conf = [normal|broken];\\n $key_args = {mode $mode} {conf $conf};\\ncmd $key_args')
    ({'mode': [ipv4|ipv6]%mode, 'conf': [normal|broken]%conf, 'key_args': '?['mode ! [ipv4|ipv6]%mode'] ! ?['conf ! [normal|broken]%conf']'%key_args} <-> 'cmd ! $key_args', [])
    >>> parse('single int 1 2 -3')
    ({} <-> 'single ! int ! 1 ! 2 ! - 3', [])
    >>> parse('$a $b',env={'a':['a','A'], 'b':['b','B']})
    ({'a': [a|A]%a, 'b': [b|B]%b} <-> '$a ! $b', [])
    >>> parse('$x = +$b; $a$x',env={'a':['a','A'], 'b':['b','B']})
    ({'a': [a|A]%a, 'x': '+ [b|B]%b'%x, 'b': [b|B]%b} <-> '$a $x', [])
    >>> parse('int range 1~2 4~3')
    ({} <-> 'int ! range ! Range(1~2) ! Range(3~4)', [])
    >>> parse('ip address 192.168.19.1~3 /[16|24]')
    ({} <-> 'ip ! address ! 192 . 168 . 19 . Range(1~3) ! / [16|24]', [])
    >>> parse('$mode = [ipv4|ipv6] ; (** mode definition **) \\n $conf = [normal|broken]; (* ///(* conf **))/\\\\)\\\\ definition **)\\n$key_args={mode $mode} {conf $conf}; (**** multi\\nline\\n comment  *****)\\ncmd $key_args')
    ({'mode': [ipv4|ipv6]%mode, 'conf': [normal|broken]%conf, 'key_args': '?['mode ! [ipv4|ipv6]%mode'] ! ?['conf ! [normal|broken]%conf']'%key_args} <-> 'cmd ! $key_args', [])
    >>> parse('ping server.[a|b][1|2]')
    ({} <-> 'ping ! server . [a|b] [1|2]', [])
    >>> parse('permit 00:11:22~23:33:44~45:55')
    ({} <-> 'permit ! 00 : 11 : Range(22~23) : 33 : Range(44~45) : 55', [])
    >>> parse('$it = [a|b|c]; $x = use $it; $x')
    ({'x': 'use ! [a|b|c]%it'%x, 'it': [a|b|c]%it} <-> '$x', [])
    >>> parse('$state_enum=[enable|disable]; config dhcpv6_server ipif [<address IpV6address> | all] state $state_enum')
    ({'state_enum': [enable|disable]%state_enum} <-> 'config ! dhcpv6_server ! ipif ! ['<address IpV6address> !'|'! all'] ! state ! $state_enum', [])
    '''
    program = None
    errors = []

    if env is not None:
        if definitions is None:
            definitions = Definitions()
        definitions.update(Definitions.from_string_options(env))

    lexer = Lexer(mode=mode,verbose=verbose)
    parser = Parser(definitions=definitions)

    try:
        program = parser.parse(s,lexer=lexer)
        #print program
    except SyntaxError as e:
        errors.append(str(e))

    errors = lexer.errors + errors

    return program,errors

class InputHandler(object):
    def __init__(self,mode=None,verbose=False,cli=False):
        self.mode = mode
        self.verbose = verbose
        self.cli = cli
        self.definitions = Definitions()
        self.current_context = CLIContext('EXEC')
        self.current_level = 15

        self.seen = defaultdict(list)
        self.options = {}

        self._commands = {
            'clear': self.clear,
            'show': self.show,
            'xml': self.xml,
            'set': self.set,
            'context': self.context,
            'level': self.level,
        }

    def clear(self,what=None,*args):
        if what == 'seen':
            self.seen = defaultdict(list)
        elif what == 'options':
            self.options = {}
        else:
            self.seen = defaultdict(list)
            self.options = {}

    def show(self,*args):
        print self.seen

    def xml(self,out_folder=None,*args):
        if out_folder is None:
            out_folder = 'out'

        def gather_commands(programs):
            return list(itertools.chain(*(CLIVisitor(level=level).visit(p) for p,level in programs)))

        generator = XMLGenerator(out_folder=out_folder,**self.options)
        generator.generate({
            context: gather_commands(self.seen[context])
            for context in self.seen
        })

        print 'XML generation completed'

    def set(self,*args):
        def update_option(key,value=None,*args):
            if value is None and key in self.options:
                del self.options[key]
                print 'Option %s removed' % (key,)
            else:
                self.options[key] = value
                print 'Option %s set to %s' % (key,value)

        [update_option(*arg.split('=')) for arg in args]

    def context(self,name,prompt=None,*args):
        self.current_context = CLIContext(name,prompt)
        print 'Current context changed to', self.current_context

    def level(self,level=None,*args):
        try:
            if level is None:
                self.current_level = 15
            else:
                self.current_level = int(level)
            print 'Level set to %s' % (self.current_level,)
        except ValueError:
            print 'Incorrect parameter[%s]' % (level,)

    def load_definitions(self, filename):
        print 'Loading definition from %s...' % (filename,)
        program, errors = parse(open(filename,'r').read())
        for error in errors:
            print error

        if program is None:
            print 'Loading failed'
            return

        self.definitions += program.definitions

    def handle_interactive_command(self, s):
        if s.startswith('!'):
            args = s[1:].split()
            if args[0] in self._commands:
                self._commands[args[0]](*args[1:])
            else:
                print 'Unknown command'
            return True

    def process_interactive_input(self, s):
        if self.handle_interactive_command(s):
            return

        program, errors = parse(s,mode=self.mode,
                                  verbose=self.verbose,
                                  definitions=self.definitions)
        for error in errors:
            print error

        if program is None:
            return

        self.seen[self.current_context].append((program,self.current_level))
        self.definitions = program.definitions

        for option in OptionsVisitor().visit(program):
            print option

        if self.cli:
            commands = CLIVisitor(self.current_level).visit(program)
            for command in commands:
                print command


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
                            help='Show conversion into CLI nodes')
    arg_parser.add_argument('-t','--test',action='store_true',
                            help='perform self-testing procedure')
    arg_parser.add_argument('-d','--definitions',type=str,
                            help='load definitions from a given file')
    args = arg_parser.parse_args()

    if args.test == True:
        import doctest
        doctest.run_docstring_examples(parse_into_options,globals())
        doctest.run_docstring_examples(parse_into_cli,globals())
        doctest.run_docstring_examples(parse,globals())
        print 'Tests completed'
        sys.exit(0)

    input_handler = InputHandler(mode=args.mode,
                                 verbose=args.verbose,
                                 cli=args.cli)

    specific_input = None
    if args.input == '-':
        specific_input = sys.stdin.read()
    elif args.input is not None:
        specific_input = open(args.input).read()

    if args.definitions is not None:
        input_handler.load_definitions(args.definitions)

    def interactive_lines_coroutine():
        prompt = yield
        try:
            while True:
                prompt = yield raw_input(prompt)
        except (EOFError,KeyboardInterrupt):
            pass

    def string_lines_coroutine(s):
        yield
        for line in s.splitlines():
            yield line

    def commands_iterator(lines_coroutine):
        try:
            lines_coroutine.send(None)
            while True:
                s = lines_coroutine.next()
                if not s:
                    continue
                while s[-1] == '\\':
                    s = s[:-1] + '\n' + lines_coroutine.next()
                yield s
        except StopIteration:
            pass

    if specific_input is not None:
        lines_coroutine = string_lines_coroutine(specific_input)
        for command in commands_iterator(lines_coroutine):
            input_handler.process_interactive_input(command)
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