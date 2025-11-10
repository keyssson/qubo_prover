"""
公式编码器
将逻辑公式转换为 QUBO 变量和约束
"""

from typing import Dict, Tuple, Set
from pyqubo import Binary
from .ast import Expr, Var, Not, And, Or, Imply


class FormulaEncoder:
    """
    将逻辑公式编码为 QUBO 变量
    
    核心思想：
    1. 每个命题变量 P 对应一个 QUBO 变量
    2. 每个复合公式对应一个 QUBO 变量，并添加结构约束
    3. 确保语义一致性（如 ~P 与 P 互斥）
    """
    
    def __init__(self):
        self.var_map: Dict[str, Binary] = {}  # 变量名 -> PyQUBO Binary
        self.formula_map: Dict[str, Expr] = {}  # 变量名 -> 原始公式
        self.constraints = []  # 结构约束列表
        self.prop_vars: Set[str] = set()  # 命题变量集合
        
    def encode_formula(self, formula: Expr, name_prefix: str = "") -> Tuple[str, Binary]:
        """
        为公式分配 QUBO 变量
        
        Args:
            formula: 逻辑公式
            name_prefix: 变量名前缀（用于区分不同上下文）
            
        Returns:
            (变量名, PyQUBO Binary 对象)
        """
        # 如果是简单变量，直接返回
        if isinstance(formula, Var):
            var_name = formula.name
            self.prop_vars.add(var_name)
            if var_name not in self.var_map:
                self.var_map[var_name] = Binary(var_name)
                self.formula_map[var_name] = formula
            return var_name, self.var_map[var_name]
        
        # 为复合公式生成唯一变量名
        var_name = self._generate_var_name(formula, name_prefix)
        
        if var_name in self.var_map:
            return var_name, self.var_map[var_name]
        
        # 创建新变量
        var = Binary(var_name)
        self.var_map[var_name] = var
        self.formula_map[var_name] = formula
        
        # 递归编码子公式并添加结构约束
        if isinstance(formula, Not):
            self._encode_not(var_name, var, formula)
        elif isinstance(formula, And):
            self._encode_and(var_name, var, formula, name_prefix)
        elif isinstance(formula, Or):
            self._encode_or(var_name, var, formula, name_prefix)
        elif isinstance(formula, Imply):
            self._encode_imply(var_name, var, formula, name_prefix)
        
        return var_name, var
    
    def _generate_var_name(self, formula: Expr, prefix: str) -> str:
        """生成公式的变量名"""
        if isinstance(formula, Not):
            operand_str = self._formula_to_str(formula.operand)
            return f"{prefix}Not_{operand_str}" if prefix else f"Not_{operand_str}"
        elif isinstance(formula, And):
            left_str = self._formula_to_str(formula.left)
            right_str = self._formula_to_str(formula.right)
            return f"{prefix}And_{left_str}_{right_str}" if prefix else f"And_{left_str}_{right_str}"
        elif isinstance(formula, Or):
            left_str = self._formula_to_str(formula.left)
            right_str = self._formula_to_str(formula.right)
            return f"{prefix}Or_{left_str}_{right_str}" if prefix else f"Or_{left_str}_{right_str}"
        elif isinstance(formula, Imply):
            left_str = self._formula_to_str(formula.left)
            right_str = self._formula_to_str(formula.right)
            return f"{prefix}Imp_{left_str}_{right_str}" if prefix else f"Imp_{left_str}_{right_str}"
        return "Unknown"
    
    def _formula_to_str(self, formula: Expr) -> str:
        """将公式转换为简短字符串（用于变量名）"""
        if isinstance(formula, Var):
            return formula.name
        elif isinstance(formula, Not):
            return f"N{self._formula_to_str(formula.operand)}"
        elif isinstance(formula, And):
            return f"{self._formula_to_str(formula.left)}A{self._formula_to_str(formula.right)}"
        elif isinstance(formula, Or):
            return f"{self._formula_to_str(formula.left)}O{self._formula_to_str(formula.right)}"
        elif isinstance(formula, Imply):
            return f"{self._formula_to_str(formula.left)}I{self._formula_to_str(formula.right)}"
        return "?"
    
    def _encode_not(self, var_name: str, var: Binary, formula: Not):
        """
        编码否定：~P
        约束：Not_P = 1 - P
        等价于：Not_P + P = 1
        QUBO 惩罚：M * (Not_P + P - 1)^2
        """
        operand_name, operand_var = self.encode_formula(formula.operand)
        
        # 约束：var = 1 - operand_var
        # 展开 (var + operand_var - 1)^2
        constraint = (var + operand_var - 1) ** 2
        self.constraints.append(("NOT", var_name, operand_name, constraint))
    
    def _encode_and(self, var_name: str, var: Binary, formula: And, prefix: str):
        """
        编码合取：P & Q
        约束：And = P * Q
        QUBO 惩罚：M * (And - P*Q)^2
        """
        left_name, left_var = self.encode_formula(formula.left, prefix)
        right_name, right_var = self.encode_formula(formula.right, prefix)
        
        # 约束：var = left_var * right_var
        # 展开 (var - left_var * right_var)^2
        constraint = (var - left_var * right_var) ** 2
        self.constraints.append(("AND", var_name, left_name, right_name, constraint))
    
    def _encode_or(self, var_name: str, var: Binary, formula: Or, prefix: str):
        """
        编码析取：P | Q
        约束：Or = P + Q - P*Q (至少一个为真)
        QUBO 惩罚：M * (Or - P - Q + P*Q)^2
        """
        left_name, left_var = self.encode_formula(formula.left, prefix)
        right_name, right_var = self.encode_formula(formula.right, prefix)
        
        # 约束：var = left_var + right_var - left_var * right_var
        constraint = (var - left_var - right_var + left_var * right_var) ** 2
        self.constraints.append(("OR", var_name, left_name, right_name, constraint))
    
    def _encode_imply(self, var_name: str, var: Binary, formula: Imply, prefix: str):
        """
        编码蕴涵：P -> Q
        约束：Imp = ~P | Q = 1 - P + P*Q
        QUBO 惩罚：M * (Imp - 1 + P - P*Q)^2
        """
        left_name, left_var = self.encode_formula(formula.left, prefix)
        right_name, right_var = self.encode_formula(formula.right, prefix)
        
        # 约束：var = 1 - left_var + left_var * right_var
        constraint = (var - 1 + left_var - left_var * right_var) ** 2
        self.constraints.append(("IMPLY", var_name, left_name, right_name, constraint))
    
    def get_all_vars(self) -> Dict[str, Binary]:
        """获取所有 QUBO 变量"""
        return self.var_map.copy()
    
    def get_constraints(self) -> list:
        """获取所有结构约束"""
        return self.constraints.copy()
    
    def get_prop_vars(self) -> Set[str]:
        """获取所有命题变量（不包括辅助变量）"""
        return self.prop_vars.copy()
    
    def get_var(self, name: str) -> Binary:
        """根据名称获取变量"""
        return self.var_map.get(name)
    
    def summary(self) -> str:
        """生成编码摘要"""
        lines = [
            f"总变量数: {len(self.var_map)}",
            f"命题变量数: {len(self.prop_vars)}",
            f"结构约束数: {len(self.constraints)}",
            "",
            "命题变量:",
        ]
        for pvar in sorted(self.prop_vars):
            lines.append(f"  - {pvar}")
        
        lines.append("")
        lines.append("复合公式变量:")
        for vname in sorted(self.var_map.keys()):
            if vname not in self.prop_vars:
                formula = self.formula_map.get(vname)
                lines.append(f"  - {vname}: {formula}")
        
        return "\n".join(lines)

