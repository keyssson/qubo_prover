"""
动态 QUBO 构建器
根据输入的公理和目标动态生成哈密顿量
"""

from typing import List, Dict, Tuple, Any
from pyqubo import Binary, Placeholder
from .ast import Expr, Var, Not, And, Or, Imply, get_all_vars
from .parser import parse
from .formula_encoder import FormulaEncoder


class QUBOBuilder:
    """
    动态 QUBO 构建器
    
    核心功能：
    1. 解析公理和目标
    2. 为所有公式分配 QUBO 变量
    3. 添加公理约束（强制为真）
    4. 添加目标约束（强制为真）
    5. 添加推理规则约束
    6. 编译为 QUBO 矩阵
    """
    
    def __init__(self, 
                 axiom_penalty: float = 100.0,
                 structure_penalty: float = 10.0,
                 rule_penalty: float = 5.0):
        """
        初始化构建器
        
        Args:
            axiom_penalty: 公理约束的惩罚系数（应该很大）
            structure_penalty: 结构约束的惩罚系数（中等）
            rule_penalty: 推理规则的惩罚系数（较小）
        """
        self.axiom_penalty = axiom_penalty
        self.structure_penalty = structure_penalty
        self.rule_penalty = rule_penalty
        
        self.encoder = FormulaEncoder()
        self.axioms: List[Expr] = []
        self.goal: Expr = None
        self.axiom_vars: List[Tuple[str, Binary]] = []
        self.goal_var: Tuple[str, Binary] = None
        
    def build(self, axioms: List[str], goal: str) -> Tuple[Any, Dict[str, Binary], float]:
        """
        构建 QUBO 问题
        
        Args:
            axioms: 公理字符串列表，如 ["P", "P->Q"]
            goal: 目标字符串，如 "Q"
            
        Returns:
            (PyQUBO Model, 变量映射, offset)
        """
        # 1. 解析公理和目标
        self.axioms = [parse(ax) for ax in axioms]
        self.goal = parse(goal)
        
        print(f"\n[解析阶段]")
        print(f"公理: {axioms}")
        print(f"目标: {goal}")
        
        # 2. 编码所有公式
        print(f"\n[编码阶段]")
        for i, axiom in enumerate(self.axioms):
            var_name, var = self.encoder.encode_formula(axiom, f"Axiom{i}_")
            self.axiom_vars.append((var_name, var))
            print(f"  公理 {i+1}: {axiom} -> 变量 {var_name}")
        
        goal_var_name, goal_var = self.encoder.encode_formula(self.goal, "Goal_")
        self.goal_var = (goal_var_name, goal_var)
        print(f"  目标: {self.goal} -> 变量 {goal_var_name}")
        
        # 3. 构建哈密顿量
        print(f"\n[构建哈密顿量]")
        H = 0
        
        # 3.1 公理约束（强制所有公理为真）
        print(f"  添加公理约束（惩罚系数={self.axiom_penalty}）")
        for var_name, var in self.axiom_vars:
            H += self.axiom_penalty * (1 - var)
            print(f"    - 强制 {var_name} = 1")
        
        # 3.2 目标约束（强制目标为真）
        print(f"  添加目标约束（惩罚系数={self.axiom_penalty}）")
        H += self.axiom_penalty * (1 - self.goal_var[1])
        print(f"    - 强制 {self.goal_var[0]} = 1")
        
        # 3.3 结构约束（确保公式语义一致性）
        print(f"  添加结构约束（惩罚系数={self.structure_penalty}）")
        constraints = self.encoder.get_constraints()
        for constraint_info in constraints:
            constraint_type = constraint_info[0]
            constraint_expr = constraint_info[-1]
            H += self.structure_penalty * constraint_expr
            print(f"    - {constraint_type} 约束")
        
        # 3.4 推理规则约束（可选，用于引导搜索）
        print(f"  添加推理规则约束（惩罚系数={self.rule_penalty}）")
        H += self._add_rule_constraints()
        
        # 4. 获取所有变量
        var_map = self.encoder.get_all_vars()
        
        print(f"\n[统计信息]")
        print(f"  总变量数: {len(var_map)}")
        print(f"  命题变量数: {len(self.encoder.get_prop_vars())}")
        print(f"  结构约束数: {len(constraints)}")
        
        # 5. 编译为 QUBO
        print(f"\n[编译 QUBO]")
        model = H.compile()
        
        return model, var_map, 0.0
    
    def _add_rule_constraints(self) -> Any:
        """
        添加推理规则约束
        
        当前实现：添加 Modus Ponens 规则作为示例
        """
        H_rules = 0
        
        # 尝试匹配 Modus Ponens: P, P->Q ⊢ Q
        # 查找形如 P->Q 的公理
        for axiom in self.axioms:
            if isinstance(axiom, Imply):
                # 找到蕴涵公式
                p_formula = axiom.left
                q_formula = axiom.right
                
                # 检查 P 是否也是公理
                if p_formula in self.axioms:
                    # 可以应用 MP 规则
                    print(f"    - 检测到 Modus Ponens 模式: {p_formula}, {axiom} ⊢ {q_formula}")
                    
                    # 获取相关变量
                    p_var_name, p_var = self.encoder.encode_formula(p_formula)
                    imp_var_name, imp_var = self.encoder.encode_formula(axiom)
                    q_var_name, q_var = self.encoder.encode_formula(q_formula)
                    
                    # 创建规则控制变量
                    r_var = Binary(f"Rule_MP_{p_var_name}_{q_var_name}")
                    
                    # MP 约束
                    mp_constraint = (
                        r_var * (1 - p_var) +
                        r_var * (1 - imp_var) +
                        r_var * (1 - q_var) +
                        q_var * (1 - r_var)
                    )
                    
                    H_rules += mp_constraint
        
        return H_rules
    
    def compile_qubo(self, model: Any) -> Tuple[Dict, Any, float]:
        """
        编译 PyQUBO 模型为 QUBO 矩阵
        
        Args:
            model: PyQUBO 编译后的模型
            
        Returns:
            (QUBO 字典, BQM 对象, offset)
        """
        qubo, offset = model.to_qubo()
        bqm = model.to_bqm()
        
        print(f"  QUBO 项数: {len(qubo)}")
        print(f"  Offset: {offset}")
        
        return qubo, bqm, offset
    
    def get_variable_info(self) -> Dict[str, Any]:
        """获取变量信息（用于调试和可视化）"""
        return {
            "all_vars": list(self.encoder.get_all_vars().keys()),
            "prop_vars": list(self.encoder.get_prop_vars()),
            "axiom_vars": [name for name, _ in self.axiom_vars],
            "goal_var": self.goal_var[0] if self.goal_var else None,
            "formula_map": {
                name: str(formula) 
                for name, formula in self.encoder.formula_map.items()
            }
        }
    
    def summary(self) -> str:
        """生成构建摘要"""
        lines = [
            "=" * 60,
            "QUBO 构建摘要",
            "=" * 60,
            "",
            f"公理数量: {len(self.axioms)}",
        ]
        
        for i, axiom in enumerate(self.axioms):
            lines.append(f"  {i+1}. {axiom}")
        
        lines.append("")
        lines.append(f"目标: {self.goal}")
        lines.append("")
        lines.append(self.encoder.summary())
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)

