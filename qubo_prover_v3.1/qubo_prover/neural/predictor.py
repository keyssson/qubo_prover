"""
规则预测器

封装神经网络预测接口，提供便捷的规则权重预测功能。
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np
from .features import FeatureEncoder, encode_features
from .model import RuleSelectorNetwork, create_model, RULE_NAMES


class RulePredictor:
    """
    规则预测器
    
    使用神经网络预测推理规则的权重。
    """
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 use_neural: bool = True):
        """
        初始化预测器
        
        Args:
            model_path: 模型路径
            use_neural: 是否使用神经网络
        """
        self.use_neural = use_neural
        self.feature_encoder = FeatureEncoder()
        self.model: Optional[RuleSelectorNetwork] = None
        
        if use_neural:
            self._load_model(model_path)
    
    def _load_model(self, model_path: Optional[str]):
        """加载模型"""
        if model_path:
            path = Path(model_path)
            if path.exists():
                try:
                    self.model = RuleSelectorNetwork.load(str(path))
                    print(f"✓ 已加载神经网络模型: {model_path}")
                    return
                except Exception as e:
                    print(f"✗ 模型加载失败: {e}")
        
        # 使用默认模型（未训练）
        self.model = create_model(
            input_size=self.feature_encoder.get_feature_dim()
        )
        print("ℹ 使用未训练的神经网络（随机权重）")
    
    def predict(self, axioms: List[str], goal: str) -> Dict[str, float]:
        """
        预测规则权重
        
        Args:
            axioms: 公理列表
            goal: 目标
            
        Returns:
            规则权重字典 {rule_name: weight}
        """
        if not self.use_neural or self.model is None:
            # 返回均匀权重
            return {name: 1.0 for name in RULE_NAMES}
        
        # 编码特征
        features = self.feature_encoder.encode(axioms, goal)
        
        # 预测
        weights = self.model.predict(features)
        
        return weights
    
    def predict_top_k(self, axioms: List[str], goal: str, 
                      k: int = 3) -> List[Tuple[str, float]]:
        """
        预测 Top-K 规则
        
        Args:
            axioms: 公理列表
            goal: 目标
            k: 返回的规则数量
            
        Returns:
            [(规则名, 权重), ...] 按权重降序排列
        """
        weights = self.predict(axioms, goal)
        sorted_rules = sorted(weights.items(), key=lambda x: -x[1])
        return sorted_rules[:k]
    
    def get_penalty_factors(self, axioms: List[str], goal: str,
                            base_penalty: float = 10.0) -> Dict[str, float]:
        """
        获取规则惩罚因子
        
        权重高 -> 惩罚低 -> 更容易使用
        
        Args:
            axioms: 公理列表
            goal: 目标
            base_penalty: 基础惩罚
            
        Returns:
            规则惩罚因子字典
        """
        weights = self.predict(axioms, goal)
        
        penalties = {}
        for rule_name, weight in weights.items():
            # penalty = base * (2 - weight)
            # weight=1.0 -> penalty=base
            # weight=0.0 -> penalty=2*base
            penalties[rule_name] = base_penalty * (2.0 - weight)
        
        return penalties
    
    def explain_prediction(self, axioms: List[str], goal: str) -> str:
        """
        解释预测结果
        
        Args:
            axioms: 公理列表
            goal: 目标
            
        Returns:
            解释字符串
        """
        weights = self.predict(axioms, goal)
        features = self.feature_encoder.encode(axioms, goal)
        
        lines = [
            "=" * 50,
            "规则权重预测",
            "=" * 50,
            "",
            "输入:",
            f"  公理: {axioms}",
            f"  目标: {goal}",
            "",
            "关键特征:",
        ]
        
        # 显示重要特征
        feature_names = self.feature_encoder.get_feature_names()
        important_indices = [0, 1, 18, 19, 20, 25]  # 选择重要特征
        for idx in important_indices:
            if idx < len(feature_names):
                lines.append(f"  - {feature_names[idx]}: {features[idx]:.2f}")
        
        lines.extend([
            "",
            "预测的规则权重 (按重要性排序):",
        ])
        
        for rule_name, weight in sorted(weights.items(), key=lambda x: -x[1]):
            bar = "█" * int(weight * 20)
            lines.append(f"  {rule_name:20s}: {weight:.3f} {bar}")
        
        lines.extend(["", "=" * 50])
        
        return "\n".join(lines)


def predict_rule_weights(axioms: List[str], goal: str,
                         model_path: Optional[str] = None) -> Dict[str, float]:
    """
    便捷函数：预测规则权重
    
    Args:
        axioms: 公理列表
        goal: 目标
        model_path: 模型路径
        
    Returns:
        规则权重字典
    """
    predictor = RulePredictor(model_path=model_path)
    return predictor.predict(axioms, goal)


def get_default_weights() -> Dict[str, float]:
    """获取默认权重（基于启发式）"""
    return {
        "modus_ponens": 0.95,      # 最常用
        "modus_tollens": 0.85,     # 常用
        "and_elim_left": 0.80,
        "and_elim_right": 0.80,
        "and_intro": 0.70,
        "or_intro_left": 0.60,
        "or_intro_right": 0.60,
        "or_elim": 0.75,
        "not_intro": 0.50,
        "double_neg_elim": 0.65,
        "imply_intro": 0.55,
        "resolution": 0.70,
    }

