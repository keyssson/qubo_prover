"""
推理规则库
定义所有支持的逻辑推理规则及其 QUBO 编码
"""

from typing import Dict, List, Tuple, Optional
from pyqubo import Binary
from .ast import Expr, Var, Not, And, Or, Imply


class Rule:
    """推理规则基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def matches(self, axioms: List[Expr], goal: Expr) -> bool:
        """
        检查规则是否适用于给定的公理和目标
        
        Args:
            axioms: 公理列表
            goal: 证明目标
            
        Returns:
            是否匹配
        """
        raise NotImplementedError
    
    def encode(self, var_map: Dict[str, Binary], control_var: Binary) -> Tuple:
        """
        生成规则的 QUBO 约束
        
        Args:
            var_map: 变量映射
            control_var: 规则控制变量（R=1 表示使用此规则）
            
        Returns:
            (约束表达式, 相关变量名列表)
        """
        raise NotImplementedError


class ModusPonensRule(Rule):
    """
    Modus Ponens（肯定前件式）
    从 P 和 P→Q 推出 Q
    """
    
    def __init__(self):
        super().__init__(
            "Modus Ponens",
            "From P and P→Q, infer Q"
        )
    
    def matches(self, axioms: List[Expr], goal: Expr) -> bool:
        """检查是否存在 P 和 P→Q 形式的公理，且目标是 Q"""
        # 简化版：总是返回 True，让 QUBO 决定是否使用
        return True
    
    def encode(self, p_var: Binary, imp_var: Binary, q_var: Binary, r_var: Binary):
        """
        编码 MP 规则
        
        约束：
        - 如果 R=1（使用规则），则必须 P=1, Imp=1, Q=1
        - 如果 R=0（不使用规则），则 Q 可以为任意值
        
        H = R*(1-P) + R*(1-Imp) + R*(1-Q) + Q*(1-R)
        
        解释：
        - R*(1-P): 如果 R=1 且 P=0，惩罚
        - R*(1-Imp): 如果 R=1 且 Imp=0，惩罚
        - R*(1-Q): 如果 R=1 且 Q=0，惩罚
        - Q*(1-R): 如果 Q=1 但 R=0，惩罚（Q 必须通过规则推导）
        """
        constraint = (
            r_var * (1 - p_var) +
            r_var * (1 - imp_var) +
            r_var * (1 - q_var) +
            q_var * (1 - r_var)
        )
        return constraint


class ModusTollensRule(Rule):
    """
    Modus Tollens（否定后件式）
    从 P→Q 和 ~Q 推出 ~P
    """
    
    def __init__(self):
        super().__init__(
            "Modus Tollens",
            "From P→Q and ~Q, infer ~P"
        )
    
    def matches(self, axioms: List[Expr], goal: Expr) -> bool:
        return True
    
    def encode(self, imp_var: Binary, not_q_var: Binary, not_p_var: Binary, r_var: Binary):
        """
        编码 MT 规则
        
        H = R*(1-Imp) + R*(1-NotQ) + R*(1-NotP) + NotP*(1-R)
        """
        constraint = (
            r_var * (1 - imp_var) +
            r_var * (1 - not_q_var) +
            r_var * (1 - not_p_var) +
            not_p_var * (1 - r_var)
        )
        return constraint


class AndEliminationLeftRule(Rule):
    """
    And-Elimination Left（合取消除-左）
    从 P∧Q 推出 P
    """
    
    def __init__(self):
        super().__init__(
            "And-Elimination (Left)",
            "From P∧Q, infer P"
        )
    
    def matches(self, axioms: List[Expr], goal: Expr) -> bool:
        return True
    
    def encode(self, and_var: Binary, p_var: Binary, r_var: Binary):
        """
        编码 And-Elim-Left 规则
        
        H = R*(1-And) + R*(1-P) + P*(1-R)
        """
        constraint = (
            r_var * (1 - and_var) +
            r_var * (1 - p_var) +
            p_var * (1 - r_var)
        )
        return constraint


class AndEliminationRightRule(Rule):
    """
    And-Elimination Right（合取消除-右）
    从 P∧Q 推出 Q
    """
    
    def __init__(self):
        super().__init__(
            "And-Elimination (Right)",
            "From P∧Q, infer Q"
        )
    
    def matches(self, axioms: List[Expr], goal: Expr) -> bool:
        return True
    
    def encode(self, and_var: Binary, q_var: Binary, r_var: Binary):
        """
        编码 And-Elim-Right 规则
        
        H = R*(1-And) + R*(1-Q) + Q*(1-R)
        """
        constraint = (
            r_var * (1 - and_var) +
            r_var * (1 - q_var) +
            q_var * (1 - r_var)
        )
        return constraint


class AndIntroductionRule(Rule):
    """
    And-Introduction（合取引入）
    从 P 和 Q 推出 P∧Q
    """
    
    def __init__(self):
        super().__init__(
            "And-Introduction",
            "From P and Q, infer P∧Q"
        )
    
    def matches(self, axioms: List[Expr], goal: Expr) -> bool:
        return True
    
    def encode(self, p_var: Binary, q_var: Binary, and_var: Binary, r_var: Binary):
        """
        编码 And-Intro 规则
        
        H = R*(1-P) + R*(1-Q) + R*(1-And) + And*(1-R)
        """
        constraint = (
            r_var * (1 - p_var) +
            r_var * (1 - q_var) +
            r_var * (1 - and_var) +
            and_var * (1 - r_var)
        )
        return constraint


class OrIntroductionRule(Rule):
    """
    Or-Introduction（析取引入）
    从 P 推出 P∨Q
    """
    
    def __init__(self):
        super().__init__(
            "Or-Introduction",
            "From P, infer P∨Q"
        )
    
    def matches(self, axioms: List[Expr], goal: Expr) -> bool:
        return True
    
    def encode(self, p_var: Binary, or_var: Binary, r_var: Binary):
        """
        编码 Or-Intro 规则
        
        H = R*(1-P) + R*(1-Or) + Or*(1-R)
        """
        constraint = (
            r_var * (1 - p_var) +
            r_var * (1 - or_var) +
            or_var * (1 - r_var)
        )
        return constraint


class DoubleNegationEliminationRule(Rule):
    """
    Double Negation Elimination（双重否定消除）
    从 ~~P 推出 P
    """
    
    def __init__(self):
        super().__init__(
            "Double Negation Elimination",
            "From ~~P, infer P"
        )
    
    def matches(self, axioms: List[Expr], goal: Expr) -> bool:
        return True
    
    def encode(self, not_not_p_var: Binary, p_var: Binary, r_var: Binary):
        """
        编码 DNE 规则
        
        H = R*(1-NotNotP) + R*(1-P) + P*(1-R)
        """
        constraint = (
            r_var * (1 - not_not_p_var) +
            r_var * (1 - p_var) +
            p_var * (1 - r_var)
        )
        return constraint


# 规则库单例
RULE_LIBRARY = {
    "modus_ponens": ModusPonensRule(),
    "modus_tollens": ModusTollensRule(),
    "and_elim_left": AndEliminationLeftRule(),
    "and_elim_right": AndEliminationRightRule(),
    "and_intro": AndIntroductionRule(),
    "or_intro": OrIntroductionRule(),
    "double_neg_elim": DoubleNegationEliminationRule(),
}


def get_rule(name: str) -> Optional[Rule]:
    """根据名称获取规则"""
    return RULE_LIBRARY.get(name)


def list_all_rules() -> List[str]:
    """列出所有可用规则"""
    return list(RULE_LIBRARY.keys())

