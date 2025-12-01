"""
证明状态管理

管理证明过程中的状态，包括：
- 当前已证明的公式
- 假设栈（用于条件证明）
- 证明步骤历史
- 目标跟踪
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict, FrozenSet
from enum import Enum
from ..logic.ast import Expr


class ProofStatus(Enum):
    """证明状态"""
    IN_PROGRESS = "in_progress"  # 进行中
    SUCCESS = "success"          # 成功
    FAILED = "failed"            # 失败
    TIMEOUT = "timeout"          # 超时


@dataclass
class ProofStep:
    """
    证明步骤
    """
    step_number: int            # 步骤编号
    formula: Expr               # 该步骤推出的公式
    rule_name: str              # 使用的规则名称
    premise_steps: List[int]    # 前提步骤编号
    justification: str          # 解释说明
    assumption_level: int = 0   # 假设层级（0 表示非假设）
    
    def __str__(self) -> str:
        premises = ", ".join(str(p) for p in self.premise_steps) if self.premise_steps else "假设"
        indent = "  " * self.assumption_level
        return f"{indent}{self.step_number}. {self.formula}  [{self.rule_name}, {premises}]"


@dataclass
class Assumption:
    """
    假设
    """
    formula: Expr               # 假设的公式
    step_number: int            # 引入步骤编号
    level: int                  # 嵌套层级
    target: Optional[Expr]      # 目标（用于条件证明）


@dataclass
class ProofState:
    """
    证明状态
    
    管理完整的证明过程状态。
    """
    axioms: FrozenSet[Expr]                          # 初始公理
    goal: Expr                                        # 最终目标
    steps: List[ProofStep] = field(default_factory=list)  # 证明步骤
    knowledge_base: Set[Expr] = field(default_factory=set)  # 当前已知公式
    assumptions: List[Assumption] = field(default_factory=list)  # 假设栈
    status: ProofStatus = ProofStatus.IN_PROGRESS    # 当前状态
    
    def __post_init__(self):
        # 将公理加入知识库和步骤
        if not self.steps:
            for i, axiom in enumerate(self.axioms):
                self.steps.append(ProofStep(
                    step_number=i + 1,
                    formula=axiom,
                    rule_name="axiom",
                    premise_steps=[],
                    justification=f"公理 {i + 1}"
                ))
                self.knowledge_base.add(axiom)
    
    @classmethod
    def from_problem(cls, axioms: List[Expr], goal: Expr) -> ProofState:
        """
        从证明问题创建状态
        
        Args:
            axioms: 公理列表
            goal: 目标
            
        Returns:
            初始证明状态
        """
        return cls(
            axioms=frozenset(axioms),
            goal=goal,
            steps=[],
            knowledge_base=set(),
        )
    
    @property
    def current_step_number(self) -> int:
        """当前步骤编号"""
        return len(self.steps)
    
    @property
    def assumption_level(self) -> int:
        """当前假设层级"""
        return len(self.assumptions)
    
    @property
    def is_complete(self) -> bool:
        """是否完成证明"""
        return self.goal in self.knowledge_base
    
    @property
    def has_contradiction(self) -> bool:
        """是否存在矛盾"""
        from ..logic.ast import Not
        for formula in self.knowledge_base:
            if isinstance(formula, Not):
                if formula.operand in self.knowledge_base:
                    return True
        return False
    
    def add_step(self, formula: Expr, rule_name: str, 
                 premise_steps: List[int], justification: str) -> ProofStep:
        """
        添加证明步骤
        
        Args:
            formula: 推出的公式
            rule_name: 规则名称
            premise_steps: 前提步骤编号
            justification: 解释
            
        Returns:
            新的证明步骤
        """
        step = ProofStep(
            step_number=self.current_step_number + 1,
            formula=formula,
            rule_name=rule_name,
            premise_steps=premise_steps,
            justification=justification,
            assumption_level=self.assumption_level
        )
        self.steps.append(step)
        self.knowledge_base.add(formula)
        
        # 检查是否完成
        if self.goal in self.knowledge_base:
            self.status = ProofStatus.SUCCESS
        
        return step
    
    def introduce_assumption(self, formula: Expr, target: Optional[Expr] = None) -> ProofStep:
        """
        引入假设（用于条件证明或归谬法）
        
        Args:
            formula: 假设的公式
            target: 条件证明的目标
            
        Returns:
            假设步骤
        """
        assumption = Assumption(
            formula=formula,
            step_number=self.current_step_number + 1,
            level=self.assumption_level + 1,
            target=target
        )
        self.assumptions.append(assumption)
        
        step = ProofStep(
            step_number=self.current_step_number + 1,
            formula=formula,
            rule_name="assumption",
            premise_steps=[],
            justification="假设",
            assumption_level=self.assumption_level
        )
        self.steps.append(step)
        self.knowledge_base.add(formula)
        
        return step
    
    def discharge_assumption(self) -> Optional[Assumption]:
        """
        释放最近的假设
        
        Returns:
            被释放的假设，或 None
        """
        if self.assumptions:
            assumption = self.assumptions.pop()
            # 从知识库中移除假设范围内的公式
            # （简化处理：只移除假设本身）
            self.knowledge_base.discard(assumption.formula)
            return assumption
        return None
    
    def conditional_proof(self, assumption: Expr, conclusion: Expr) -> Optional[ProofStep]:
        """
        完成条件证明：从假设 P 推出 Q，得到 P → Q
        
        Args:
            assumption: 假设
            conclusion: 在假设下推出的结论
            
        Returns:
            条件证明步骤
        """
        from ..logic.ast import Imply
        
        if conclusion in self.knowledge_base:
            implication = Imply(assumption, conclusion)
            
            # 查找假设和结论的步骤编号
            assumption_step = None
            conclusion_step = None
            for step in self.steps:
                if step.formula == assumption and step.rule_name == "assumption":
                    assumption_step = step.step_number
                if step.formula == conclusion:
                    conclusion_step = step.step_number
            
            if assumption_step and conclusion_step:
                # 释放假设
                self.discharge_assumption()
                
                return self.add_step(
                    formula=implication,
                    rule_name="imply_intro",
                    premise_steps=[assumption_step, conclusion_step],
                    justification=f"条件证明：假设 {assumption}，得 {conclusion}，因此 {implication}"
                )
        
        return None
    
    def get_step_by_formula(self, formula: Expr) -> Optional[ProofStep]:
        """根据公式查找步骤"""
        for step in reversed(self.steps):
            if step.formula == formula:
                return step
        return None
    
    def clone(self) -> ProofState:
        """创建状态的深拷贝"""
        return ProofState(
            axioms=self.axioms,
            goal=self.goal,
            steps=self.steps.copy(),
            knowledge_base=self.knowledge_base.copy(),
            assumptions=self.assumptions.copy(),
            status=self.status
        )
    
    def format_proof(self) -> str:
        """格式化输出证明"""
        lines = [
            "=" * 60,
            "证明",
            "=" * 60,
            "",
            "公理:",
        ]
        
        for axiom in self.axioms:
            lines.append(f"  {axiom}")
        
        lines.extend([
            "",
            f"目标: {self.goal}",
            "",
            "证明步骤:",
            "-" * 60,
        ])
        
        for step in self.steps:
            lines.append(str(step))
        
        lines.extend([
            "-" * 60,
            "",
            f"状态: {self.status.value}",
        ])
        
        if self.status == ProofStatus.SUCCESS:
            lines.append("✓ 证明完成")
        elif self.status == ProofStatus.FAILED:
            lines.append("✗ 证明失败")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def get_proof_summary(self) -> Dict:
        """获取证明摘要"""
        return {
            "axiom_count": len(self.axioms),
            "step_count": len(self.steps),
            "goal": str(self.goal),
            "status": self.status.value,
            "rules_used": list(set(s.rule_name for s in self.steps)),
            "is_complete": self.is_complete
        }

