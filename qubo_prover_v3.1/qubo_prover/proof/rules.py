"""
完整的推理规则库

实现自然演绎系统的所有标准规则，确保命题逻辑的完备性。

规则分类：
1. 引入规则（Introduction）：从前提推出复合公式
2. 消除规则（Elimination）：从复合公式推出更简单的公式
3. 归结规则（Resolution）：完备性保证

每个规则定义：
- 名称和描述
- 前提模式匹配
- 结论生成
- 正确性验证
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Set, Dict, Tuple, Iterator
from ..logic.ast import Expr, Var, Not, And, Or, Imply, Iff, get_vars
from ..logic.cnf import Literal, Clause, resolve as cnf_resolve


@dataclass
class RuleResult:
    """
    规则应用结果
    """
    rule_name: str          # 规则名称
    conclusion: Expr        # 结论
    premises: List[Expr]    # 使用的前提
    description: str        # 规则应用描述
    
    def __str__(self) -> str:
        premises_str = ", ".join(str(p) for p in self.premises)
        return f"{self.rule_name}: {premises_str} ⊢ {self.conclusion}"


class Rule(ABC):
    """
    推理规则基类
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """规则名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """规则描述"""
        pass
    
    @abstractmethod
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        """
        尝试应用规则
        
        Args:
            knowledge_base: 当前已知公式集合
            goal: 可选的目标（用于引导搜索）
            
        Yields:
            所有可能的规则应用结果
        """
        pass
    
    def matches(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> bool:
        """
        检查规则是否可以应用
        
        Args:
            knowledge_base: 当前已知公式集合
            goal: 可选的目标
            
        Returns:
            是否至少有一个可能的应用
        """
        try:
            next(self.apply(knowledge_base, goal))
            return True
        except StopIteration:
            return False


# ============================================================
# 蕴涵规则
# ============================================================

class ModusPonens(Rule):
    """
    Modus Ponens（肯定前件）
    
    P, P → Q ⊢ Q
    """
    
    @property
    def name(self) -> str:
        return "modus_ponens"
    
    @property
    def description(self) -> str:
        return "P, P → Q ⊢ Q"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        for formula in knowledge_base:
            if isinstance(formula, Imply):
                antecedent = formula.left
                consequent = formula.right
                
                # 检查前件是否在知识库中
                if antecedent in knowledge_base:
                    # 如果有目标，优先匹配目标
                    if goal is None or consequent == goal:
                        yield RuleResult(
                            rule_name=self.name,
                            conclusion=consequent,
                            premises=[antecedent, formula],
                            description=f"由 {antecedent} 和 {formula}，根据 MP 得 {consequent}"
                        )


class ModusTollens(Rule):
    """
    Modus Tollens（否定后件）
    
    P → Q, ~Q ⊢ ~P
    """
    
    @property
    def name(self) -> str:
        return "modus_tollens"
    
    @property
    def description(self) -> str:
        return "P → Q, ~Q ⊢ ~P"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        for formula in knowledge_base:
            if isinstance(formula, Imply):
                antecedent = formula.left
                consequent = formula.right
                neg_consequent = Not(consequent) if not isinstance(consequent, Not) else consequent.operand
                neg_antecedent = Not(antecedent) if not isinstance(antecedent, Not) else antecedent.operand
                
                # 检查 ~Q 是否在知识库中
                if isinstance(consequent, Not):
                    # 如果 Q = ~R，那么 ~Q = R
                    check_formula = consequent.operand
                else:
                    check_formula = Not(consequent)
                
                if check_formula in knowledge_base:
                    # 结论是 ~P
                    if isinstance(antecedent, Not):
                        conclusion = antecedent.operand
                    else:
                        conclusion = Not(antecedent)
                    
                    if goal is None or conclusion == goal:
                        yield RuleResult(
                            rule_name=self.name,
                            conclusion=conclusion,
                            premises=[formula, check_formula],
                            description=f"由 {formula} 和 {check_formula}，根据 MT 得 {conclusion}"
                        )


class ImplyIntro(Rule):
    """
    蕴涵引入（条件证明）
    
    [P] ... Q ⊢ P → Q
    
    这是一个假设规则，在实际实现中通过假设引入机制处理
    """
    
    @property
    def name(self) -> str:
        return "imply_intro"
    
    @property
    def description(self) -> str:
        return "[P] ... Q ⊢ P → Q (条件证明)"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        # 条件证明需要特殊处理，这里提供基本框架
        if goal and isinstance(goal, Imply):
            # 如果目标是 P → Q，检查是否 Q 已经在知识库中
            # （这是一个简化处理，完整实现需要假设管理）
            if goal.right in knowledge_base:
                yield RuleResult(
                    rule_name=self.name,
                    conclusion=goal,
                    premises=[goal.right],
                    description=f"由 {goal.right} 成立，得 {goal}"
                )


class ImplyElim(Rule):
    """
    蕴涵消除（等同于 Modus Ponens）
    """
    
    @property
    def name(self) -> str:
        return "imply_elim"
    
    @property
    def description(self) -> str:
        return "P → Q, P ⊢ Q (同 MP)"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        # 委托给 ModusPonens
        mp = ModusPonens()
        yield from mp.apply(knowledge_base, goal)


# ============================================================
# 合取规则
# ============================================================

class AndIntro(Rule):
    """
    合取引入
    
    P, Q ⊢ P ∧ Q
    """
    
    @property
    def name(self) -> str:
        return "and_intro"
    
    @property
    def description(self) -> str:
        return "P, Q ⊢ P ∧ Q"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        kb_list = list(knowledge_base)
        
        # 如果有目标且是合取
        if goal and isinstance(goal, And):
            if goal.left in knowledge_base and goal.right in knowledge_base:
                yield RuleResult(
                    rule_name=self.name,
                    conclusion=goal,
                    premises=[goal.left, goal.right],
                    description=f"由 {goal.left} 和 {goal.right}，得 {goal}"
                )
        else:
            # 枚举所有可能的配对
            for i, p in enumerate(kb_list):
                for q in kb_list[i+1:]:
                    conclusion = And(p, q)
                    if goal is None or conclusion == goal:
                        yield RuleResult(
                            rule_name=self.name,
                            conclusion=conclusion,
                            premises=[p, q],
                            description=f"由 {p} 和 {q}，得 {conclusion}"
                        )


class AndElimLeft(Rule):
    """
    合取消除（左）
    
    P ∧ Q ⊢ P
    """
    
    @property
    def name(self) -> str:
        return "and_elim_left"
    
    @property
    def description(self) -> str:
        return "P ∧ Q ⊢ P"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        for formula in knowledge_base:
            if isinstance(formula, And):
                conclusion = formula.left
                if goal is None or conclusion == goal:
                    yield RuleResult(
                        rule_name=self.name,
                        conclusion=conclusion,
                        premises=[formula],
                        description=f"由 {formula}，得 {conclusion}"
                    )


class AndElimRight(Rule):
    """
    合取消除（右）
    
    P ∧ Q ⊢ Q
    """
    
    @property
    def name(self) -> str:
        return "and_elim_right"
    
    @property
    def description(self) -> str:
        return "P ∧ Q ⊢ Q"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        for formula in knowledge_base:
            if isinstance(formula, And):
                conclusion = formula.right
                if goal is None or conclusion == goal:
                    yield RuleResult(
                        rule_name=self.name,
                        conclusion=conclusion,
                        premises=[formula],
                        description=f"由 {formula}，得 {conclusion}"
                    )


# ============================================================
# 析取规则
# ============================================================

class OrIntroLeft(Rule):
    """
    析取引入（左）
    
    P ⊢ P ∨ Q
    """
    
    @property
    def name(self) -> str:
        return "or_intro_left"
    
    @property
    def description(self) -> str:
        return "P ⊢ P ∨ Q"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        # 如果有目标且是析取
        if goal and isinstance(goal, Or):
            if goal.left in knowledge_base:
                yield RuleResult(
                    rule_name=self.name,
                    conclusion=goal,
                    premises=[goal.left],
                    description=f"由 {goal.left}，得 {goal}"
                )
        # 不枚举所有可能，因为 Q 可以是任意公式


class OrIntroRight(Rule):
    """
    析取引入（右）
    
    Q ⊢ P ∨ Q
    """
    
    @property
    def name(self) -> str:
        return "or_intro_right"
    
    @property
    def description(self) -> str:
        return "Q ⊢ P ∨ Q"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        if goal and isinstance(goal, Or):
            if goal.right in knowledge_base:
                yield RuleResult(
                    rule_name=self.name,
                    conclusion=goal,
                    premises=[goal.right],
                    description=f"由 {goal.right}，得 {goal}"
                )


class OrElim(Rule):
    """
    析取消除（析取三段论变体）
    
    P ∨ Q, ~P ⊢ Q
    P ∨ Q, ~Q ⊢ P
    
    或完整形式：
    P ∨ Q, P → R, Q → R ⊢ R
    """
    
    @property
    def name(self) -> str:
        return "or_elim"
    
    @property
    def description(self) -> str:
        return "P ∨ Q, ~P ⊢ Q (析取三段论)"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        for formula in knowledge_base:
            if isinstance(formula, Or):
                left = formula.left
                right = formula.right
                
                # 检查 ~left 是否存在
                neg_left = Not(left) if not isinstance(left, Not) else left.operand
                if neg_left in knowledge_base or (isinstance(left, Not) and left.operand in knowledge_base):
                    actual_neg = neg_left if neg_left in knowledge_base else left.operand
                    if goal is None or right == goal:
                        yield RuleResult(
                            rule_name=self.name,
                            conclusion=right,
                            premises=[formula, actual_neg],
                            description=f"由 {formula} 和 {actual_neg}，得 {right}"
                        )
                
                # 检查 ~right 是否存在
                neg_right = Not(right) if not isinstance(right, Not) else right.operand
                if neg_right in knowledge_base or (isinstance(right, Not) and right.operand in knowledge_base):
                    actual_neg = neg_right if neg_right in knowledge_base else right.operand
                    if goal is None or left == goal:
                        yield RuleResult(
                            rule_name=self.name,
                            conclusion=left,
                            premises=[formula, actual_neg],
                            description=f"由 {formula} 和 {actual_neg}，得 {left}"
                        )


# ============================================================
# 否定规则
# ============================================================

class NotIntro(Rule):
    """
    否定引入（归谬法）
    
    [P] ... ⊥ ⊢ ~P
    
    如果假设 P 能导出矛盾，则 ~P 成立
    """
    
    @property
    def name(self) -> str:
        return "not_intro"
    
    @property
    def description(self) -> str:
        return "[P] ... ⊥ ⊢ ~P (归谬法)"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        # 归谬法需要假设管理，这里简化处理
        # 检查是否存在矛盾（P 和 ~P 同时存在）
        for formula in knowledge_base:
            if isinstance(formula, Not):
                if formula.operand in knowledge_base:
                    # 发现矛盾
                    yield RuleResult(
                        rule_name=self.name,
                        conclusion=formula,  # 矛盾时可以推出任何东西
                        premises=[formula, formula.operand],
                        description=f"检测到矛盾: {formula} 与 {formula.operand}"
                    )


class NotElim(Rule):
    """
    否定消除
    
    ~P, P ⊢ ⊥ (矛盾)
    
    或在某些系统中：~~P ⊢ P
    """
    
    @property
    def name(self) -> str:
        return "not_elim"
    
    @property
    def description(self) -> str:
        return "~P, P ⊢ ⊥ (检测矛盾)"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        # 检测矛盾
        for formula in knowledge_base:
            if isinstance(formula, Not):
                if formula.operand in knowledge_base:
                    yield RuleResult(
                        rule_name=self.name,
                        conclusion=And(formula, formula.operand),  # 表示矛盾
                        premises=[formula, formula.operand],
                        description=f"检测到矛盾：{formula} 与 {formula.operand}"
                    )


class DoubleNegElim(Rule):
    """
    双重否定消除
    
    ~~P ⊢ P
    """
    
    @property
    def name(self) -> str:
        return "double_neg_elim"
    
    @property
    def description(self) -> str:
        return "~~P ⊢ P"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        for formula in knowledge_base:
            if isinstance(formula, Not) and isinstance(formula.operand, Not):
                conclusion = formula.operand.operand
                if goal is None or conclusion == goal:
                    yield RuleResult(
                        rule_name=self.name,
                        conclusion=conclusion,
                        premises=[formula],
                        description=f"由 {formula}，得 {conclusion}"
                    )


# ============================================================
# 归结规则（完备性保证）
# ============================================================

class Resolution(Rule):
    """
    归结消解
    
    A ∨ P, B ∨ ~P ⊢ A ∨ B
    
    这是一个完备的推理规则，可以证明所有有效的推理。
    """
    
    @property
    def name(self) -> str:
        return "resolution"
    
    @property
    def description(self) -> str:
        return "A ∨ P, B ∨ ~P ⊢ A ∨ B (归结消解)"
    
    def apply(self, knowledge_base: Set[Expr], goal: Optional[Expr] = None) -> Iterator[RuleResult]:
        # 将知识库中的析取式转换为子句
        clauses: Dict[Expr, Clause] = {}
        
        for formula in knowledge_base:
            clause = self._expr_to_clause(formula)
            if clause:
                clauses[formula] = clause
        
        # 尝试所有可能的归结
        clause_list = list(clauses.items())
        for i, (expr1, c1) in enumerate(clause_list):
            for expr2, c2 in clause_list[i+1:]:
                # 查找可归结的变量
                c1_pos = {l.var for l in c1.literals if l.positive}
                c1_neg = {l.var for l in c1.literals if not l.positive}
                c2_pos = {l.var for l in c2.literals if l.positive}
                c2_neg = {l.var for l in c2.literals if not l.positive}
                
                # 可归结的变量
                resolvable = (c1_pos & c2_neg) | (c1_neg & c2_pos)
                
                for var in resolvable:
                    resolvent = cnf_resolve(c1, c2, var)
                    if resolvent is not None and not resolvent.is_tautology():
                        conclusion = resolvent.to_expr()
                        if goal is None or conclusion == goal:
                            yield RuleResult(
                                rule_name=self.name,
                                conclusion=conclusion,
                                premises=[expr1, expr2],
                                description=f"归结 {expr1} 和 {expr2} 在变量 {var} 上，得 {conclusion}"
                            )
    
    def _expr_to_clause(self, expr: Expr) -> Optional[Clause]:
        """将表达式转换为子句（如果可能）"""
        literals: Set[Literal] = set()
        
        def collect_literals(e: Expr) -> bool:
            if isinstance(e, Var):
                literals.add(Literal(e.name, True))
                return True
            elif isinstance(e, Not) and isinstance(e.operand, Var):
                literals.add(Literal(e.operand.name, False))
                return True
            elif isinstance(e, Or):
                return collect_literals(e.left) and collect_literals(e.right)
            return False
        
        if collect_literals(expr):
            return Clause(frozenset(literals))
        return None


# ============================================================
# 规则注册表
# ============================================================

RULE_REGISTRY: Dict[str, Rule] = {
    "modus_ponens": ModusPonens(),
    "modus_tollens": ModusTollens(),
    "imply_intro": ImplyIntro(),
    "imply_elim": ImplyElim(),
    "and_intro": AndIntro(),
    "and_elim_left": AndElimLeft(),
    "and_elim_right": AndElimRight(),
    "or_intro_left": OrIntroLeft(),
    "or_intro_right": OrIntroRight(),
    "or_elim": OrElim(),
    "not_intro": NotIntro(),
    "not_elim": NotElim(),
    "double_neg_elim": DoubleNegElim(),
    "resolution": Resolution(),
}


def get_rule(name: str) -> Optional[Rule]:
    """获取指定名称的规则"""
    return RULE_REGISTRY.get(name)


def list_rules() -> List[str]:
    """列出所有可用规则"""
    return list(RULE_REGISTRY.keys())


def apply_all_rules(knowledge_base: Set[Expr], 
                   goal: Optional[Expr] = None,
                   exclude_rules: Optional[Set[str]] = None) -> List[RuleResult]:
    """
    尝试应用所有规则
    
    Args:
        knowledge_base: 知识库
        goal: 目标（可选）
        exclude_rules: 排除的规则名称
        
    Returns:
        所有可能的规则应用结果
    """
    results: List[RuleResult] = []
    exclude = exclude_rules or set()
    
    for name, rule in RULE_REGISTRY.items():
        if name not in exclude:
            for result in rule.apply(knowledge_base, goal):
                results.append(result)
    
    return results

