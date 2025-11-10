"""
抽象语法树（AST）定义
定义命题逻辑公式的数据结构
"""

from dataclasses import dataclass
from typing import Union


class Sentence:
    """所有逻辑公式的基类"""
    pass


@dataclass(frozen=True)
class Var(Sentence):
    """命题变量，如 P, Q, R"""
    name: str
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"Var({self.name})"


@dataclass(frozen=True)
class Not(Sentence):
    """否定，如 ~P"""
    operand: Sentence
    
    def __str__(self):
        return f"~{self.operand}"
    
    def __repr__(self):
        return f"Not({self.operand})"


@dataclass(frozen=True)
class And(Sentence):
    """合取，如 P & Q"""
    left: Sentence
    right: Sentence
    
    def __str__(self):
        return f"({self.left} & {self.right})"
    
    def __repr__(self):
        return f"And({self.left}, {self.right})"


@dataclass(frozen=True)
class Or(Sentence):
    """析取，如 P | Q"""
    left: Sentence
    right: Sentence
    
    def __str__(self):
        return f"({self.left} | {self.right})"
    
    def __repr__(self):
        return f"Or({self.left}, {self.right})"


@dataclass(frozen=True)
class Imply(Sentence):
    """蕴涵，如 P -> Q"""
    left: Sentence
    right: Sentence
    
    def __str__(self):
        return f"({self.left} -> {self.right})"
    
    def __repr__(self):
        return f"Imply({self.left}, {self.right})"


# 类型别名
Expr = Union[Var, Not, And, Or, Imply]


def get_all_vars(expr: Expr) -> set[str]:
    """
    提取公式中的所有命题变量
    
    Args:
        expr: 逻辑公式
        
    Returns:
        所有变量名的集合
    """
    if isinstance(expr, Var):
        return {expr.name}
    elif isinstance(expr, Not):
        return get_all_vars(expr.operand)
    elif isinstance(expr, (And, Or, Imply)):
        return get_all_vars(expr.left) | get_all_vars(expr.right)
    else:
        return set()


def formula_complexity(expr: Expr) -> int:
    """
    计算公式的复杂度（节点数）
    
    Args:
        expr: 逻辑公式
        
    Returns:
        公式的节点总数
    """
    if isinstance(expr, Var):
        return 1
    elif isinstance(expr, Not):
        return 1 + formula_complexity(expr.operand)
    elif isinstance(expr, (And, Or, Imply)):
        return 1 + formula_complexity(expr.left) + formula_complexity(expr.right)
    else:
        return 0

