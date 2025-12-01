"""
相继式（Sequent）表示

相继式是形如 Γ ⊢ Δ 的结构，其中：
- Γ（Gamma）是前提集合（前件/antecedent）
- Δ（Delta）是结论集合（后件/succedent）

语义：如果 Γ 中所有公式都为真，则 Δ 中至少一个公式为真

用于组织证明搜索和表示证明目标。
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import FrozenSet, Set, Optional, List, Iterator, Tuple
from ..logic.ast import Expr, Not, And, Or, Imply, Iff, Var


@dataclass(frozen=True)
class Sequent:
    """
    相继式
    
    Γ ⊢ Δ
    
    表示：如果 Γ 中所有公式为真，则 Δ 中至少一个公式为真
    """
    antecedent: FrozenSet[Expr]  # 前件 Γ
    succedent: FrozenSet[Expr]   # 后件 Δ
    
    def __str__(self) -> str:
        ant_str = ", ".join(str(f) for f in sorted(self.antecedent, key=str))
        suc_str = ", ".join(str(f) for f in sorted(self.succedent, key=str))
        return f"{ant_str} ⊢ {suc_str}"
    
    def __repr__(self) -> str:
        return f"Sequent({self.antecedent!r}, {self.succedent!r})"
    
    @classmethod
    def from_implication(cls, premises: List[Expr], conclusion: Expr) -> Sequent:
        """
        从蕴涵关系创建相继式
        
        Args:
            premises: 前提列表
            conclusion: 结论
            
        Returns:
            相继式 premises ⊢ conclusion
        """
        return cls(
            antecedent=frozenset(premises),
            succedent=frozenset([conclusion])
        )
    
    @classmethod
    def goal(cls, goal_formula: Expr) -> Sequent:
        """
        创建目标相继式（无前提）
        
        Args:
            goal_formula: 目标公式
            
        Returns:
            相继式 ⊢ goal
        """
        return cls(
            antecedent=frozenset(),
            succedent=frozenset([goal_formula])
        )
    
    def is_axiom(self) -> bool:
        """
        是否为公理相继式
        
        公理相继式：前件和后件有共同元素
        Γ, A ⊢ A, Δ
        """
        return bool(self.antecedent & self.succedent)
    
    def is_closed(self) -> bool:
        """是否已关闭（证明完成）"""
        return self.is_axiom()
    
    def add_antecedent(self, formula: Expr) -> Sequent:
        """向前件添加公式"""
        return Sequent(
            antecedent=self.antecedent | {formula},
            succedent=self.succedent
        )
    
    def add_succedent(self, formula: Expr) -> Sequent:
        """向后件添加公式"""
        return Sequent(
            antecedent=self.antecedent,
            succedent=self.succedent | {formula}
        )
    
    def remove_antecedent(self, formula: Expr) -> Sequent:
        """从前件移除公式"""
        return Sequent(
            antecedent=self.antecedent - {formula},
            succedent=self.succedent
        )
    
    def remove_succedent(self, formula: Expr) -> Sequent:
        """从后件移除公式"""
        return Sequent(
            antecedent=self.antecedent,
            succedent=self.succedent - {formula}
        )
    
    def get_principal_formula(self) -> Optional[Expr]:
        """
        获取主公式（用于分解的复合公式）
        
        优先选择后件中的复合公式
        """
        # 先检查后件
        for f in self.succedent:
            if not isinstance(f, Var):
                return f
        # 再检查前件
        for f in self.antecedent:
            if not isinstance(f, Var):
                return f
        return None


def decompose_sequent(seq: Sequent) -> List[Tuple[str, List[Sequent]]]:
    """
    分解相继式
    
    根据相继式演算规则分解复合公式。
    
    Args:
        seq: 要分解的相继式
        
    Returns:
        [(规则名称, [子相继式列表]), ...]
    """
    results: List[Tuple[str, List[Sequent]]] = []
    
    # 检查公理
    if seq.is_axiom():
        return [("axiom", [])]
    
    # 分解后件中的公式（右规则）
    for formula in seq.succedent:
        sub_seq = seq.remove_succedent(formula)
        
        if isinstance(formula, Not):
            # ~R: Γ, A ⊢ Δ  =>  Γ ⊢ ~A, Δ
            new_seq = sub_seq.add_antecedent(formula.operand)
            results.append(("not_right", [new_seq]))
        
        elif isinstance(formula, And):
            # &R: Γ ⊢ A, Δ 和 Γ ⊢ B, Δ  =>  Γ ⊢ A&B, Δ
            seq1 = sub_seq.add_succedent(formula.left)
            seq2 = sub_seq.add_succedent(formula.right)
            results.append(("and_right", [seq1, seq2]))
        
        elif isinstance(formula, Or):
            # |R: Γ ⊢ A, B, Δ  =>  Γ ⊢ A|B, Δ
            new_seq = sub_seq.add_succedent(formula.left).add_succedent(formula.right)
            results.append(("or_right", [new_seq]))
        
        elif isinstance(formula, Imply):
            # ->R: Γ, A ⊢ B, Δ  =>  Γ ⊢ A->B, Δ
            new_seq = sub_seq.add_antecedent(formula.left).add_succedent(formula.right)
            results.append(("imply_right", [new_seq]))
        
        elif isinstance(formula, Iff):
            # <->R: Γ, A ⊢ B, Δ 和 Γ, B ⊢ A, Δ  =>  Γ ⊢ A<->B, Δ
            seq1 = sub_seq.add_antecedent(formula.left).add_succedent(formula.right)
            seq2 = sub_seq.add_antecedent(formula.right).add_succedent(formula.left)
            results.append(("iff_right", [seq1, seq2]))
    
    # 分解前件中的公式（左规则）
    for formula in seq.antecedent:
        sub_seq = seq.remove_antecedent(formula)
        
        if isinstance(formula, Not):
            # ~L: Γ ⊢ A, Δ  =>  Γ, ~A ⊢ Δ
            new_seq = sub_seq.add_succedent(formula.operand)
            results.append(("not_left", [new_seq]))
        
        elif isinstance(formula, And):
            # &L: Γ, A, B ⊢ Δ  =>  Γ, A&B ⊢ Δ
            new_seq = sub_seq.add_antecedent(formula.left).add_antecedent(formula.right)
            results.append(("and_left", [new_seq]))
        
        elif isinstance(formula, Or):
            # |L: Γ, A ⊢ Δ 和 Γ, B ⊢ Δ  =>  Γ, A|B ⊢ Δ
            seq1 = sub_seq.add_antecedent(formula.left)
            seq2 = sub_seq.add_antecedent(formula.right)
            results.append(("or_left", [seq1, seq2]))
        
        elif isinstance(formula, Imply):
            # ->L: Γ ⊢ A, Δ 和 Γ, B ⊢ Δ  =>  Γ, A->B ⊢ Δ
            seq1 = sub_seq.add_succedent(formula.left)
            seq2 = sub_seq.add_antecedent(formula.right)
            results.append(("imply_left", [seq1, seq2]))
        
        elif isinstance(formula, Iff):
            # <->L: Γ, A, B ⊢ Δ 和 Γ ⊢ A, B, Δ  =>  Γ, A<->B ⊢ Δ
            seq1 = sub_seq.add_antecedent(formula.left).add_antecedent(formula.right)
            seq2 = sub_seq.add_succedent(formula.left).add_succedent(formula.right)
            results.append(("iff_left", [seq1, seq2]))
    
    return results


def prove_sequent(seq: Sequent, max_depth: int = 100) -> Tuple[bool, List[str]]:
    """
    证明相继式
    
    使用深度优先搜索证明相继式。
    
    Args:
        seq: 要证明的相继式
        max_depth: 最大搜索深度
        
    Returns:
        (是否成功, 证明步骤列表)
    """
    proof_steps: List[str] = []
    
    def search(s: Sequent, depth: int) -> bool:
        if depth > max_depth:
            return False
        
        # 检查公理
        if s.is_axiom():
            proof_steps.append(f"公理: {s}")
            return True
        
        # 尝试分解
        decompositions = decompose_sequent(s)
        
        for rule_name, sub_sequents in decompositions:
            # 检查所有子相继式是否都能证明
            all_proved = True
            sub_proofs: List[str] = []
            
            for sub_seq in sub_sequents:
                if not search(sub_seq, depth + 1):
                    all_proved = False
                    break
            
            if all_proved:
                proof_steps.append(f"规则 {rule_name}: {s}")
                return True
        
        return False
    
    success = search(seq, 0)
    return success, proof_steps


def sequent_to_formula(seq: Sequent) -> Expr:
    """
    将相继式转换为公式
    
    Γ ⊢ Δ  <=>  (∧Γ) -> (∨Δ)
    
    Args:
        seq: 相继式
        
    Returns:
        等价公式
    """
    # 构建前件的合取
    ant_list = list(seq.antecedent)
    if not ant_list:
        antecedent_formula: Optional[Expr] = None
    elif len(ant_list) == 1:
        antecedent_formula = ant_list[0]
    else:
        antecedent_formula = ant_list[0]
        for f in ant_list[1:]:
            antecedent_formula = And(antecedent_formula, f)
    
    # 构建后件的析取
    suc_list = list(seq.succedent)
    if not suc_list:
        succedent_formula: Optional[Expr] = None
    elif len(suc_list) == 1:
        succedent_formula = suc_list[0]
    else:
        succedent_formula = suc_list[0]
        for f in suc_list[1:]:
            succedent_formula = Or(succedent_formula, f)
    
    # 组合
    if antecedent_formula is None:
        if succedent_formula is None:
            # 空相继式，返回矛盾
            return And(Var("_EMPTY_"), Not(Var("_EMPTY_")))
        return succedent_formula
    else:
        if succedent_formula is None:
            return Not(antecedent_formula)
        return Imply(antecedent_formula, succedent_formula)

