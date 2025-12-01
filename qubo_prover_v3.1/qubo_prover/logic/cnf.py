"""
合取范式（CNF）转换

实现将任意命题逻辑公式转换为合取范式，这是实现完备性证明的基础。

CNF 形式: (l11 ∨ l12 ∨ ...) ∧ (l21 ∨ l22 ∨ ...) ∧ ...
其中每个 lij 是文字（变量或其否定）

转换步骤：
1. 消除等价：P <-> Q  =>  (P -> Q) & (Q -> P)
2. 消除蕴涵：P -> Q   =>  ~P | Q
3. 推入否定（NNF）：~(P & Q) => ~P | ~Q, ~(P | Q) => ~P & ~Q
4. 分配律：P | (Q & R) => (P | Q) & (P | R)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import FrozenSet, Set, Iterator, List, Tuple
from .ast import Expr, Var, Not, And, Or, Imply, Iff, is_literal, get_literal_var


@dataclass(frozen=True)
class Literal:
    """
    文字：变量或其否定
    """
    var: str
    positive: bool  # True = 正文字, False = 负文字
    
    def __str__(self) -> str:
        return self.var if self.positive else f"~{self.var}"
    
    def __repr__(self) -> str:
        return f"Literal({self.var!r}, {self.positive})"
    
    def __neg__(self) -> Literal:
        """取否定"""
        return Literal(self.var, not self.positive)
    
    def to_expr(self) -> Expr:
        """转换为 AST 表达式"""
        v = Var(self.var)
        return v if self.positive else Not(v)


@dataclass(frozen=True)
class Clause:
    """
    子句：文字的析取
    
    空子句表示矛盾（False）
    """
    literals: FrozenSet[Literal]
    
    def __str__(self) -> str:
        if not self.literals:
            return "⊥"  # 空子句 = False
        return " | ".join(str(lit) for lit in sorted(self.literals, key=lambda l: (l.var, not l.positive)))
    
    def __repr__(self) -> str:
        return f"Clause({{{', '.join(repr(l) for l in self.literals)}}})"
    
    def __iter__(self) -> Iterator[Literal]:
        return iter(self.literals)
    
    def __len__(self) -> int:
        return len(self.literals)
    
    def __bool__(self) -> bool:
        """非空子句为真"""
        return bool(self.literals)
    
    def is_empty(self) -> bool:
        """是否为空子句（矛盾）"""
        return len(self.literals) == 0
    
    def is_unit(self) -> bool:
        """是否为单元子句"""
        return len(self.literals) == 1
    
    def is_tautology(self) -> bool:
        """是否为永真子句（包含 P 和 ~P）"""
        vars_pos = {lit.var for lit in self.literals if lit.positive}
        vars_neg = {lit.var for lit in self.literals if not lit.positive}
        return bool(vars_pos & vars_neg)
    
    def get_unit_literal(self) -> Literal | None:
        """获取单元子句的文字"""
        if self.is_unit():
            return next(iter(self.literals))
        return None
    
    def remove(self, lit: Literal) -> Clause:
        """移除指定文字"""
        return Clause(self.literals - {lit})
    
    def contains(self, lit: Literal) -> bool:
        """是否包含指定文字"""
        return lit in self.literals
    
    def contains_var(self, var: str) -> bool:
        """是否包含指定变量（正或负）"""
        return any(l.var == var for l in self.literals)
    
    def get_vars(self) -> Set[str]:
        """获取子句中的所有变量"""
        return {l.var for l in self.literals}
    
    def to_expr(self) -> Expr:
        """转换为 AST 表达式"""
        if not self.literals:
            # 空子句 -> False（但我们用 P & ~P 表示）
            return And(Var("_FALSE_"), Not(Var("_FALSE_")))
        
        exprs = [lit.to_expr() for lit in self.literals]
        result = exprs[0]
        for e in exprs[1:]:
            result = Or(result, e)
        return result
    
    @staticmethod
    def from_literals(*lits: Literal) -> Clause:
        """从文字创建子句"""
        return Clause(frozenset(lits))
    
    @staticmethod
    def from_strings(*specs: str) -> Clause:
        """
        从字符串创建子句
        
        Args:
            specs: 文字字符串，如 "P", "~Q"
        """
        literals: Set[Literal] = set()
        for s in specs:
            s = s.strip()
            if s.startswith("~"):
                literals.add(Literal(s[1:], False))
            else:
                literals.add(Literal(s, True))
        return Clause(frozenset(literals))


@dataclass
class CNF:
    """
    合取范式：子句的集合（合取）
    
    空集合表示永真（True）
    """
    clauses: Set[Clause]
    
    def __str__(self) -> str:
        if not self.clauses:
            return "⊤"  # 空CNF = True
        return " ∧ ".join(f"({c})" for c in sorted(self.clauses, key=str))
    
    def __repr__(self) -> str:
        return f"CNF({self.clauses!r})"
    
    def __iter__(self) -> Iterator[Clause]:
        return iter(self.clauses)
    
    def __len__(self) -> int:
        return len(self.clauses)
    
    def __bool__(self) -> bool:
        """非空 CNF 为真"""
        return True
    
    def is_empty(self) -> bool:
        """是否为空（永真）"""
        return len(self.clauses) == 0
    
    def has_empty_clause(self) -> bool:
        """是否包含空子句（矛盾）"""
        return any(c.is_empty() for c in self.clauses)
    
    def add(self, clause: Clause) -> CNF:
        """添加子句"""
        # 跳过永真子句
        if clause.is_tautology():
            return self
        return CNF(self.clauses | {clause})
    
    def union(self, other: CNF) -> CNF:
        """合并两个 CNF"""
        result = CNF(self.clauses.copy())
        for c in other.clauses:
            if not c.is_tautology():
                result.clauses.add(c)
        return result
    
    def get_vars(self) -> Set[str]:
        """获取所有变量"""
        result: Set[str] = set()
        for c in self.clauses:
            result |= c.get_vars()
        return result
    
    def get_unit_clauses(self) -> List[Clause]:
        """获取所有单元子句"""
        return [c for c in self.clauses if c.is_unit()]
    
    def to_expr(self) -> Expr:
        """转换为 AST 表达式"""
        if not self.clauses:
            # 空 CNF -> True（用 P | ~P 表示）
            return Or(Var("_TRUE_"), Not(Var("_TRUE_")))
        
        exprs = [c.to_expr() for c in self.clauses]
        result = exprs[0]
        for e in exprs[1:]:
            result = And(result, e)
        return result
    
    @staticmethod
    def from_clauses(*clauses: Clause) -> CNF:
        """从子句列表创建 CNF"""
        result: Set[Clause] = set()
        for c in clauses:
            if not c.is_tautology():
                result.add(c)
        return CNF(result)


# ============================================================
# 转换函数
# ============================================================

def to_nnf(expr: Expr) -> Expr:
    """
    转换为否定范式（Negation Normal Form）
    
    NNF 中否定只出现在变量前面。
    
    Args:
        expr: 逻辑公式
        
    Returns:
        等价的 NNF 公式
    """
    # 1. 消除等价和蕴涵
    expr = _eliminate_iff_imply(expr)
    
    # 2. 推入否定
    return _push_negation(expr)


def _eliminate_iff_imply(expr: Expr) -> Expr:
    """消除等价和蕴涵"""
    if isinstance(expr, Var):
        return expr
    
    if isinstance(expr, Not):
        return Not(_eliminate_iff_imply(expr.operand))
    
    if isinstance(expr, And):
        return And(_eliminate_iff_imply(expr.left), _eliminate_iff_imply(expr.right))
    
    if isinstance(expr, Or):
        return Or(_eliminate_iff_imply(expr.left), _eliminate_iff_imply(expr.right))
    
    if isinstance(expr, Imply):
        # P -> Q  =>  ~P | Q
        left = _eliminate_iff_imply(expr.left)
        right = _eliminate_iff_imply(expr.right)
        return Or(Not(left), right)
    
    if isinstance(expr, Iff):
        # P <-> Q  =>  (P -> Q) & (Q -> P)  =>  (~P | Q) & (~Q | P)
        left = _eliminate_iff_imply(expr.left)
        right = _eliminate_iff_imply(expr.right)
        return And(
            Or(Not(left), right),
            Or(Not(right), left)
        )
    
    raise ValueError(f"Unknown expression type: {type(expr)}")


def _push_negation(expr: Expr) -> Expr:
    """推入否定到文字层"""
    if isinstance(expr, Var):
        return expr
    
    if isinstance(expr, Not):
        return _negate_push(expr.operand)
    
    if isinstance(expr, And):
        return And(_push_negation(expr.left), _push_negation(expr.right))
    
    if isinstance(expr, Or):
        return Or(_push_negation(expr.left), _push_negation(expr.right))
    
    # Imply 和 Iff 应该已经被消除
    raise ValueError(f"Unexpected expression type in NNF conversion: {type(expr)}")


def _negate_push(expr: Expr) -> Expr:
    """对表达式取否定并推入"""
    if isinstance(expr, Var):
        return Not(expr)
    
    if isinstance(expr, Not):
        # ~~P => P
        return _push_negation(expr.operand)
    
    if isinstance(expr, And):
        # ~(P & Q) => ~P | ~Q (德摩根定律)
        return Or(_negate_push(expr.left), _negate_push(expr.right))
    
    if isinstance(expr, Or):
        # ~(P | Q) => ~P & ~Q (德摩根定律)
        return And(_negate_push(expr.left), _negate_push(expr.right))
    
    raise ValueError(f"Unexpected expression type in negation push: {type(expr)}")


def to_cnf(expr: Expr) -> CNF:
    """
    转换为合取范式（CNF）
    
    Args:
        expr: 逻辑公式
        
    Returns:
        等价的 CNF
    """
    # 1. 先转换为 NNF
    nnf = to_nnf(expr)
    
    # 2. 应用分配律转换为 CNF
    return _nnf_to_cnf(nnf)


def _nnf_to_cnf(expr: Expr) -> CNF:
    """将 NNF 转换为 CNF"""
    if isinstance(expr, Var):
        lit = Literal(expr.name, True)
        return CNF({Clause(frozenset({lit}))})
    
    if isinstance(expr, Not):
        # NNF 中 Not 只出现在变量前
        if isinstance(expr.operand, Var):
            lit = Literal(expr.operand.name, False)
            return CNF({Clause(frozenset({lit}))})
        raise ValueError("Not should only appear before Var in NNF")
    
    if isinstance(expr, And):
        left_cnf = _nnf_to_cnf(expr.left)
        right_cnf = _nnf_to_cnf(expr.right)
        return left_cnf.union(right_cnf)
    
    if isinstance(expr, Or):
        left_cnf = _nnf_to_cnf(expr.left)
        right_cnf = _nnf_to_cnf(expr.right)
        return _distribute_or(left_cnf, right_cnf)
    
    raise ValueError(f"Unexpected expression type in CNF conversion: {type(expr)}")


def _distribute_or(cnf1: CNF, cnf2: CNF) -> CNF:
    """
    分配律：(A1 & A2 & ...) | (B1 & B2 & ...)
    => (A1 | B1) & (A1 | B2) & ... & (A2 | B1) & ...
    """
    if cnf1.is_empty():
        return cnf2
    if cnf2.is_empty():
        return cnf1
    
    result: Set[Clause] = set()
    for c1 in cnf1.clauses:
        for c2 in cnf2.clauses:
            # 合并两个子句
            new_clause = Clause(c1.literals | c2.literals)
            # 跳过永真子句
            if not new_clause.is_tautology():
                result.add(new_clause)
    
    return CNF(result)


def expr_to_literal(expr: Expr) -> Literal | None:
    """
    将表达式转换为文字（如果可能）
    
    Args:
        expr: 逻辑公式
        
    Returns:
        文字，或 None（如果不是文字）
    """
    if isinstance(expr, Var):
        return Literal(expr.name, True)
    if isinstance(expr, Not) and isinstance(expr.operand, Var):
        return Literal(expr.operand.name, False)
    return None


# ============================================================
# 归结消解
# ============================================================

def resolve(c1: Clause, c2: Clause, var: str) -> Clause | None:
    """
    归结消解：对两个子句在指定变量上进行归结
    
    例如：(A | P) 和 (B | ~P) 归结得到 (A | B)
    
    Args:
        c1: 第一个子句
        c2: 第二个子句
        var: 归结变量
        
    Returns:
        归结结果，或 None（如果无法归结）
    """
    pos_lit = Literal(var, True)
    neg_lit = Literal(var, False)
    
    # 检查是否可以归结
    if pos_lit in c1.literals and neg_lit in c2.literals:
        new_lits = (c1.literals - {pos_lit}) | (c2.literals - {neg_lit})
        return Clause(frozenset(new_lits))
    elif neg_lit in c1.literals and pos_lit in c2.literals:
        new_lits = (c1.literals - {neg_lit}) | (c2.literals - {pos_lit})
        return Clause(frozenset(new_lits))
    
    return None


def find_resolvable_var(c1: Clause, c2: Clause) -> str | None:
    """
    查找可以归结的变量
    
    Args:
        c1: 第一个子句
        c2: 第二个子句
        
    Returns:
        可归结的变量名，或 None
    """
    c1_pos = {l.var for l in c1.literals if l.positive}
    c1_neg = {l.var for l in c1.literals if not l.positive}
    c2_pos = {l.var for l in c2.literals if l.positive}
    c2_neg = {l.var for l in c2.literals if not l.positive}
    
    # 查找 c1 中为正、c2 中为负的变量
    candidates = (c1_pos & c2_neg) | (c1_neg & c2_pos)
    
    if candidates:
        return next(iter(candidates))
    return None


def resolution_refutation(cnf: CNF, max_iterations: int = 1000) -> Tuple[bool, List[Tuple[Clause, Clause, Clause]]]:
    """
    归结反驳：尝试推导出空子句
    
    Args:
        cnf: CNF 公式
        max_iterations: 最大迭代次数
        
    Returns:
        (是否推出空子句, 归结步骤列表)
        步骤格式：(子句1, 子句2, 归结结果)
    """
    clauses = set(cnf.clauses)
    steps: List[Tuple[Clause, Clause, Clause]] = []
    new_clauses: Set[Clause] = set()
    
    for _ in range(max_iterations):
        clause_list = list(clauses)
        
        for i, c1 in enumerate(clause_list):
            for c2 in clause_list[i+1:]:
                var = find_resolvable_var(c1, c2)
                if var:
                    resolvent = resolve(c1, c2, var)
                    if resolvent is not None:
                        steps.append((c1, c2, resolvent))
                        
                        if resolvent.is_empty():
                            return True, steps
                        
                        if resolvent not in clauses and not resolvent.is_tautology():
                            new_clauses.add(resolvent)
        
        if not new_clauses:
            break
        
        clauses |= new_clauses
        new_clauses = set()
    
    return False, steps

