"""
神经网络层

提供神经网络引导的规则选择功能：
- features: 改进的特征编码
- model: 规则选择器网络
- predictor: 预测接口
"""

from .features import FeatureEncoder, encode_features
from .model import RuleSelectorNetwork, create_model
from .predictor import RulePredictor, predict_rule_weights

__all__ = [
    # Features
    "FeatureEncoder", "encode_features",
    # Model
    "RuleSelectorNetwork", "create_model",
    # Predictor
    "RulePredictor", "predict_rule_weights",
]

