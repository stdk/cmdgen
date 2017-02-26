from ..lexer import lexer
from .. import parse,SyntaxError

import sys
import pytest

lexer.debug = True

def parse_clear_errors(s,errors):
    del errors[:]
    return parse(s,errors)

def test_syntax_errors():
    errors = []

    assert parse_clear_errors('test\n{a|b|c}\nd|e',errors) == []
    assert errors == ["Line 3 column 2 -> syntax error at '|'"]

    assert parse_clear_errors('test {[a} b]',errors) == []
    assert errors == ["Line 1 column 9 -> syntax error at '}'"]

    assert parse_clear_errors('a b c [1',errors) == []
    assert errors == ["Syntax error: not enough tokens to complete parsing"]

    assert parse_clear_errors('$a  =   test     ;\n\n\n   \n\n    123  $ ',errors) == []
    assert errors == ["Line 6 column 11 -> syntax error at ' '"]


def test_lexical_errors():
    errors = []

    assert parse_clear_errors('command test !',errors) == ['command test']
    assert errors == ["Warning: Line 1 column 14: illegal character '!' skipped"]
    

def test_parsing():
    assert parse('a+b') == ['a+b']