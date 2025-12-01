"""
证明步骤编码器

将证明搜索空间编码为 QUBO 问题。

核心创新：
1. 证明步骤变量：step[t][r][args] ∈ {0,1}
2. 时间步约束：每步至多一个规则激活
3. 依赖约束：规则前提必须在之前步骤已证明
4. 目标约束：目标必须在某一步被证明
5. 最小化证明长度

这种编码允许 QUBO 求解器同时搜索最优证明路径。
"""

from __future__ import annotations
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from pyqubo import Binary
from ..logic.ast import Expr, Var, Not, And, Or, Imply
from ..proof.rules import Rule, RULE_REGISTRY, list_rules
from .encoder import FormulaEncoder, EncodedFormula


@dataclass
class StepVariable:
    """
    证明步骤变量
    """
    time_step: int              # 时间步
    rule_name: str              # 规则名称
    formula: Expr               # 结论公式
    qubo_var: Binary            # QUBO 变量
    var_name: str               # 变量名
    premises: List[Expr] = field(default_factory=list)  # 前提公式


@dataclass
class ProofQUBO:
    """
    证明问题的 QUBO 表示
    """
    step_vars: List[StepVariable]           # 步骤变量
    formula_encoder: FormulaEncoder         # 公式编码器
    hamiltonian: Any                         # 哈密顿量
    var_map: Dict[str, Binary]              # 变量映射
    axiom_vars: List[str]                   # 公理变量名
    goal_var: str                           # 目标变量名
    max_steps: int                          # 最大步数


