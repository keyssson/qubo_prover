"""
约束生成器

生成各种类型的 QUBO 约束：
- 公理约束：强制公理为真
- 目标约束：强制目标为真
- 结构约束：确保逻辑语义一致性
- 规则约束：编码推理规则
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from pyqubo import Binary
from ..logic.ast import Expr, Var, Not, And, Or, Imply, Iff
from .encoder import FormulaEncoder, EncodedFormula


class ConstraintBuilder:
    """
    约束构建器
    
    提供构建各类 QUBO 约束的方法。
    """
    
    def __init__(self, encoder: FormulaEncoder):
        """
        初始化约束构建器
        
        Args:
            encoder: 公式编码器
        """
        self.encoder = encoder
        self._constraints: List[Tuple[str, Any, float]] = []  # (类型, 表达式, 权重)
    
    def add_truth_constraint(self, formula: Expr, value: bool = True, 
                            weight: float = 100.0) -> Any:
        """
        添加真值约束：强制公式取指定真值
        
        Args:
            formula: 公式
            value: 目标真值
            weight: 惩罚权重
            
        Returns:
            约束表达式
        """
        encoded = self.encoder.encode(formula)
        
        if value:
            # 强制为真：惩罚 (1 - var)
            constraint = weight * (1 - encoded.qubo_var)
        else:
            # 强制为假：惩罚 var
            constraint = weight * encoded.qubo_var
        
        self._constraints.append(("TRUTH", constraint, weight))
        return constraint
    
    def add_implication_constraint(self, antecedent: Expr, consequent: Expr,
                                  weight: float = 50.0) -> Any:
        """
        添加蕴涵约束：如果 A 为真，则 B 必须为真
        
        Args:
            antecedent: 前件
            consequent: 后件
            weight: 惩罚权重
            
        Returns:
            约束表达式
        """
        ant_enc = self.encoder.encode(antecedent)
        con_enc = self.encoder.encode(consequent)
        
        # A=1 且 B=0 时惩罚
        # 惩罚 = A * (1 - B)
        constraint = weight * ant_enc.qubo_var * (1 - con_enc.qubo_var)
        
        self._constraints.append(("IMPLICATION", constraint, weight))
        return constraint
    
    def add_equivalence_constraint(self, expr1: Expr, expr2: Expr,
                                  weight: float = 50.0) -> Any:
        """
        添加等价约束：两个公式必须取相同真值
        
        Args:
            expr1: 第一个公式
            expr2: 第二个公式
            weight: 惩罚权重
            
        Returns:
            约束表达式
        """
        enc1 = self.encoder.encode(expr1)
        enc2 = self.encoder.encode(expr2)
        
        # 不相等时惩罚：(x1 - x2)^2
        constraint = weight * (enc1.qubo_var - enc2.qubo_var) ** 2
        
        self._constraints.append(("EQUIVALENCE", constraint, weight))
        return constraint
    
    def add_exclusion_constraint(self, formulas: List[Expr],
                                weight: float = 50.0) -> Any:
        """
        添加互斥约束：至多一个公式为真
        
        Args:
            formulas: 公式列表
            weight: 惩罚权重
            
        Returns:
            约束表达式
        """
        encodings = [self.encoder.encode(f) for f in formulas]
        
        if len(encodings) < 2:
            return 0
        
        # sum <= 1
        # 惩罚 sum * (sum - 1) / 2 当 sum >= 2
        total = encodings[0].qubo_var
        for enc in encodings[1:]:
            total = total + enc.qubo_var
        
        constraint = weight * total * (total - 1) / 2
        
        self._constraints.append(("EXCLUSION", constraint, weight))
        return constraint
    
    def add_at_least_one_constraint(self, formulas: List[Expr],
                                   weight: float = 50.0) -> Any:
        """
        添加至少一个约束：至少一个公式为真
        
        Args:
            formulas: 公式列表
            weight: 惩罚权重
            
        Returns:
            约束表达式
        """
        encodings = [self.encoder.encode(f) for f in formulas]
        
        if not encodings:
            return weight  # 空列表，总是惩罚
        
        # 所有都为 0 时惩罚
        # 1 - (1 - x1)(1 - x2)... 应该为 1
        # 等价于 sum >= 1
        total = encodings[0].qubo_var
        for enc in encodings[1:]:
            total = total + enc.qubo_var
        
        # sum = 0 时惩罚：(1 - indicator)
        # 使用辅助变量或简化为 weight * product(1 - xi)
        # 简化：惩罚 (sum < 1) 等价于 sum = 0
        # QUBO: 当 sum = 0 时能量高
        
        # 使用软约束
        constraint = weight * (1 - total) * (1 - total)
        
        self._constraints.append(("AT_LEAST_ONE", constraint, weight))
        return constraint
    
    def add_modus_ponens_constraint(self, p: Expr, p_implies_q: Imply, q: Expr,
                                   weight: float = 20.0) -> Any:
        """
        添加 Modus Ponens 约束
        
        如果 P=1 且 (P→Q)=1，则 Q=1
        
        Args:
            p: 前件 P
            p_implies_q: 蕴涵 P→Q
            q: 后件 Q
            weight: 惩罚权重
            
        Returns:
            约束表达式
        """
        p_enc = self.encoder.encode(p)
        imp_enc = self.encoder.encode(p_implies_q)
        q_enc = self.encoder.encode(q)
        
        # P=1 且 Imp=1 且 Q=0 时惩罚
        constraint = weight * p_enc.qubo_var * imp_enc.qubo_var * (1 - q_enc.qubo_var)
        
        self._constraints.append(("MODUS_PONENS", constraint, weight))
        return constraint
    
    def add_modus_tollens_constraint(self, p_implies_q: Imply, not_q: Expr, not_p: Expr,
                                    weight: float = 20.0) -> Any:
        """
        添加 Modus Tollens 约束
        
        如果 (P→Q)=1 且 ~Q=1，则 ~P=1
        
        Args:
            p_implies_q: 蕴涵 P→Q
            not_q: ~Q
            not_p: ~P
            weight: 惩罚权重
            
        Returns:
            约束表达式
        """
        imp_enc = self.encoder.encode(p_implies_q)
        nq_enc = self.encoder.encode(not_q)
        np_enc = self.encoder.encode(not_p)
        
        constraint = weight * imp_enc.qubo_var * nq_enc.qubo_var * (1 - np_enc.qubo_var)
        
        self._constraints.append(("MODUS_TOLLENS", constraint, weight))
        return constraint
    
    def get_total_constraint(self) -> Any:
        """获取所有约束的总和"""
        if not self._constraints:
            return 0
        
        total = self._constraints[0][1]
        for _, constraint, _ in self._constraints[1:]:
            total = total + constraint
        return total
    
    def get_constraints(self) -> List[Tuple[str, Any, float]]:
        """获取所有约束"""
        return self._constraints.copy()
    
    def summary(self) -> str:
        """生成约束摘要"""
        type_counts: Dict[str, int] = {}
        for ctype, _, _ in self._constraints:
            type_counts[ctype] = type_counts.get(ctype, 0) + 1
        
        lines = [
            "约束摘要",
            "-" * 40,
            f"总约束数: {len(self._constraints)}",
            "",
            "按类型:",
        ]
        for ctype, count in sorted(type_counts.items()):
            lines.append(f"  - {ctype}: {count}")
        
        return "\n".join(lines)


# 便捷函数

def add_axiom_constraint(encoder: FormulaEncoder, axiom: Expr, 
                        weight: float = 100.0) -> Any:
    """添加公理约束"""
    builder = ConstraintBuilder(encoder)
    return builder.add_truth_constraint(axiom, True, weight)


def add_goal_constraint(encoder: FormulaEncoder, goal: Expr,
                       weight: float = 100.0) -> Any:
    """添加目标约束"""
    builder = ConstraintBuilder(encoder)
    return builder.add_truth_constraint(goal, True, weight)


def add_structure_constraint(encoder: FormulaEncoder,
                            weight: float = 20.0) -> Any:
    """添加结构约束"""
    return weight * encoder.get_constraint_expression()


def add_rule_constraint(encoder: FormulaEncoder, rule_name: str,
                       premises: List[Expr], conclusion: Expr,
                       weight: float = 10.0) -> Any:
    """添加规则约束"""
    builder = ConstraintBuilder(encoder)
    
    # 所有前提为真 => 结论为真
    for premise in premises:
        builder.add_implication_constraint(premise, conclusion, weight)
    
    return builder.get_total_constraint()

