from .lexer import tokens
from .ast import *

def p_program(p):
    'program : definition_list node_sequence'
    p[0] = Program(p[1],p[2])

def p_program_short(p):
    'program : node_sequence'
    p[0] = Program(p.parser.definitions.copy(),p[1])

def p_program_definitions_only(p):
    'program : definition_list'
    p[0] = Program(p[1],None)

def p_definition_list_single(p):
    'definition_list : definition'
    p[0] = p.parser.definitions.copy()
    p[0].add_definition(p[1])

def p_definition_list(p):
    'definition_list : definition_list definition'
    p[1].add_definition(p[2])
    p[0] = p[1]

def p_definition(p):
    'definition : "$" ID ASSIGN node_sequence SEMICOLON'
    p[0] = Definition(p[2],p[4])

def p_node_sequence_single(p):
    'node_sequence : node'
    p[0] = Sequence([p[1]])

def p_node_sequence_normal(p):
    'node_sequence : node_sequence node'
    p[0] = p[1].append(p[2])

def p_node_writespace(p):
    'node : WHITESPACE'
    p[0] = Delimiter(' ')

def p_node_minus(p):
    'node : "-"'
    p[0] = Primitive('-')

def p_node_id(p):
    'node : ID'
    p[0] = Primitive(p[1])

def p_node_node(p):
    'node : NODE'
    p[0] = Primitive(p[1])

def p_node_number(p):
    'node : NUMBER'
    p[0] = Primitive(p[1])

def p_node_range(p):
    'node : NUMBER "~" NUMBER'
    p[0] = Range(p[1],p[3])

def p_node_variable(p):
    'node : "$" ID'
    p[0] = Variable(p[2])

def p_node_parameter_single_id(p):
    'node : "<" ID ">"'
    p[0] = Parameter(p[2])

def p_node_parameter_typed_id(p):
    'node : "<" ID ID ">"'
    p[0] = Parameter(p[2],p[3])

def p_node_parameter_string(p):
    'node : "<" ID NUMBER ">"'
    p[0] = StringParameter(p[2],p[3])

def p_node_parameter_int(p):
    'node : "<" ID NUMBER "-" NUMBER ">"'
    p[0] = IntParameter(p[2],p[3],p[5])

def p_node_optional_group(p):
    'node : OPTIONAL_BRACE_BEGIN node_options OPTIONAL_BRACE_END'
    p[2].optional = True
    p[0] = p[2].simplify()    

def p_node_optional_group_with_required_count(p):
    'node : OPTIONAL_BRACE_BEGIN node_options OPTIONAL_BRACE_END "(" NUMBER ")"'
    min_options = int(p[5])
    p[0] = p[2].convert_to_min_req_options(min_options).simplify()

def p_node_mandatory_group(p):
    'node : MANDATORY_BRACE_BEGIN node_options MANDATORY_BRACE_END'
    p[0] = p[2].simplify()

def p_node_options_single(p):
    'node_options : node_sequence'
    p[0] = Options()
    p[0].append(p[1])

def p_node_options(p):
    'node_options : node_options "|" node_sequence'
    p[0] = p[1]
    p[0].append(p[3])

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

class Parser(object):
    def __init__(self,definitions=None):
        if definitions is None:
            definitions = Definitions()
        self.parser = yacc.yacc()
        self.parser.definitions = definitions

    def parse(self,*args,**kwargs):
        return self.parser.parse(*args,**kwargs)