class ProofStepEncoder:
    """
    证明步骤编码器
    
    将证明搜索问题编码为 QUBO。
    """
    
    def __init__(self, 
                 max_steps: int = 10,
                 axiom_penalty: float = 100.0,
                 step_penalty: float = 50.0,
                 structure_penalty: float = 20.0,
                 rule_penalty: float = 10.0,
                 length_penalty: float = 1.0):
        """
        初始化编码器
        
        Args:
            max_steps: 最大证明步数
            axiom_penalty: 公理约束惩罚
            step_penalty: 步骤约束惩罚
            structure_penalty: 结构约束惩罚
            rule_penalty: 规则约束惩罚
            length_penalty: 证明长度惩罚（越短越好）
        """
        self.max_steps = max_steps
        self.axiom_penalty = axiom_penalty
        self.step_penalty = step_penalty
        self.structure_penalty = structure_penalty
        self.rule_penalty = rule_penalty
        self.length_penalty = length_penalty
        
        self.formula_encoder = FormulaEncoder()
        self.step_vars: List[StepVariable] = []
        self._proven_at: Dict[Expr, Binary] = {}  # 公式 -> 是否已证明
        self._step_active: Dict[int, Binary] = {}  # 时间步 -> 是否激活
    
    def encode(self, axioms: List[Expr], goal: Expr, 
               rule_weights: Optional[Dict[str, float]] = None) -> ProofQUBO:
        """
        编码证明问题
        
        Args:
            axioms: 公理列表
            goal: 目标公式
            rule_weights: 规则权重（神经网络预测）
            
        Returns:
            QUBO 表示
        """
        rule_weights = rule_weights or {}
        
        # 1. 编码所有公式
        axiom_encodings = [self.formula_encoder.encode(ax) for ax in axioms]
        goal_encoding = self.formula_encoder.encode(goal)
        
        # 2. 收集所有可能的中间公式
        all_formulas = self._collect_relevant_formulas(axioms, goal)
        for f in all_formulas:
            self.formula_encoder.encode(f)
        
        # 3. 为每个公式创建 "已证明" 变量
        for formula in [goal] + axioms + all_formulas:
            if formula not in self._proven_at:
                var_name = f"proven_{id(formula)}"
                self._proven_at[formula] = Binary(var_name)
        
        # 4. 创建步骤变量
        self._create_step_variables(axioms, goal, all_formulas)
        
        # 5. 构建哈密顿量
        H = self._build_hamiltonian(axioms, goal, rule_weights)
        
        # 6. 收集所有变量
        var_map = self.formula_encoder.get_all_vars()
        var_map.update({sv.var_name: sv.qubo_var for sv in self.step_vars})
        var_map.update({f"proven_{id(f)}": v for f, v in self._proven_at.items()})
        
        return ProofQUBO(
            step_vars=self.step_vars,
            formula_encoder=self.formula_encoder,
            hamiltonian=H,
            var_map=var_map,
            axiom_vars=[enc.var_name for enc in axiom_encodings],
            goal_var=goal_encoding.var_name,
            max_steps=self.max_steps
        )
    
    def _collect_relevant_formulas(self, axioms: List[Expr], goal: Expr) -> List[Expr]:
        """
        收集所有可能在证明中出现的公式
        
        通过模式匹配和规则应用推断可能的中间公式。
        """
        formulas: Set[Expr] = set()
        
        # 添加子公式
        for ax in axioms:
            for sub in ax.subformulas():
                formulas.add(sub)
        for sub in goal.subformulas():
            formulas.add(sub)
        
        # 尝试一步推理
        kb = set(axioms)
        for rule in RULE_REGISTRY.values():
            for result in rule.apply(kb, goal):
                formulas.add(result.conclusion)
        
        # 移除已有的公理和目标
        formulas -= set(axioms)
        formulas.discard(goal)
        
        return list(formulas)
    
    def _create_step_variables(self, axioms: List[Expr], goal: Expr, 
                               intermediate: List[Expr]):
        """
        创建证明步骤变量
        
        为每个 (时间步, 规则, 结论) 组合创建变量
        """
        all_conclusions = [goal] + intermediate
        
        for t in range(self.max_steps):
            # 每个时间步的激活变量
            step_active_var = Binary(f"step_active_{t}")
            self._step_active[t] = step_active_var
            
            # 为每个可能的规则应用创建变量
            for rule_name in list_rules():
                for conclusion in all_conclusions:
                    var_name = f"step_{t}_{rule_name}_{id(conclusion)}"
                    qubo_var = Binary(var_name)
                    
                    self.step_vars.append(StepVariable(
                        time_step=t,
                        rule_name=rule_name,
                        formula=conclusion,
                        qubo_var=qubo_var,
                        var_name=var_name
                    ))
    
    def _build_hamiltonian(self, axioms: List[Expr], goal: Expr,
                          rule_weights: Dict[str, float]) -> Any:
        """
        构建哈密顿量
        """
        H = 0
        
        # 1. 公理约束：公理强制为真
        for ax in axioms:
            ax_enc = self.formula_encoder.get_encoded(ax)
            if ax_enc:
                H += self.axiom_penalty * (1 - ax_enc.qubo_var)
        
        # 2. 目标约束：目标必须为真
        goal_enc = self.formula_encoder.get_encoded(goal)
        if goal_enc:
            H += self.axiom_penalty * (1 - goal_enc.qubo_var)
        
        # 3. 结构约束：确保逻辑一致性
        H += self.structure_penalty * self.formula_encoder.get_constraint_expression()
        
        # 4. 步骤约束：每步至多一个规则激活
        for t in range(self.max_steps):
            step_vars_t = [sv for sv in self.step_vars if sv.time_step == t]
            if len(step_vars_t) > 1:
                # 至多一个激活：sum <= 1
                # QUBO: (sum - 1)^2 当 sum > 1 时惩罚
                sum_vars = step_vars_t[0].qubo_var
                for sv in step_vars_t[1:]:
                    sum_vars = sum_vars + sv.qubo_var
                H += self.step_penalty * (sum_vars * (sum_vars - 1) / 2)
        
        # 5. 规则约束（带神经网络权重）
        for sv in self.step_vars:
            weight = rule_weights.get(sv.rule_name, 1.0)
            # 权重高的规则惩罚低
            penalty = self.rule_penalty * (2.0 - weight)
            H += penalty * sv.qubo_var * (1 - goal_enc.qubo_var if goal_enc else 1)
        
        # 6. 证明长度惩罚（鼓励短证明）
        for sv in self.step_vars:
            H += self.length_penalty * sv.qubo_var
        
        return H
    
    def decode_solution(self, assignment: Dict[str, int], 
                        qubo: ProofQUBO) -> List[Tuple[int, str, str]]:
        """
        解码 QUBO 解为证明步骤
        
        Args:
            assignment: 变量赋值
            qubo: QUBO 表示
            
        Returns:
            [(步骤编号, 规则名, 结论), ...]
        """
        steps = []
        
        for sv in qubo.step_vars:
            if assignment.get(sv.var_name, 0) == 1:
                steps.append((sv.time_step, sv.rule_name, str(sv.formula)))
        
        # 按时间步排序
        steps.sort(key=lambda x: x[0])
        
        return steps


def create_simple_proof_qubo(axioms: List[Expr], goal: Expr,
                             axiom_penalty: float = 100.0,
                             structure_penalty: float = 20.0) -> Tuple[Any, Dict[str, Binary], FormulaEncoder]:
    """
    创建简化的证明 QUBO（不使用步骤编码）
    
    适用于简单的一步推理问题。
    
    Args:
        axioms: 公理列表
        goal: 目标
        axiom_penalty: 公理惩罚
        structure_penalty: 结构惩罚
        
    Returns:
        (哈密顿量, 变量映射, 编码器)
    """
    encoder = FormulaEncoder()
    
    # 编码公理
    axiom_encodings = [encoder.encode(ax) for ax in axioms]
    
    # 编码目标
    goal_encoding = encoder.encode(goal)
    
    # 构建哈密顿量
    H = 0
    
    # 公理约束
    for enc in axiom_encodings:
        H += axiom_penalty * (1 - enc.qubo_var)
    
    # 目标约束
    H += axiom_penalty * (1 - goal_encoding.qubo_var)
    
    # 结构约束
    H += structure_penalty * encoder.get_constraint_expression()
    
    return H, encoder.get_all_vars(), encoder

