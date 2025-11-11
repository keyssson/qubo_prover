"""
基础测试脚本 - 不需要额外依赖

测试特征编码器和数据生成器的基本功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from qubo_prover_v3.neural.feature_encoder import FeatureEncoder


def test_feature_encoder():
    """测试特征编码器"""
    print("=" * 60)
    print("测试特征编码器")
    print("=" * 60)
    
    encoder = FeatureEncoder()
    
    # 测试案例1：Modus Ponens
    print("\n案例1: Modus Ponens")
    axioms1 = ["P", "P->Q"]
    goal1 = "Q"
    features1 = encoder.encode(axioms1, goal1)
    
    print(f"  公理: {axioms1}")
    print(f"  目标: {goal1}")
    print(f"  特征维度: {features1.shape}")
    print(f"  特征值: {features1}")
    print(f"  特征名称: {encoder.get_feature_names()}")
    
    # 验证
    assert features1.shape == (12,), f"特征维度错误: {features1.shape}"
    assert features1[0] == 2, f"公理数量错误: {features1[0]}"
    assert features1[1] == 1, f"蕴涵检测错误: {features1[1]}"
    print("  ✓ 测试通过")
    
    # 测试案例2：Modus Tollens
    print("\n案例2: Modus Tollens")
    axioms2 = ["P->Q", "~Q"]
    goal2 = "~P"
    features2 = encoder.encode(axioms2, goal2)
    
    print(f"  公理: {axioms2}")
    print(f"  目标: {goal2}")
    print(f"  特征值: {features2}")
    
    assert features2[0] == 2, "公理数量应该是2"
    assert features2[1] == 1, "应该包含蕴涵"
    assert features2[2] == 1, "应该包含否定"
    assert features2[6] == 1, "目标应该包含否定"
    print("  ✓ 测试通过")
    
    # 测试案例3：复杂公式
    print("\n案例3: 复杂公式")
    axioms3 = ["P&Q", "(P&Q)->R", "~R"]
    goal3 = "~P|~Q"
    features3 = encoder.encode(axioms3, goal3)
    
    print(f"  公理: {axioms3}")
    print(f"  目标: {goal3}")
    print(f"  特征值: {features3}")
    
    assert features3[0] == 3, "公理数量应该是3"
    assert features3[1] == 1, "应该包含蕴涵"
    assert features3[2] == 1, "应该包含否定"
    assert features3[3] == 1, "应该包含合取"
    assert features3[8] == 1, "目标应该包含析取"
    print("  ✓ 测试通过")
    
    print("\n" + "=" * 60)
    print("✓ 所有特征编码器测试通过！")
    print("=" * 60)


def test_data_generator():
    """测试数据生成器（简化版，不使用tqdm）"""
    print("\n" + "=" * 60)
    print("测试数据生成器")
    print("=" * 60)
    
    from qubo_prover_v3.data.generator import TrainingDataGenerator
    
    generator = TrainingDataGenerator(seed=42)
    
    # 生成几个示例
    print("\n生成5个示例问题:")
    for i in range(5):
        problem = generator.generate_problem()
        print(f"\n问题 {i+1} ({problem['template_name']}):")
        print(f"  公理: {problem['axioms']}")
        print(f"  目标: {problem['goal']}")
        print(f"  有用的规则: {problem['useful_rules']}")
        
        # 验证
        assert 'axioms' in problem, "缺少公理"
        assert 'goal' in problem, "缺少目标"
        assert 'useful_rules' in problem, "缺少有用规则"
        assert len(problem['axioms']) > 0, "公理不能为空"
        assert len(problem['goal']) > 0, "目标不能为空"
    
    print("\n" + "=" * 60)
    print("✓ 数据生成器测试通过！")
    print("=" * 60)


def test_integration():
    """集成测试"""
    print("\n" + "=" * 60)
    print("集成测试：特征编码器 + 数据生成器")
    print("=" * 60)
    
    from qubo_prover_v3.data.generator import TrainingDataGenerator
    
    encoder = FeatureEncoder()
    generator = TrainingDataGenerator(seed=42)
    
    # 生成问题并编码
    print("\n生成问题并编码特征:")
    for i in range(3):
        problem = generator.generate_problem()
        features = encoder.encode(problem['axioms'], problem['goal'])
        
        print(f"\n问题 {i+1}:")
        print(f"  模板: {problem['template_name']}")
        print(f"  公理: {problem['axioms']}")
        print(f"  目标: {problem['goal']}")
        print(f"  特征: {features}")
        print(f"  有用规则: {problem['useful_rules']}")
        
        # 验证
        assert features.shape == (12,), "特征维度错误"
        assert features[0] == len(problem['axioms']), "公理数量特征错误"
    
    print("\n" + "=" * 60)
    print("✓ 集成测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_feature_encoder()
        test_data_generator()
        test_integration()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        print("\n下一步:")
        print("  1. 安装 PyTorch: pip install torch")
        print("  2. 安装其他依赖: pip install -r requirements.txt")
        print("  3. 生成训练数据: python scripts/generate_data.py")
        print("  4. 训练模型: python scripts/train_model.py")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

