import sys
import os

# 使项目根目录可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qubo_prover_v3.core.parser import parse
from qubo_prover_v3.core.ast import Var, Not, And, Or, Imply


def test_parse_basic_vars():
    expr = parse("P")
    assert isinstance(expr, Var)
    assert expr.name == "P"


def test_parse_unary_not():
    expr = parse("~P")
    assert isinstance(expr, Not)
    assert isinstance(expr.operand, Var)
    assert expr.operand.name == "P"


def test_parse_and_or_precedence():
    expr = parse("P&Q|R")
    assert isinstance(expr, Or)
    assert isinstance(expr.left, And)
    assert isinstance(expr.left.left, Var) and expr.left.left.name == "P"
    assert isinstance(expr.left.right, Var) and expr.left.right.name == "Q"
    assert isinstance(expr.right, Var) and expr.right.name == "R"


def test_parse_nested_parens():
    expr = parse("~(P&(Q|R))")
    assert isinstance(expr, Not)
    inner = expr.operand
    assert isinstance(inner, And)
    assert isinstance(inner.left, Var) and inner.left.name == "P"
    assert isinstance(inner.right, Or)
    assert isinstance(inner.right.left, Var) and inner.right.left.name == "Q"
    assert isinstance(inner.right.right, Var) and inner.right.right.name == "R"


def test_parse_chain_implication():
    expr = parse("P->Q->R")
    assert isinstance(expr, Imply)
    assert isinstance(expr.left, Var) and expr.left.name == "P"
    assert isinstance(expr.right, Imply)
    assert isinstance(expr.right.left, Var) and expr.right.left.name == "Q"
    assert isinstance(expr.right.right, Var) and expr.right.right.name == "R"


def test_parse_error_missing_paren():
    try:
        parse("(P&Q")
        assert False
    except ValueError as e:
        assert "Missing closing parenthesis" in str(e)

