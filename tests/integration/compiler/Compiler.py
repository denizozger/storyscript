# -*- coding: utf-8 -*-
from storyscript.compiler import Compiler


def test_compiler_expression_sum(parser):
    """
    Ensures that numbers are compiled correctly
    """
    tree = parser.parse('3 + 2')
    result = Compiler.compile(tree)
    args = [
        {'$OBJECT': 'expression', 'expression': 'sum', 'values': [3, 2]}
    ]
    assert result['tree']['1']['method'] == 'expression'
    assert result['tree']['1']['args'] == args


def test_compiler_expression_mutation(parser):
    """
    Ensures that mutation expressions are compiled correctly
    """
    tree = parser.parse("'hello' length")
    result = Compiler.compile(tree)
    args = [
        {'$OBJECT': 'string', 'string': 'hello'},
        {'$OBJECT': 'mutation', 'mutation': 'length', 'arguments': []}
    ]
    assert result['tree']['1']['method'] == 'expression'
    assert result['tree']['1']['args'] == args


def test_compiler_expression_path(parser):
    """
    Ensures that expressions with paths are compiled correctly.
    """
    tree = parser.parse('x = 3\nx + 2')
    result = Compiler.compile(tree)
    path = {'$OBJECT': 'path', 'paths': ['x']}
    assert result['tree']['2']['args'][0]['values'][0] == path


def test_compiler_if(parser):
    tree = parser.parse('if colour == "red"\n\tx = 0')
    result = Compiler.compile(tree)
    args = [
        {'$OBJECT': 'assertion', 'assertion': 'equals',
         'values': [{'$OBJECT': 'path', 'paths': ['colour']},
                    {'$OBJECT': 'string', 'string': 'red'}]}
    ]
    assert result['tree']['1']['method'] == 'if'
    assert result['tree']['1']['args'] == args
    assert result['tree']['1']['enter'] == '2'
    assert result['tree']['2']['parent'] == '1'


def test_compiler_if_inline_expression(parser):
    tree = parser.parse('if (random numbers)\n\tx = 0')
    result = Compiler.compile(tree)
    entry = result['entrypoint']
    name = result['tree'][entry]['name']
    assert result['tree']['1']['method'] == 'if'
    assert result['tree']['1']['args'] == [{'$OBJECT': 'path', 'paths': name}]


def test_compiler_if_elseif(parser):
    source = 'if colour == "red"\n\tx = 0\nelse if colour == "blue"\n\tx = 1'
    tree = parser.parse(source)
    result = Compiler.compile(tree)
    args = [
        {'$OBJECT': 'assertion', 'assertion': 'equals',
         'values': [{'$OBJECT': 'path', 'paths': ['colour']},
                    {'$OBJECT': 'string', 'string': 'blue'}]}]
    assert result['tree']['1']['exit'] == '3'
    assert result['tree']['3']['method'] == 'elif'
    assert result['tree']['3']['args'] == args
    assert result['tree']['4']['parent'] == '3'


def test_compiler_if_else(parser):
    source = 'if colour == "red"\n\tx = 0\nelse\n\tx = 1'
    tree = parser.parse(source)
    result = Compiler.compile(tree)
    assert result['tree']['1']['exit'] == '3'
    assert result['tree']['3']['method'] == 'else'
    assert result['tree']['4']['parent'] == '3'


def test_compiler_foreach(parser):
    tree = parser.parse('foreach items as item\n\tx = 0')
    result = Compiler.compile(tree)
    args = [{'$OBJECT': 'path', 'paths': ['items']}]
    assert result['tree']['1']['method'] == 'for'
    assert result['tree']['1']['output'] == ['item']
    assert result['tree']['1']['args'] == args
    assert result['tree']['1']['enter'] == '2'
    assert result['tree']['2']['parent'] == '1'


def test_compiler_foreach_key_value(parser):
    tree = parser.parse('foreach items as key, value\n\tx = 0')
    result = Compiler.compile(tree)
    assert result['tree']['1']['output'] == ['key', 'value']


