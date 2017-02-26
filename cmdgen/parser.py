from .cmd_lexer import tokens
from .ast import *

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

def p_node_sequence_normal(p):
    'node_sequence : node_sequence node'
    p[0] = p[1].append(p[2])

def p_node_writespace(p):
    'node : WHITESPACE'
    p[0] = Node(' ',primitive=True)

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