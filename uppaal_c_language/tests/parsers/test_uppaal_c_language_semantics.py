import pprint

import pytest

from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import (
    ast_rotate_left, ast_rotate_left_while_assoc_prec,
    ast_rotate_right
)

pp = pprint.PrettyPrinter(indent=4, compact=True)
printExpectedResults = False
printActualResults = False


@pytest.fixture
def base_binary_ast_right():
    return {
        'astType': 'BinaryExpr',
        'left': {'astType': 'Integer', 'val': 1},
        'op': 'Mult',
        'right': {
            'astType': 'BinaryExpr',
            'left': {
                'astType': 'BinaryExpr',
                'left': {'astType': 'Integer', 'val': 1},
                'op': 'Add',
                'right': {'astType': 'Integer', 'val': 2}
            },
            'op': 'Mult',
            'right': {
                'astType': 'BinaryExpr',
                'left': {'astType': 'Integer', 'val': 3},
                'op': 'Add',
                'right': {'astType': 'Integer', 'val': 4}
            },
        },
    }


@pytest.fixture
def base_binary_ast_left():
    return {
        'astType': 'BinaryExpr',
        'left': {
            'astType': 'BinaryExpr',
            'left': {
                'astType': 'BinaryExpr',
                'left': {'astType': 'Integer', 'val': 1},
                'op': 'Add',
                'right': {'astType': 'Integer', 'val': 2}
            },
            'op': 'Mult',
            'right': {
                'astType': 'BinaryExpr',
                'left': {'astType': 'Integer', 'val': 3},
                'op': 'Add',
                'right': {'astType': 'Integer', 'val': 4}
            },
        },
        'op': 'Mult',
        'right': {'astType': 'Integer', 'val': 1},
    }


@pytest.fixture
def base_unary_ast():
    return {
        'astType': 'UnaryExpr',
        'expr': {
            'astType': 'BinaryExpr',
            'left': {
                'astType': 'BinaryExpr',
                'left': {'astType': 'Integer', 'val': 1},
                'op': 'Add',
                'right': {'astType': 'Integer', 'val': 2}
            },
            'op': 'Mult',
            'right': {
                'astType': 'BinaryExpr',
                'left': {'astType': 'Integer', 'val': 3},
                'op': 'Add',
                'right': {'astType': 'Integer', 'val': 4}
            },
        },
        'op': 'Neg',
    }


def test_binary_ast_rotate_left(base_binary_ast_right):
    res_ast = ast_rotate_left(base_binary_ast_right)
    expected_ast = {
        'astType': 'BinaryExpr',
        'left': {'astType': 'BinaryExpr',
                 'left': {'astType': 'Integer', 'val': 1},
                 'op': 'Mult',
                 'right': {'astType': 'BinaryExpr',
                           'left': {'astType': 'Integer', 'val': 1},
                           'op': 'Add',
                           'right': {'astType': 'Integer', 'val': 2}}},
        'op': 'Mult',
        'right': {'astType': 'BinaryExpr',
                  'left': {'astType': 'Integer', 'val': 3},
                  'op': 'Add',
                  'right': {'astType': 'Integer', 'val': 4}}}
    assert res_ast == expected_ast


def test_binary_ast_rotate_left_while_assoc_prec(base_binary_ast_right):
    res_ast = ast_rotate_left_while_assoc_prec(base_binary_ast_right)
    expected_ast = {
        'astType': 'BinaryExpr',
        'left': {'astType': 'BinaryExpr',
                 'left': {'astType': 'BinaryExpr',
                          'left': {'astType': 'Integer', 'val': 1},
                          'op': 'Mult',
                          'right': {'astType': 'Integer', 'val': 1}},
                 'op': 'Add',
                 'right': {'astType': 'Integer', 'val': 2}},
        'op': 'Mult',
        'right': {'astType': 'BinaryExpr',
                  'left': {'astType': 'Integer', 'val': 3},
                  'op': 'Add',
                  'right': {'astType': 'Integer', 'val': 4}}}
    assert res_ast == expected_ast


def test_binary_ast_rotate_right(base_binary_ast_left):
    res_ast = ast_rotate_right(base_binary_ast_left)
    expected_ast = {
        'astType': 'BinaryExpr',
        'left': {'astType': 'BinaryExpr',
                 'left': {'astType': 'Integer', 'val': 1},
                 'op': 'Add',
                 'right': {'astType': 'Integer', 'val': 2}},
        'op': 'Mult',
        'right': {'astType': 'BinaryExpr',
                  'left': {'astType': 'BinaryExpr',
                           'left': {'astType': 'Integer', 'val': 3},
                           'op': 'Add',
                           'right': {'astType': 'Integer', 'val': 4}},
                  'op': 'Mult',
                  'right': {'astType': 'Integer', 'val': 1}}}
    assert res_ast == expected_ast


def test_unary_ast_rotate_left(base_unary_ast):
    res_ast = ast_rotate_left(base_unary_ast)
    expected_ast = {
        'astType': 'BinaryExpr',
        'left': {'astType': 'UnaryExpr',
                 'expr': {'astType': 'BinaryExpr',
                          'left': {'astType': 'Integer', 'val': 1},
                          'op': 'Add',
                          'right': {'astType': 'Integer', 'val': 2}},
                 'op': 'Neg'},
        'op': 'Mult',
        'right': {'astType': 'BinaryExpr',
                  'left': {'astType': 'Integer', 'val': 3},
                  'op': 'Add',
                  'right': {'astType': 'Integer', 'val': 4}}}
    assert res_ast == expected_ast


def test_unary_ast_rotate_left_while_assoc_prec(base_unary_ast):
    res_ast = ast_rotate_left_while_assoc_prec(base_unary_ast)
    expected_ast = {
        'astType': 'BinaryExpr',
        'left': {'astType': 'BinaryExpr',
                 'left': {'astType': 'UnaryExpr',
                          'expr': {'astType': 'Integer', 'val': 1},
                          'op': 'Neg'},
                 'op': 'Add',
                 'right': {'astType': 'Integer', 'val': 2}},
        'op': 'Mult',
        'right': {'astType': 'BinaryExpr',
                  'left': {'astType': 'Integer', 'val': 3},
                  'op': 'Add',
                  'right': {'astType': 'Integer', 'val': 4}}}
    assert res_ast == expected_ast


def test_unary_ast_rotate_right(base_unary_ast):
    res_ast = ast_rotate_right(base_unary_ast)
    expected_ast = {
        'astType': 'BinaryExpr',
        'left': {'astType': 'BinaryExpr',
                 'left': {'astType': 'Integer', 'val': 1},
                 'op': 'Add',
                 'right': {'astType': 'Integer', 'val': 2}},
        'op': 'Mult',
        'right': {'astType': 'UnaryExpr',
                  'expr': {'astType': 'BinaryExpr',
                           'left': {'astType': 'Integer', 'val': 3},
                           'op': 'Add',
                           'right': {'astType': 'Integer', 'val': 4}},
                  'op': 'Neg'}}
    assert res_ast == expected_ast
