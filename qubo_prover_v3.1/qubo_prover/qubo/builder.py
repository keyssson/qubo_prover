"""
QUBO 构建器

将证明问题构建为完整的 QUBO 问题。

改进点：
- 模块化设计，易于扩展
- 支持神经网络权重集成
- 优化的约束生成
- 详细的调试信息
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass, field
from pyqubo import Binary
from ..logic.ast import Expr, Var, Not, And, Or, Imply
from ..logic.parser import parse
from ..proof.rules import RULE_REGISTRY, RuleResult
from .encoder import FormulaEncoder, EncodedFormula
from .constraints import ConstraintBuilder


@dataclass
class QUBOProblem:
    """
    QUBO 问题表示
    """
    model: Any                              # PyQUBO 编译后的模型
    var_map: Dict[str, Binary]              # 变量映射
    qubo_dict: Dict[Tuple[str, str], float] # QUBO 矩阵
    bqm: Any                                # BQM 对象
    offset: float                           # 能量偏移
    encoder: FormulaEncoder                 # 公式编码器
    axiom_vars: List[str]                   # 公理变量
    goal_var: str                           # 目标变量
    info: Dict[str, Any] = field(default_factory=dict)  # 附加信息


class QUBOBuilder:
    """
    QUBO 构建器
    
    将命题逻辑证明问题转换为 QUBO 问题。
    """
    
    def __init__(self,
                 axiom_penalty: float = 100.0,
                 goal_penalty: float = 100.0,
                 structure_penalty: float = 20.0,
                 rule_penalty: float = 10.0,
                 verbose: bool = True):
        """
        初始化构建器
        
        Args:
            axiom_penalty: 公理约束惩罚系数
            goal_penalty: 目标约束惩罚系数
            structure_penalty: 结构约束惩罚系数
            rule_penalty: 规则约束惩罚系数
            verbose: 是否输出详细信息
        """
        self.axiom_penalty = axiom_penalty
        self.goal_penalty = goal_penalty
        self.structure_penalty = structure_penalty
        self.rule_penalty = rule_penalty
        self.verbose = verbose
        
        self.encoder: Optional[FormulaEncoder] = None
        self.constraint_builder: Optional[ConstraintBuilder] = None
        self.axioms: List[Expr] = []
        self.goal: Optional[Expr] = None
        self.axiom_encodings: List[EncodedFormula] = []
        self.goal_encoding: Optional[EncodedFormula] = None
    
    def build(self, axioms: List[str], goal: str,
              rule_weights: Optional[Dict[str, float]] = None) -> QUBOProblem:
        """
        构建 QUBO 问题
        
        Args:
            axioms: 公理字符串列表
            goal: 目标字符串
            rule_weights: 规则权重（来自神经网络）
            
        Returns:
            QUBO 问题
        """
        rule_weights = rule_weights or {}
        
        # 1. 解析公式
        if self.verbose:
            print("\n" + "=" * 60)
            print("QUBO 构建开始")
            print("=" * 60)
            print(f"\n公理: {axioms}")
            print(f"目标: {goal}")
        
        self.axioms = [parse(ax) for ax in axioms]
        self.goal = parse(goal)
        
        # 2. 初始化编码器
        self.encoder = FormulaEncoder()
        self.constraint_builder = ConstraintBuilder(self.encoder)
        
        # 3. 编码公理和目标
        if self.verbose:
            print("\n[编码阶段]")
        
        self.axiom_encodings = []
        for i, axiom in enumerate(self.axioms):
            enc = self.encoder.encode(axiom)
            self.axiom_encodings.append(enc)
            if self.verbose:
                print(f"  公理 {i+1}: {axiom} -> {enc.var_name}")
        
        self.goal_encoding = self.encoder.encode(self.goal)
        if self.verbose:
            print(f"  目标: {self.goal} -> {self.goal_encoding.var_name}")
        
        # 4. 构建哈密顿量
        if self.verbose:
            print("\n[构建哈密顿量]")
        
        H = self._build_hamiltonian(rule_weights)
        
        # 5. 编译 QUBO
        if self.verbose:
            print("\n[编译 QUBO]")
        
        model = H.compile()
        qubo_dict, offset = model.to_qubo()
        bqm = model.to_bqm()
        
        if self.verbose:
            print(f"  QUBO 项数: {len(qubo_dict)}")
            print(f"  变量数: {len(self.encoder.get_all_vars())}")
            print(f"  偏移量: {offset}")
        
        # 6. 收集信息
        info = {
            "axiom_count": len(self.axioms),
            "var_count": len(self.encoder.get_all_vars()),
            "prop_var_count": len(self.encoder.get_prop_vars()),
            "constraint_count": len(self.encoder.get_constraints()),
            "qubo_term_count": len(qubo_dict),
        }
        
        return QUBOProblem(
            model=model,
            var_map=self.encoder.get_all_vars(),
            qubo_dict=qubo_dict,
            bqm=bqm,
            offset=offset,
            encoder=self.encoder,
            axiom_vars=[enc.var_name for enc in self.axiom_encodings],
            goal_var=self.goal_encoding.var_name,
            info=info
        )
    
    def _build_hamiltonian(self, rule_weights: Dict[str, float]) -> Any:
        """
        构建哈密顿量
        """
        H = 0
        
        # 1. 公理约束
        if self.verbose:
            print(f"  添加公理约束 (惩罚={self.axiom_penalty})")
        
        for enc in self.axiom_encodings:
            H += self.axiom_penalty * (1 - enc.qubo_var)
            if self.verbose:
                print(f"    - 强制 {enc.var_name} = 1")
        
        # 2. 目标约束
        if self.verbose:
            print(f"  添加目标约束 (惩罚={self.goal_penalty})")
        
        H += self.goal_penalty * (1 - self.goal_encoding.qubo_var)
        if self.verbose:
            print(f"    - 强制 {self.goal_encoding.var_name} = 1")
        
        # 3. 结构约束
        if self.verbose:
            print(f"  添加结构约束 (惩罚={self.structure_penalty})")
        
        constraints = self.encoder.get_constraints()
        for constraint_type, constraint_expr in constraints:
            H += self.structure_penalty * constraint_expr
            if self.verbose:
                print(f"    - {constraint_type} 约束")
        
        # 4. 推理规则约束
        if self.verbose:
            print(f"  添加推理规则约束 (基础惩罚={self.rule_penalty})")
        
        H += self._build_rule_constraints(rule_weights)
        
        return H
    
    def _build_rule_constraints(self, rule_weights: Dict[str, float]) -> Any:
        """
        构建推理规则约束
        """
        H_rules = 0
        
        # 检测并编码 Modus Ponens
        for axiom in self.axioms:
            if isinstance(axiom, Imply):
                p = axiom.left
                q = axiom.right
                
                # 检查 P 是否也是公理
                if p in self.axioms:
                    if self.verbose:
                        print(f"    - 检测到 MP: {p}, {axiom} ⊢ {q}")
                    
                    # 获取权重
                    weight = rule_weights.get("modus_ponens", 1.0)
                    penalty = self.rule_penalty * (2.0 - weight)
                    
                    # 编码规则
                    p_enc = self.encoder.encode(p)
                    imp_enc = self.encoder.encode(axiom)
                    q_enc = self.encoder.encode(q)
                    
                    # 规则控制变量
                    r_var = Binary(f"Rule_MP_{p_enc.var_name}_{q_enc.var_name}")
                    
                    # MP 约束：如果 P=1 且 P->Q=1 且 R=1，则 Q=1
                    mp_constraint = (
                        r_var * (1 - p_enc.qubo_var) +
                        r_var * (1 - imp_enc.qubo_var) +
                        r_var * (1 - q_enc.qubo_var)
                    )
                    H_rules += penalty * mp_constraint
        
        # 检测 Modus Tollens
        for axiom in self.axioms:
            if isinstance(axiom, Imply):
                p = axiom.left
                q = axiom.right
                
                # 检查 ~Q 是否是公理
                neg_q = Not(q) if not isinstance(q, Not) else q.operand
                if neg_q in self.axioms:
                    if self.verbose:
                        print(f"    - 检测到 MT: {axiom}, {neg_q} ⊢ ~{p}")
                    
                    weight = rule_weights.get("modus_tollens", 1.0)
                    penalty = self.rule_penalty * (2.0 - weight)
                    
                    imp_enc = self.encoder.encode(axiom)
                    neg_q_enc = self.encoder.encode(neg_q)
                    neg_p = Not(p) if not isinstance(p, Not) else p.operand
                    neg_p_enc = self.encoder.encode(neg_p)
                    
                    r_var = Binary(f"Rule_MT_{p}_{q}")
                    
                    mt_constraint = (
                        r_var * (1 - imp_enc.qubo_var) +
                        r_var * (1 - neg_q_enc.qubo_var) +
                        r_var * (1 - neg_p_enc.qubo_var)
                    )
                    H_rules += penalty * mt_constraint
        
        # 检测 And-Elimination
        for axiom in self.axioms:
            if isinstance(axiom, And):
                if self.verbose:
                    print(f"    - 检测到 And-Elim: {axiom} ⊢ {axiom.left}, {axiom.right}")
                
                weight = rule_weights.get("and_elim_left", 1.0)
                penalty = self.rule_penalty * (2.0 - weight)
                
                and_enc = self.encoder.encode(axiom)
                left_enc = self.encoder.encode(axiom.left)
                right_enc = self.encoder.encode(axiom.right)
                
                # And-Elim: 如果 P&Q=1，则 P=1 且 Q=1
                ae_constraint = (
                    and_enc.qubo_var * (1 - left_enc.qubo_var) +
                    and_enc.qubo_var * (1 - right_enc.qubo_var)
                )
                H_rules += penalty * ae_constraint
        
        return H_rules
    
    def get_variable_info(self) -> Dict[str, Any]:
        """获取变量信息"""
        if not self.encoder:
            return {}
        
        return {
            "all_vars": list(self.encoder.get_all_vars().keys()),
            "prop_vars": list(self.encoder.get_prop_vars()),
            "axiom_vars": [enc.var_name for enc in self.axiom_encodings],
            "goal_var": self.goal_encoding.var_name if self.goal_encoding else None,
            "formula_map": {
                enc.var_name: str(enc.formula)
                for f, enc in self.encoder._formula_map.items()
            },
            "axiom_formulas": [str(ax) for ax in self.axioms],
            "goal_formula": str(self.goal) if self.goal else ""
        }
    
    def summary(self) -> str:
        """生成构建摘要"""
        if not self.encoder:
            return "构建器未初始化"
        
        lines = [
            "=" * 60,
            "QUBO 构建摘要",
            "=" * 60,
            "",
            f"公理数量: {len(self.axioms)}",
        ]
        
        for i, axiom in enumerate(self.axioms):
            lines.append(f"  {i+1}. {axiom}")
        
        lines.extend([
            "",
            f"目标: {self.goal}",
            "",
            self.encoder.summary(),
            "",
            "=" * 60
        ])
        
        return "\n".join(lines)


def build_qubo(axioms: List[str], goal: str,
               axiom_penalty: float = 100.0,
               structure_penalty: float = 20.0,
               rule_weights: Optional[Dict[str, float]] = None,
               verbose: bool = False) -> QUBOProblem:
    """
    便捷函数：构建 QUBO 问题
    
    Args:
        axioms: 公理字符串列表
        goal: 目标字符串
        axiom_penalty: 公理惩罚
        structure_penalty: 结构惩罚
        rule_weights: 规则权重
        verbose: 是否详细输出
        
    Returns:
        QUBO 问题
    """
    builder = QUBOBuilder(
        axiom_penalty=axiom_penalty,
        goal_penalty=axiom_penalty,
        structure_penalty=structure_penalty,
        verbose=verbose
    )
    return builder.build(axioms, goal, rule_weights)

