from .lexer import tokens
from .ast import *

def p_program(p):
    'program : definition_list command'
    p[0] = Program(p[1],p[2])

def p_program_short(p):
    'program : command'
    p[0] = Program(DefinitionList(),p[1])
    
def p_program_definitions_only(p):
    'program : definition_list'
    p[0] = Program(p[1],None)

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

def p_node_sequence_normal(p):
    'node_sequence : node_sequence node'
    p[0] = p[1].append(p[2])

def p_node_writespace(p):
    'node : WHITESPACE'
    p[0] = Delimiter(' ')

def p_node_minus(p):
    'node : "-"'
    p[0] = PrimitiveNode('-')

def p_node_id(p):
    'node : ID'    
    p[0] = PrimitiveNode(p[1])

def p_node_node(p):
    'node : NODE'
    p[0] = PrimitiveNode(p[1])

def p_node_number(p):
    'node : NUMBER'    
    p[0] = PrimitiveNode(p[1])

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
    if len(p[2]) > 1:
        contents = p[2]
    else:
        contents = p[2].contents[0]
    p[0] = Node(contents,optional=True)

def p_node_optional_group_with_required_count(p):
    'node : OPTIONAL_BRACE_BEGIN node_options OPTIONAL_BRACE_END "(" NUMBER ")"'
    min_options = int(p[5])
    available = len(p[2])
    if available < min_options:
        print 'Warning: requested min number of params[%d] is greater than available number [%d]' % (min_options,available)
        min_options = available
    
    if available > 1:
        p[0] = p[2]
        p[0].min_options = min_options
    else:
        p[0] = p[2].contents[0]
    
def p_node_mandatory_group(p):
    'node : MANDATORY_BRACE_BEGIN node_options MANDATORY_BRACE_END'
    if len(p[2]) > 1:
        p[0] = p[2]
    else:
        p[0] = p[2].contents[0]

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