"""
抽象语法树（AST）定义

定义命题逻辑公式的数据结构，支持：
- 命题变量 (Var)
- 否定 (Not)
- 合取 (And)
- 析取 (Or)
- 蕴涵 (Imply)
- 双条件/等价 (Iff)

增强功能：
- 公式规范化
- 结构相等性
- 哈希支持（用于集合和字典）
- 子公式遍历
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Set, Iterator, Union, FrozenSet
from abc import ABC, abstractmethod


class Expr(ABC):
    """所有逻辑公式的抽象基类"""
    
    @abstractmethod
    def __str__(self) -> str:
        """返回公式的字符串表示"""
        pass
    
    @abstractmethod
    def __hash__(self) -> int:
        """返回公式的哈希值"""
        pass
    
    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """判断公式是否相等"""
        pass
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    
    @abstractmethod
    def subformulas(self) -> Iterator[Expr]:
        """迭代所有子公式（包括自身）"""
        pass
    
    @abstractmethod
    def substitute(self, mapping: dict[str, Expr]) -> Expr:
        """变量替换"""
        pass


@dataclass(frozen=True, eq=False)
class Var(Expr):
    """
    命题变量
    
    例如: P, Q, R, Premise1
    """
    name: str
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f"Var({self.name!r})"
    
    def __hash__(self) -> int:
        return hash(("Var", self.name))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Var):
            return self.name == other.name
        return False
    
    def subformulas(self) -> Iterator[Expr]:
        yield self
    
    def substitute(self, mapping: dict[str, Expr]) -> Expr:
        return mapping.get(self.name, self)


@dataclass(frozen=True, eq=False)
class Not(Expr):
    """
    否定
    
    例如: ~P, ¬Q
    """
    operand: Expr
    
    def __str__(self) -> str:
        if isinstance(self.operand, Var):
            return f"~{self.operand}"
        return f"~({self.operand})"
    
    def __repr__(self) -> str:
        return f"Not({self.operand!r})"
    
    def __hash__(self) -> int:
        return hash(("Not", hash(self.operand)))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Not):
            return self.operand == other.operand
        return False
    
    def subformulas(self) -> Iterator[Expr]:
        yield self
        yield from self.operand.subformulas()
    
    def substitute(self, mapping: dict[str, Expr]) -> Expr:
        return Not(self.operand.substitute(mapping))


@dataclass(frozen=True, eq=False)
class And(Expr):
    """
    合取（与）
    
    例如: P & Q, P ∧ Q
    """
    left: Expr
    right: Expr
    
    def __str__(self) -> str:
        left_str = str(self.left) if isinstance(self.left, (Var, Not)) else f"({self.left})"
        right_str = str(self.right) if isinstance(self.right, (Var, Not)) else f"({self.right})"
        return f"{left_str} & {right_str}"
    
    def __repr__(self) -> str:
        return f"And({self.left!r}, {self.right!r})"
    
    def __hash__(self) -> int:
        # 合取满足交换律，使用 frozenset 保证 A&B == B&A
        return hash(("And", frozenset([hash(self.left), hash(self.right)])))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, And):
            # 考虑交换律
            return (self.left == other.left and self.right == other.right) or \
                   (self.left == other.right and self.right == other.left)
        return False
    
    def subformulas(self) -> Iterator[Expr]:
        yield self
        yield from self.left.subformulas()
        yield from self.right.subformulas()
    
    def substitute(self, mapping: dict[str, Expr]) -> Expr:
        return And(self.left.substitute(mapping), self.right.substitute(mapping))
    
    @staticmethod
    def of(*args: Expr) -> Expr:
        """创建多元合取"""
        if len(args) == 0:
            raise ValueError("And.of requires at least one argument")
        if len(args) == 1:
            return args[0]
        result = args[0]
        for arg in args[1:]:
            result = And(result, arg)
        return result


@dataclass(frozen=True, eq=False)
class Or(Expr):
    """
    析取（或）
    
    例如: P | Q, P ∨ Q
    """
    left: Expr
    right: Expr
    
    def __str__(self) -> str:
        left_str = str(self.left) if isinstance(self.left, (Var, Not, And)) else f"({self.left})"
        right_str = str(self.right) if isinstance(self.right, (Var, Not, And)) else f"({self.right})"
        return f"{left_str} | {right_str}"
    
    def __repr__(self) -> str:
        return f"Or({self.left!r}, {self.right!r})"
    
    def __hash__(self) -> int:
        # 析取满足交换律
        return hash(("Or", frozenset([hash(self.left), hash(self.right)])))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Or):
            return (self.left == other.left and self.right == other.right) or \
                   (self.left == other.right and self.right == other.left)
        return False
    
    def subformulas(self) -> Iterator[Expr]:
        yield self
        yield from self.left.subformulas()
        yield from self.right.subformulas()
    
    def substitute(self, mapping: dict[str, Expr]) -> Expr:
        return Or(self.left.substitute(mapping), self.right.substitute(mapping))
    
    @staticmethod
    def of(*args: Expr) -> Expr:
        """创建多元析取"""
        if len(args) == 0:
            raise ValueError("Or.of requires at least one argument")
        if len(args) == 1:
            return args[0]
        result = args[0]
        for arg in args[1:]:
            result = Or(result, arg)
        return result


@dataclass(frozen=True, eq=False)
class Imply(Expr):
    """
    蕴涵（如果...那么...）
    
    例如: P -> Q
    """
    left: Expr   # 前件
    right: Expr  # 后件
    
    def __str__(self) -> str:
        left_str = str(self.left) if isinstance(self.left, (Var, Not)) else f"({self.left})"
        right_str = str(self.right) if isinstance(self.right, (Var, Not)) else f"({self.right})"
        return f"{left_str} -> {right_str}"
    
    def __repr__(self) -> str:
        return f"Imply({self.left!r}, {self.right!r})"
    
    def __hash__(self) -> int:
        return hash(("Imply", hash(self.left), hash(self.right)))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Imply):
            return self.left == other.left and self.right == other.right
        return False
    
    def subformulas(self) -> Iterator[Expr]:
        yield self
        yield from self.left.subformulas()
        yield from self.right.subformulas()
    
    def substitute(self, mapping: dict[str, Expr]) -> Expr:
        return Imply(self.left.substitute(mapping), self.right.substitute(mapping))


@dataclass(frozen=True, eq=False)
class Iff(Expr):
    """
    双条件/等价（当且仅当）
    
    例如: P <-> Q
    """
    left: Expr
    right: Expr
    
    def __str__(self) -> str:
        left_str = str(self.left) if isinstance(self.left, (Var, Not)) else f"({self.left})"
        right_str = str(self.right) if isinstance(self.right, (Var, Not)) else f"({self.right})"
        return f"{left_str} <-> {right_str}"
    
    def __repr__(self) -> str:
        return f"Iff({self.left!r}, {self.right!r})"
    
    def __hash__(self) -> int:
        # 等价满足交换律
        return hash(("Iff", frozenset([hash(self.left), hash(self.right)])))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Iff):
            return (self.left == other.left and self.right == other.right) or \
                   (self.left == other.right and self.right == other.left)
        return False
    
    def subformulas(self) -> Iterator[Expr]:
        yield self
        yield from self.left.subformulas()
        yield from self.right.subformulas()
    
    def substitute(self, mapping: dict[str, Expr]) -> Expr:
        return Iff(self.left.substitute(mapping), self.right.substitute(mapping))


# ============================================================
# 辅助函数
# ============================================================

def get_vars(expr: Expr) -> Set[str]:
    """
    提取公式中的所有命题变量名
    
    Args:
        expr: 逻辑公式
        
    Returns:
        变量名集合
    """
    result: Set[str] = set()
    for sub in expr.subformulas():
        if isinstance(sub, Var):
            result.add(sub.name)
    return result


def depth(expr: Expr) -> int:
    """
    计算公式的嵌套深度
    
    Args:
        expr: 逻辑公式
        
    Returns:
        嵌套深度（变量深度为0）
    """
    if isinstance(expr, Var):
        return 0
    elif isinstance(expr, Not):
        return 1 + depth(expr.operand)
    elif isinstance(expr, (And, Or, Imply, Iff)):
        return 1 + max(depth(expr.left), depth(expr.right))
    return 0


def size(expr: Expr) -> int:
    """
    计算公式的大小（节点数）
    
    Args:
        expr: 逻辑公式
        
    Returns:
        AST 节点总数
    """
    if isinstance(expr, Var):
        return 1
    elif isinstance(expr, Not):
        return 1 + size(expr.operand)
    elif isinstance(expr, (And, Or, Imply, Iff)):
        return 1 + size(expr.left) + size(expr.right)
    return 0


def negate(expr: Expr) -> Expr:
    """
    对公式取否定（简化双重否定）
    
    Args:
        expr: 逻辑公式
        
    Returns:
        否定后的公式
    """
    if isinstance(expr, Not):
        return expr.operand  # ~~P -> P
    return Not(expr)


def is_literal(expr: Expr) -> bool:
    """
    判断是否为文字（变量或否定变量）
    
    Args:
        expr: 逻辑公式
        
    Returns:
        是否为文字
    """
    if isinstance(expr, Var):
        return True
    if isinstance(expr, Not) and isinstance(expr.operand, Var):
        return True
    return False


def get_literal_var(expr: Expr) -> str | None:
    """
    获取文字中的变量名
    
    Args:
        expr: 逻辑公式（应为文字）
        
    Returns:
        变量名，如果不是文字则返回 None
    """
    if isinstance(expr, Var):
        return expr.name
    if isinstance(expr, Not) and isinstance(expr.operand, Var):
        return expr.operand.name
    return None


def is_positive_literal(expr: Expr) -> bool:
    """判断是否为正文字"""
    return isinstance(expr, Var)


def is_negative_literal(expr: Expr) -> bool:
    """判断是否为负文字"""
    return isinstance(expr, Not) and isinstance(expr.operand, Var)

