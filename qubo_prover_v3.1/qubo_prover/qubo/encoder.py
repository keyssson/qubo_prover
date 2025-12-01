"""
公式编码器

将逻辑公式编码为 QUBO 变量和约束。

编码策略：
1. 每个命题变量对应一个 QUBO 变量
2. 每个复合公式对应一个辅助 QUBO 变量
3. 结构约束确保逻辑语义的一致性

改进点：
- 支持公式规范化，避免重复编码
- 优化变量命名策略
- 支持增量编码
"""

from __future__ import annotations
from typing import Dict, Tuple, Set, List, Optional, Any
from dataclasses import dataclass, field
from pyqubo import Binary
from ..logic.ast import Expr, Var, Not, And, Or, Imply, Iff, get_vars


@dataclass
class EncodedFormula:
    """
    编码后的公式信息
    """
    var_name: str               # QUBO 变量名
    qubo_var: Binary            # PyQUBO Binary 对象
    formula: Expr               # 原始公式
    is_atomic: bool             # 是否为原子公式
    constraint: Optional[Any]   # 结构约束表达式


class FormulaEncoder:
    """
    公式编码器
    
    将逻辑公式转换为 QUBO 变量和约束。
    
    核心思想：
    1. 命题变量 P -> QUBO 变量 P ∈ {0, 1}
    2. 否定 ~P -> 辅助变量，约束 Not_P + P = 1
    3. 合取 P&Q -> 辅助变量，约束 And = P * Q
    4. 析取 P|Q -> 辅助变量，约束 Or = P + Q - P*Q
    5. 蕴涵 P->Q -> 辅助变量，约束 Imp = 1 - P + P*Q
    """
    
    def __init__(self, prefix: str = ""):
        """
        初始化编码器
        
        Args:
            prefix: 变量名前缀（用于区分不同编码上下文）
        """
        self.prefix = prefix
        self._var_map: Dict[str, Binary] = {}           # 变量名 -> QUBO变量
        self._formula_map: Dict[Expr, EncodedFormula] = {}  # 公式 -> 编码信息
        self._constraints: List[Tuple[str, Any]] = []   # (约束类型, 约束表达式)
        self._prop_vars: Set[str] = set()               # 命题变量集合
        self._counter = 0                               # 辅助变量计数器
    
    def encode(self, formula: Expr, force_new: bool = False) -> EncodedFormula:
        """
        编码公式
        
        Args:
            formula: 逻辑公式
            force_new: 是否强制创建新变量
            
        Returns:
            编码后的公式信息
        """
        # 检查是否已编码
        if not force_new and formula in self._formula_map:
            return self._formula_map[formula]
        
        # 根据公式类型编码
        if isinstance(formula, Var):
            return self._encode_var(formula)
        elif isinstance(formula, Not):
            return self._encode_not(formula)
        elif isinstance(formula, And):
            return self._encode_and(formula)
        elif isinstance(formula, Or):
            return self._encode_or(formula)
        elif isinstance(formula, Imply):
            return self._encode_imply(formula)
        elif isinstance(formula, Iff):
            return self._encode_iff(formula)
        else:
            raise ValueError(f"Unknown formula type: {type(formula)}")
    
    def _encode_var(self, var: Var) -> EncodedFormula:
        """编码命题变量"""
        var_name = f"{self.prefix}{var.name}" if self.prefix else var.name
        
        if var_name not in self._var_map:
            self._var_map[var_name] = Binary(var_name)
            self._prop_vars.add(var_name)
        
        encoded = EncodedFormula(
            var_name=var_name,
            qubo_var=self._var_map[var_name],
            formula=var,
            is_atomic=True,
            constraint=None
        )
        self._formula_map[var] = encoded
        return encoded
    
    def _encode_not(self, formula: Not) -> EncodedFormula:
        """
        编码否定
        
        约束：Not_P = 1 - P
        QUBO 惩罚：(Not_P + P - 1)²
        """
        # 先编码操作数
        operand_enc = self.encode(formula.operand)
        
        # 创建辅助变量
        var_name = self._make_var_name("Not", operand_enc.var_name)
        qubo_var = Binary(var_name)
        self._var_map[var_name] = qubo_var
        
        # 添加约束: Not_P + P = 1
        constraint = (qubo_var + operand_enc.qubo_var - 1) ** 2
        self._constraints.append(("NOT", constraint))
        
        encoded = EncodedFormula(
            var_name=var_name,
            qubo_var=qubo_var,
            formula=formula,
            is_atomic=False,
            constraint=constraint
        )
        self._formula_map[formula] = encoded
        return encoded
    
    def _encode_and(self, formula: And) -> EncodedFormula:
        """
        编码合取
        
        约束：And = P * Q
        QUBO 惩罚：(And - P*Q)²
        但由于 And, P, Q ∈ {0,1}，展开为：
        3*And + P*Q - 2*And*P - 2*And*Q
        """
        left_enc = self.encode(formula.left)
        right_enc = self.encode(formula.right)
        
        var_name = self._make_var_name("And", left_enc.var_name, right_enc.var_name)
        qubo_var = Binary(var_name)
        self._var_map[var_name] = qubo_var
        
        # 线性化约束：And = P * Q
        # 使用标准 QUBO 技术
        P, Q, A = left_enc.qubo_var, right_enc.qubo_var, qubo_var
        constraint = 3*A + P*Q - 2*A*P - 2*A*Q
        self._constraints.append(("AND", constraint))
        
        encoded = EncodedFormula(
            var_name=var_name,
            qubo_var=qubo_var,
            formula=formula,
            is_atomic=False,
            constraint=constraint
        )
        self._formula_map[formula] = encoded
        return encoded
    
    def _encode_or(self, formula: Or) -> EncodedFormula:
        """
        编码析取
        
        约束：Or = P + Q - P*Q
        QUBO 惩罚：(Or - P - Q + P*Q)²
        """
        left_enc = self.encode(formula.left)
        right_enc = self.encode(formula.right)
        
        var_name = self._make_var_name("Or", left_enc.var_name, right_enc.var_name)
        qubo_var = Binary(var_name)
        self._var_map[var_name] = qubo_var
        
        P, Q, O = left_enc.qubo_var, right_enc.qubo_var, qubo_var
        constraint = (O - P - Q + P*Q) ** 2
        self._constraints.append(("OR", constraint))
        
        encoded = EncodedFormula(
            var_name=var_name,
            qubo_var=qubo_var,
            formula=formula,
            is_atomic=False,
            constraint=constraint
        )
        self._formula_map[formula] = encoded
        return encoded
    
    def _encode_imply(self, formula: Imply) -> EncodedFormula:
        """
        编码蕴涵
        
        P -> Q ≡ ~P | Q
        约束：Imp = 1 - P + P*Q
        QUBO 惩罚：(Imp - 1 + P - P*Q)²
        """
        left_enc = self.encode(formula.left)
        right_enc = self.encode(formula.right)
        
        var_name = self._make_var_name("Imp", left_enc.var_name, right_enc.var_name)
        qubo_var = Binary(var_name)
        self._var_map[var_name] = qubo_var
        
        P, Q, I = left_enc.qubo_var, right_enc.qubo_var, qubo_var
        constraint = (I - 1 + P - P*Q) ** 2
        self._constraints.append(("IMPLY", constraint))
        
        encoded = EncodedFormula(
            var_name=var_name,
            qubo_var=qubo_var,
            formula=formula,
            is_atomic=False,
            constraint=constraint
        )
        self._formula_map[formula] = encoded
        return encoded
    
    def _encode_iff(self, formula: Iff) -> EncodedFormula:
        """
        编码等价
        
        P <-> Q ≡ (P -> Q) & (Q -> P) ≡ (P & Q) | (~P & ~Q)
        约束：Iff = 1 - P - Q + 2*P*Q
        """
        left_enc = self.encode(formula.left)
        right_enc = self.encode(formula.right)
        
        var_name = self._make_var_name("Iff", left_enc.var_name, right_enc.var_name)
        qubo_var = Binary(var_name)
        self._var_map[var_name] = qubo_var
        
        P, Q, E = left_enc.qubo_var, right_enc.qubo_var, qubo_var
        # Iff = 1 当且仅当 P = Q
        constraint = (E - 1 + P + Q - 2*P*Q) ** 2
        self._constraints.append(("IFF", constraint))
        
        encoded = EncodedFormula(
            var_name=var_name,
            qubo_var=qubo_var,
            formula=formula,
            is_atomic=False,
            constraint=constraint
        )
        self._formula_map[formula] = encoded
        return encoded
    
    def _make_var_name(self, op: str, *operand_names: str) -> str:
        """生成唯一的变量名"""
        self._counter += 1
        operands = "_".join(self._shorten_name(n) for n in operand_names)
        return f"{self.prefix}{op}_{operands}_{self._counter}"
    
    def _shorten_name(self, name: str, max_len: int = 10) -> str:
        """缩短变量名"""
        # 移除前缀
        if self.prefix and name.startswith(self.prefix):
            name = name[len(self.prefix):]
        # 截断
        if len(name) > max_len:
            return name[:max_len]
        return name
    
    # 公共接口
    
    def get_var(self, name: str) -> Optional[Binary]:
        """根据名称获取 QUBO 变量"""
        return self._var_map.get(name)
    
    def get_encoded(self, formula: Expr) -> Optional[EncodedFormula]:
        """获取公式的编码信息"""
        return self._formula_map.get(formula)
    
    def get_all_vars(self) -> Dict[str, Binary]:
        """获取所有 QUBO 变量"""
        return self._var_map.copy()
    
    def get_prop_vars(self) -> Set[str]:
        """获取所有命题变量"""
        return self._prop_vars.copy()
    
    def get_constraints(self) -> List[Tuple[str, Any]]:
        """获取所有结构约束"""
        return self._constraints.copy()
    
    def get_constraint_expression(self, weight: float = 1.0) -> Any:
        """获取所有约束的加权和"""
        if not self._constraints:
            return 0
        
        total = weight * self._constraints[0][1]
        for _, constraint in self._constraints[1:]:
            total = total + weight * constraint
        return total
    
    def summary(self) -> str:
        """生成编码摘要"""
        lines = [
            "公式编码器摘要",
            "-" * 40,
            f"总变量数: {len(self._var_map)}",
            f"命题变量数: {len(self._prop_vars)}",
            f"辅助变量数: {len(self._var_map) - len(self._prop_vars)}",
            f"结构约束数: {len(self._constraints)}",
            "",
            "命题变量:",
        ]
        for pv in sorted(self._prop_vars):
            lines.append(f"  - {pv}")
        
        lines.append("")
        lines.append("编码的公式:")
        for formula, enc in self._formula_map.items():
            lines.append(f"  - {enc.var_name}: {formula}")
        
        return "\n".join(lines)


def encode_formula(formula: Expr, prefix: str = "") -> Tuple[FormulaEncoder, EncodedFormula]:
    """
    便捷函数：编码单个公式
    
    Args:
        formula: 逻辑公式
        prefix: 变量名前缀
        
    Returns:
        (编码器, 编码信息)
    """
    encoder = FormulaEncoder(prefix)
    encoded = encoder.encode(formula)
    return encoder, encoded


def encode_formulas(formulas: List[Expr], prefix: str = "") -> Tuple[FormulaEncoder, List[EncodedFormula]]:
    """
    便捷函数：编码多个公式
    
    Args:
        formulas: 公式列表
        prefix: 变量名前缀
        
    Returns:
        (编码器, 编码信息列表)
    """
    encoder = FormulaEncoder(prefix)
    encoded_list = [encoder.encode(f) for f in formulas]
    return encoder, encoded_list