def test_compiler_service(parser):
    """
    Ensures that services are compiled correctly
    """
    tree = parser.parse("alpine echo message:'hello'")
    result = Compiler.compile(tree)
    args = [
        {'$OBJECT': 'argument', 'name': 'message', 'argument':
         {'$OBJECT': 'string', 'string': 'hello'}}
    ]
    assert result['tree']['1']['method'] == 'execute'
    assert result['tree']['1']['service'] == 'alpine'
    assert result['tree']['1']['command'] == 'echo'
    assert result['tree']['1']['args'] == args


def test_compiler_service_indented_arguments(parser):
    """
    Ensures that services with indented arguments are compiled correctly
    """
    tree = parser.parse('alpine echo message:"hello"\n\tcolour:"red"')
    result = Compiler.compile(tree)
    args = [
        {'$OBJECT': 'argument', 'name': 'message', 'argument':
         {'$OBJECT': 'string', 'string': 'hello'}},
        {'$OBJECT': 'argument', 'name': 'colour', 'argument':
         {'string': 'red', '$OBJECT': 'string'}}
    ]
    assert result['tree']['1']['args'] == args


def test_compiler_service_streaming(parser):
    """
    Ensures that streaming services are compiled correctly
    """
    source = 'api stream as client\n\twhen client event as e\n\t\tx=0'
    tree = parser.parse(source)
    result = Compiler.compile(tree)
    assert result['tree']['1']['output'] == ['client']
    assert result['tree']['1']['enter'] == '2'
    assert result['tree']['2']['method'] == 'when'
    assert result['tree']['2']['output'] == ['e']
    assert result['tree']['2']['enter'] == '3'
    assert result['tree']['3']['method'] == 'set'


def test_compiler_service_inline_expression(parser):
    """
    Ensures that inline expressions in services are compiled correctly
    """
    source = 'alpine echo text:(random strings)'
    tree = parser.parse(source)
    result = Compiler.compile(tree)
    entry = result['entrypoint']
    name = result['tree'][entry]['name']
    assert result['tree'][entry]['method'] == 'execute'
    assert result['tree'][entry]['service'] == 'random'
    assert result['tree'][entry]['command'] == 'strings'
    assert result['tree'][entry]['next'] == '1'
    path = {'$OBJECT': 'path', 'paths': name}
    argument = {'$OBJECT': 'argument', 'name': 'text', 'argument': path}
    assert result['tree']['1']['args'] == [argument]


def test_compiler_inline_expression_access(parser):
    """
    Ensures that inline expressions followed a bracket accesso are compiled
    correctly.
    """
    tree = parser.parse('x = (random array)[0]')
    result = Compiler.compile(tree)
    entry = result['entrypoint']
    name = result['tree'][entry]['name'][0]
    args = [{'$OBJECT': 'path', 'paths': [name, '0']}]
    assert result['tree']['1']['args'] == args


def test_compiler_try(parser):
    source = 'try\n\tx=0'
    tree = parser.parse(source)
    result = Compiler.compile(tree)
    assert result['tree']['1']['method'] == 'try'
    assert result['tree']['1']['enter'] == '2'
    assert result['tree']['2']['parent'] == '1'


def test_compiler_try_catch(parser):
    source = 'try\n\tx=0\ncatch as error\n\tx=1'
    tree = parser.parse(source)
    result = Compiler.compile(tree)
    assert result['tree']['1']['exit'] == '3'
    assert result['tree']['3']['method'] == 'catch'
    assert result['tree']['3']['output'] == ['error']
    assert result['tree']['3']['enter'] == '4'
    assert result['tree']['4']['parent'] == '3'


def test_compiler_try_finally(parser):
    source = 'try\n\tx=0\nfinally\n\tx=1'
    tree = parser.parse(source)
    result = Compiler.compile(tree)
    assert result['tree']['3']['method'] == 'finally'
    assert result['tree']['3']['enter'] == '4'
    assert result['tree']['4']['parent'] == '3'