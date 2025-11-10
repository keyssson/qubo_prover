"""
特征编码器 - 将逻辑公式转换为神经网络可以理解的特征向量

功能：
1. 提取公理和目标的结构特征
2. 统计逻辑运算符的使用情况
3. 分析变量数量和复杂度
"""

import re
from typing import List, Dict
import numpy as np


class FeatureEncoder:
    """特征编码器"""
    
    def __init__(self):
        """初始化特征编码器"""
        self.feature_names = [
            "num_axioms",              # 公理数量
            "has_implication",         # 是否包含蕴涵（->）
            "has_negation",            # 是否包含否定（~）
            "has_conjunction",         # 是否包含合取（&）
            "has_disjunction",         # 是否包含析取（|）
            "goal_has_implication",    # 目标是否包含蕴涵
            "goal_has_negation",       # 目标是否包含否定
            "goal_has_conjunction",    # 目标是否包含合取
            "goal_has_disjunction",    # 目标是否包含析取
            "num_variables",           # 变量数量
            "avg_formula_length",      # 平均公式长度
            "max_formula_depth",       # 最大公式深度（嵌套层数）
        ]
        self.feature_dim = len(self.feature_names)
    
    def encode(self, axioms: List[str], goal: str) -> np.ndarray:
        """
        将公理和目标编码为特征向量
        
        Args:
            axioms: 公理列表，例如 ["P", "P->Q"]
            goal: 目标，例如 "Q"
        
        Returns:
            特征向量，形状为 (feature_dim,)
        """
        features = []
        
        # 特征1：公理数量
        features.append(len(axioms))
        
        # 特征2-5：公理中的逻辑运算符
        axioms_text = " ".join(axioms)
        features.append(1 if "->" in axioms_text else 0)
        features.append(1 if "~" in axioms_text else 0)
        features.append(1 if "&" in axioms_text else 0)
        features.append(1 if "|" in axioms_text else 0)
        
        # 特征6-9：目标中的逻辑运算符
        features.append(1 if "->" in goal else 0)
        features.append(1 if "~" in goal else 0)
        features.append(1 if "&" in goal else 0)
        features.append(1 if "|" in goal else 0)
        
        # 特征10：变量数量
        all_formulas = axioms + [goal]
        variables = self._extract_variables(all_formulas)
        features.append(len(variables))
        
        # 特征11：平均公式长度
        avg_length = np.mean([len(f) for f in all_formulas])
        features.append(avg_length)
        
        # 特征12：最大公式深度
        max_depth = max([self._calculate_depth(f) for f in all_formulas])
        features.append(max_depth)
        
        return np.array(features, dtype=np.float32)
    
    def _extract_variables(self, formulas: List[str]) -> set:
        """
        提取所有变量
        
        Args:
            formulas: 公式列表
        
        Returns:
            变量集合
        """
        variables = set()
        for formula in formulas:
            # 匹配大写字母（变量）
            vars_in_formula = re.findall(r'[A-Z]', formula)
            variables.update(vars_in_formula)
        return variables
    
    def _calculate_depth(self, formula: str) -> int:
        """
        计算公式的嵌套深度
        
        Args:
            formula: 公式字符串
        
        Returns:
            嵌套深度
        """
        max_depth = 0
        current_depth = 0
        
        for char in formula:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth -= 1
        
        return max_depth
    
    def get_feature_names(self) -> List[str]:
        """获取特征名称列表"""
        return self.feature_names.copy()
    
    def get_feature_dim(self) -> int:
        """获取特征维度"""
        return self.feature_dim


# 示例用法
if __name__ == "__main__":
    encoder = FeatureEncoder()
    
    # 测试案例1：Modus Ponens
    axioms1 = ["P", "P->Q"]
    goal1 = "Q"
    features1 = encoder.encode(axioms1, goal1)
    
    print("案例1: Modus Ponens")
    print(f"公理: {axioms1}")
    print(f"目标: {goal1}")
    print(f"特征向量: {features1}")
    print(f"特征名称: {encoder.get_feature_names()}")
    print()
    
    # 测试案例2：复杂公式
    axioms2 = ["P&Q", "(P&Q)->R", "~R"]
    goal2 = "~P|~Q"
    features2 = encoder.encode(axioms2, goal2)
    
    print("案例2: 复杂公式")
    print(f"公理: {axioms2}")
    print(f"目标: {goal2}")
    print(f"特征向量: {features2}")

