"""
逻辑表示层

提供命题逻辑公式的表示、解析、转换和求值功能。
"""

from .ast import Var, Not, And, Or, Imply, Iff, Expr, get_vars, depth, size
from .parser import parse
from .cnf import to_cnf, to_nnf, Clause, CNF
from .evaluator import evaluate, is_tautology, is_satisfiable, find_model

__all__ = [
    # AST
    "Var", "Not", "And", "Or", "Imply", "Iff", "Expr",
    "get_vars", "depth", "size",
    # Parser
    "parse",
    # CNF
    "to_cnf", "to_nnf", "Clause", "CNF",
    # Evaluator
    "evaluate", "is_tautology", "is_satisfiable", "find_model",
]

