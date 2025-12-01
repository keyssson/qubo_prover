"""
特征编码器

将逻辑公式转换为神经网络可以理解的特征向量。

改进点（相比 V3）：
1. 扩展特征维度（12 -> 32+）
2. 公式结构特征
3. 模式匹配特征
4. 目标相关特征
5. 变量共现特征
"""

from __future__ import annotations
from typing import List, Set, Dict, Tuple
import numpy as np
from ..logic.ast import Expr, Var, Not, And, Or, Imply, Iff, get_vars, depth, size
from ..logic.parser import parse


class FeatureEncoder:
    """
    特征编码器
    
    将证明问题编码为固定维度的特征向量。
    """
    
    # 特征名称列表
    FEATURE_NAMES = [
        # 基础统计 (0-4)
        "num_axioms",               # 公理数量
        "num_variables",            # 变量数量
        "total_formula_size",       # 公式总大小
        "max_formula_depth",        # 最大深度
        "avg_formula_depth",        # 平均深度
        
        # 公理运算符统计 (5-9)
        "axiom_has_imply",          # 公理包含蕴涵
        "axiom_has_not",            # 公理包含否定
        "axiom_has_and",            # 公理包含合取
        "axiom_has_or",             # 公理包含析取
        "axiom_has_iff",            # 公理包含等价
        
        # 目标运算符统计 (10-14)
        "goal_has_imply",           # 目标包含蕴涵
        "goal_has_not",             # 目标包含否定
        "goal_has_and",             # 目标包含合取
        "goal_has_or",              # 目标包含析取
        "goal_has_iff",             # 目标包含等价
        
        # 目标特征 (15-17)
        "goal_size",                # 目标大小
        "goal_depth",               # 目标深度
        "goal_is_atomic",           # 目标是否为原子
        
        # 模式匹配特征 (18-25)
        "mp_potential",             # Modus Ponens 潜力
        "mt_potential",             # Modus Tollens 潜力
        "and_elim_potential",       # And-Elim 潜力
        "or_intro_potential",       # Or-Intro 潜力
        "double_neg_potential",     # 双重否定潜力
        "chain_potential",          # 推理链潜力
        "contradiction_potential",  # 矛盾潜力
        "goal_in_axioms",           # 目标是否在公理中
        
        # 变量关系特征 (26-31)
        "var_overlap_ratio",        # 变量重叠比例
        "goal_var_coverage",        # 目标变量覆盖率
        "avg_var_frequency",        # 平均变量频率
        "max_var_frequency",        # 最大变量频率
        "isolated_var_count",       # 孤立变量数
        "shared_var_count",         # 共享变量数
    ]
    
    def __init__(self):
        self.feature_dim = len(self.FEATURE_NAMES)
    
    def encode(self, axioms: List[str], goal: str) -> np.ndarray:
        """
        编码证明问题为特征向量
        
        Args:
            axioms: 公理字符串列表
            goal: 目标字符串
            
        Returns:
            特征向量 (feature_dim,)
        """
        # 解析公式
        axiom_exprs = [parse(ax) for ax in axioms]
        goal_expr = parse(goal)
        
        features = np.zeros(self.feature_dim, dtype=np.float32)
        
        # 基础统计 (0-4)
        features[0] = len(axioms)
        all_vars = set()
        for ax in axiom_exprs:
            all_vars |= get_vars(ax)
        all_vars |= get_vars(goal_expr)
        features[1] = len(all_vars)
        
        total_size = sum(size(ax) for ax in axiom_exprs) + size(goal_expr)
        features[2] = total_size
        
        depths = [depth(ax) for ax in axiom_exprs] + [depth(goal_expr)]
        features[3] = max(depths) if depths else 0
        features[4] = np.mean(depths) if depths else 0
        
        # 公理运算符统计 (5-9)
        axiom_ops = self._count_operators(axiom_exprs)
        features[5] = 1 if axiom_ops["imply"] > 0 else 0
        features[6] = 1 if axiom_ops["not"] > 0 else 0
        features[7] = 1 if axiom_ops["and"] > 0 else 0
        features[8] = 1 if axiom_ops["or"] > 0 else 0
        features[9] = 1 if axiom_ops["iff"] > 0 else 0
        
        # 目标运算符统计 (10-14)
        goal_ops = self._count_operators([goal_expr])
        features[10] = 1 if goal_ops["imply"] > 0 else 0
        features[11] = 1 if goal_ops["not"] > 0 else 0
        features[12] = 1 if goal_ops["and"] > 0 else 0
        features[13] = 1 if goal_ops["or"] > 0 else 0
        features[14] = 1 if goal_ops["iff"] > 0 else 0
        
        # 目标特征 (15-17)
        features[15] = size(goal_expr)
        features[16] = depth(goal_expr)
        features[17] = 1 if isinstance(goal_expr, Var) else 0
        
        # 模式匹配特征 (18-25)
        features[18] = self._count_mp_potential(axiom_exprs, goal_expr)
        features[19] = self._count_mt_potential(axiom_exprs, goal_expr)
        features[20] = self._count_and_elim_potential(axiom_exprs)
        features[21] = self._count_or_intro_potential(axiom_exprs, goal_expr)
        features[22] = self._count_double_neg_potential(axiom_exprs)
        features[23] = self._count_chain_potential(axiom_exprs)
        features[24] = self._count_contradiction_potential(axiom_exprs)
        features[25] = 1 if goal_expr in axiom_exprs else 0
        
        # 变量关系特征 (26-31)
        axiom_vars = set()
        for ax in axiom_exprs:
            axiom_vars |= get_vars(ax)
        goal_vars = get_vars(goal_expr)
        
        if axiom_vars | goal_vars:
            features[26] = len(axiom_vars & goal_vars) / len(axiom_vars | goal_vars)
        if goal_vars:
            features[27] = len(axiom_vars & goal_vars) / len(goal_vars)
        
        var_freq = self._compute_var_frequency(axiom_exprs + [goal_expr])
        if var_freq:
            features[28] = np.mean(list(var_freq.values()))
            features[29] = max(var_freq.values())
            features[30] = sum(1 for f in var_freq.values() if f == 1)
            features[31] = sum(1 for f in var_freq.values() if f > 1)
        
        return features
    
    def _count_operators(self, exprs: List[Expr]) -> Dict[str, int]:
        """统计运算符数量"""
        counts = {"imply": 0, "not": 0, "and": 0, "or": 0, "iff": 0}
        
        for expr in exprs:
            for sub in expr.subformulas():
                if isinstance(sub, Imply):
                    counts["imply"] += 1
                elif isinstance(sub, Not):
                    counts["not"] += 1
                elif isinstance(sub, And):
                    counts["and"] += 1
                elif isinstance(sub, Or):
                    counts["or"] += 1
                elif isinstance(sub, Iff):
                    counts["iff"] += 1
        
        return counts
    
    def _count_mp_potential(self, axioms: List[Expr], goal: Expr) -> float:
        """计算 Modus Ponens 潜力"""
        count = 0
        for ax in axioms:
            if isinstance(ax, Imply):
                # 检查前件是否在公理中
                if ax.left in axioms:
                    count += 1
                    # 额外奖励：后件是目标
                    if ax.right == goal:
                        count += 2
        return min(count / max(len(axioms), 1), 1.0)
    
    def _count_mt_potential(self, axioms: List[Expr], goal: Expr) -> float:
        """计算 Modus Tollens 潜力"""
        count = 0
        for ax in axioms:
            if isinstance(ax, Imply):
                # 检查后件的否定是否在公理中
                neg_right = Not(ax.right)
                if neg_right in axioms:
                    count += 1
                    # 检查目标是否是前件的否定
                    if goal == Not(ax.left):
                        count += 2
        return min(count / max(len(axioms), 1), 1.0)
    
    def _count_and_elim_potential(self, axioms: List[Expr]) -> float:
        """计算 And-Elim 潜力"""
        count = sum(1 for ax in axioms if isinstance(ax, And))
        return min(count / max(len(axioms), 1), 1.0)
    
    def _count_or_intro_potential(self, axioms: List[Expr], goal: Expr) -> float:
        """计算 Or-Intro 潜力"""
        if isinstance(goal, Or):
            # 检查目标的某个分支是否在公理中
            if goal.left in axioms or goal.right in axioms:
                return 1.0
        return 0.0
    
    def _count_double_neg_potential(self, axioms: List[Expr]) -> float:
        """计算双重否定消除潜力"""
        count = 0
        for ax in axioms:
            if isinstance(ax, Not) and isinstance(ax.operand, Not):
                count += 1
        return min(count / max(len(axioms), 1), 1.0)
    
    def _count_chain_potential(self, axioms: List[Expr]) -> float:
        """计算推理链潜力"""
        implications = [ax for ax in axioms if isinstance(ax, Imply)]
        if len(implications) < 2:
            return 0.0
        
        # 检查是否存在链式蕴涵
        chain_count = 0
        for imp1 in implications:
            for imp2 in implications:
                if imp1.right == imp2.left:
                    chain_count += 1
        
        return min(chain_count / max(len(implications), 1), 1.0)
    
    def _count_contradiction_potential(self, axioms: List[Expr]) -> float:
        """计算矛盾潜力"""
        for ax in axioms:
            neg_ax = Not(ax) if not isinstance(ax, Not) else ax.operand
            if neg_ax in axioms:
                return 1.0
        return 0.0
    
    def _compute_var_frequency(self, exprs: List[Expr]) -> Dict[str, int]:
        """计算变量频率"""
        freq: Dict[str, int] = {}
        for expr in exprs:
            for var in get_vars(expr):
                freq[var] = freq.get(var, 0) + 1
        return freq
    
    def get_feature_names(self) -> List[str]:
        """获取特征名称"""
        return self.FEATURE_NAMES.copy()
    
    def get_feature_dim(self) -> int:
        """获取特征维度"""
        return self.feature_dim


def encode_features(axioms: List[str], goal: str) -> np.ndarray:
    """
    便捷函数：编码特征
    
    Args:
        axioms: 公理列表
        goal: 目标
        
    Returns:
        特征向量
    """
    encoder = FeatureEncoder()
    return encoder.encode(axioms, goal)

