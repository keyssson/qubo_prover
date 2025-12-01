"""
证明搜索策略

实现多种证明搜索策略：
- 前向推理（Forward Chaining）
- 后向推理（Backward Chaining）
- 混合搜索
- 神经网络引导搜索

支持配置搜索参数和规则优先级。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Optional, Dict, Callable, Tuple
from enum import Enum
from ..logic.ast import Expr, get_vars
from ..logic.evaluator import entails
from .rules import Rule, RuleResult, RULE_REGISTRY, apply_all_rules
from .proof_state import ProofState, ProofStep, ProofStatus


class SearchStrategy(Enum):
    """搜索策略"""
    FORWARD = "forward"       # 前向推理
    BACKWARD = "backward"     # 后向推理
    BIDIRECTIONAL = "bidirectional"  # 双向搜索


@dataclass
class SearchConfig:
    """
    搜索配置
    """
    strategy: SearchStrategy = SearchStrategy.FORWARD
    max_steps: int = 100              # 最大步数
    max_depth: int = 20               # 最大深度
    max_branching: int = 10           # 最大分支因子
    use_semantic_check: bool = True   # 是否使用语义检查
    rule_priority: Optional[Dict[str, float]] = None  # 规则优先级
    excluded_rules: Set[str] = field(default_factory=set)  # 排除的规则
    
    def get_rule_priority(self, rule_name: str) -> float:
        """获取规则优先级"""
        if self.rule_priority:
            return self.rule_priority.get(rule_name, 1.0)
        return 1.0


@dataclass
class SearchResult:
    """
    搜索结果
    """
    success: bool                     # 是否成功
    proof_state: ProofState           # 最终证明状态
    steps_explored: int               # 探索的步数
    time_ms: float                    # 耗时（毫秒）
    search_path: List[str] = field(default_factory=list)  # 搜索路径
    
    def format_result(self) -> str:
        """格式化结果"""
        lines = [
            "=" * 60,
            "搜索结果",
            "=" * 60,
            f"成功: {'是' if self.success else '否'}",
            f"探索步数: {self.steps_explored}",
            f"耗时: {self.time_ms:.2f} ms",
            "",
        ]
        
        if self.success:
            lines.append(self.proof_state.format_proof())
        
        return "\n".join(lines)


class ProofSearcher:
    """
    证明搜索器
    
    使用配置的策略搜索证明。
    """
    
    def __init__(self, config: Optional[SearchConfig] = None):
        """
        初始化搜索器
        
        Args:
            config: 搜索配置
        """
        self.config = config or SearchConfig()
        self._steps_explored = 0
    
    def search(self, axioms: List[Expr], goal: Expr) -> SearchResult:
        """
        搜索证明
        
        Args:
            axioms: 公理列表
            goal: 目标
            
        Returns:
            搜索结果
        """
        import time
        start_time = time.time()
        
        self._steps_explored = 0
        
        # 创建初始证明状态
        state = ProofState.from_problem(axioms, goal)
        
        # 快速检查：目标是否已经是公理
        if goal in state.knowledge_base:
            state.status = ProofStatus.SUCCESS
            return SearchResult(
                success=True,
                proof_state=state,
                steps_explored=0,
                time_ms=(time.time() - start_time) * 1000
            )
        
        # 语义检查：前提是否蕴涵目标
        if self.config.use_semantic_check:
            if not entails(axioms, goal):
                state.status = ProofStatus.FAILED
                return SearchResult(
                    success=False,
                    proof_state=state,
                    steps_explored=0,
                    time_ms=(time.time() - start_time) * 1000,
                    search_path=["语义检查失败：前提不蕴涵目标"]
                )
        
        # 执行搜索
        if self.config.strategy == SearchStrategy.FORWARD:
            success = self._forward_search(state, goal)
        elif self.config.strategy == SearchStrategy.BACKWARD:
            success = self._backward_search(state, goal)
        else:
            success = self._bidirectional_search(state, goal)
        
        elapsed = (time.time() - start_time) * 1000
        
        return SearchResult(
            success=success,
            proof_state=state,
            steps_explored=self._steps_explored,
            time_ms=elapsed
        )
    
    def _forward_search(self, state: ProofState, goal: Expr) -> bool:
        """
        前向推理搜索
        
        从公理出发，不断应用规则直到达到目标。
        
        Args:
            state: 证明状态
            goal: 目标
            
        Returns:
            是否成功
        """
        no_progress_count = 0
        
        for _ in range(self.config.max_steps):
            self._steps_explored += 1
            
            # 检查是否已完成
            if goal in state.knowledge_base:
                state.status = ProofStatus.SUCCESS
                return True
            
            # 获取所有可能的规则应用
            results = apply_all_rules(
                state.knowledge_base,
                goal=None,  # 不限制目标，探索所有可能
                exclude_rules=self.config.excluded_rules
            )
            
            if not results:
                no_progress_count += 1
                if no_progress_count > 3:
                    break
                continue
            
            # 按优先级排序，目标相关的结果优先
            def score_result(r):
                priority = self.config.get_rule_priority(r.rule_name)
                goal_bonus = 10 if r.conclusion == goal else 0
                return -(priority + goal_bonus)
            
            results.sort(key=score_result)
            
            # 应用所有不冲突的规则
            applied_any = False
            for result in results[:self.config.max_branching]:
                # 跳过已经在知识库中的结论
                if result.conclusion in state.knowledge_base:
                    continue
                
                # 应用规则
                premise_steps = []
                for premise in result.premises:
                    step = state.get_step_by_formula(premise)
                    if step:
                        premise_steps.append(step.step_number)
                
                state.add_step(
                    formula=result.conclusion,
                    rule_name=result.rule_name,
                    premise_steps=premise_steps,
                    justification=result.description
                )
                applied_any = True
                
                # 检查是否达到目标
                if result.conclusion == goal:
                    state.status = ProofStatus.SUCCESS
                    return True
            
            if not applied_any:
                no_progress_count += 1
                if no_progress_count > 3:
                    break
            else:
                no_progress_count = 0
        
        state.status = ProofStatus.FAILED
        return False
    
    def _backward_search(self, state: ProofState, goal: Expr) -> bool:
        """
        后向推理搜索
        
        从目标出发，分解为子目标。
        
        Args:
            state: 证明状态
            goal: 目标
            
        Returns:
            是否成功
        """
        return self._backward_search_recursive(state, goal, set(), 0)
    
    def _backward_search_recursive(self, state: ProofState, goal: Expr, 
                                   visited: Set[Expr], depth: int) -> bool:
        """递归后向搜索"""
        self._steps_explored += 1
        
        if depth > self.config.max_depth:
            return False
        
        if goal in visited:
            return False
        visited.add(goal)
        
        # 目标已在知识库中
        if goal in state.knowledge_base:
            return True
        
        # 尝试找到能产生目标的规则
        for rule in RULE_REGISTRY.values():
            if rule.name in self.config.excluded_rules:
                continue
            
            for result in rule.apply(state.knowledge_base, goal):
                if result.conclusion == goal:
                    # 检查前提是否都满足
                    all_premises_satisfied = True
                    for premise in result.premises:
                        if premise not in state.knowledge_base:
                            # 递归证明前提
                            if not self._backward_search_recursive(state, premise, visited, depth + 1):
                                all_premises_satisfied = False
                                break
                    
                    if all_premises_satisfied:
                        # 添加证明步骤
                        premise_steps = []
                        for premise in result.premises:
                            step = state.get_step_by_formula(premise)
                            if step:
                                premise_steps.append(step.step_number)
                        
                        state.add_step(
                            formula=goal,
                            rule_name=result.rule_name,
                            premise_steps=premise_steps,
                            justification=result.description
                        )
                        return True
        
        return False
    
    def _bidirectional_search(self, state: ProofState, goal: Expr) -> bool:
        """
        双向搜索
        
        同时从公理和目标两端搜索，在中间相遇。
        
        Args:
            state: 证明状态
            goal: 目标
            
        Returns:
            是否成功
        """
        # 简化实现：交替进行前向和后向搜索
        forward_kb = state.knowledge_base.copy()
        backward_targets = {goal}
        
        for _ in range(self.config.max_steps // 2):
            self._steps_explored += 1
            
            # 前向步骤
            forward_results = apply_all_rules(
                forward_kb,
                exclude_rules=self.config.excluded_rules
            )
            
            for result in forward_results[:self.config.max_branching]:
                if result.conclusion not in forward_kb:
                    forward_kb.add(result.conclusion)
                    
                    # 检查是否达到目标
                    if result.conclusion in backward_targets or result.conclusion == goal:
                        # 找到连接点，构建完整证明
                        return self._forward_search(state, goal)
            
            # 后向步骤：分解目标
            new_targets: Set[Expr] = set()
            for target in backward_targets:
                # 分解目标为子目标
                sub_goals = self._decompose_goal(target)
                new_targets.update(sub_goals)
                
                # 检查子目标是否在前向集合中
                if all(sg in forward_kb for sg in sub_goals):
                    return self._forward_search(state, goal)
            
            backward_targets.update(new_targets)
        
        return self._forward_search(state, goal)
    
    def _decompose_goal(self, goal: Expr) -> Set[Expr]:
        """分解目标为子目标"""
        from ..logic.ast import And, Or, Imply, Not
        
        sub_goals: Set[Expr] = set()
        
        if isinstance(goal, And):
            sub_goals.add(goal.left)
            sub_goals.add(goal.right)
        elif isinstance(goal, Imply):
            # P -> Q 的子目标是 P（作为假设）和 Q（作为结论）
            sub_goals.add(goal.right)
        
        return sub_goals


def prove(axioms: List[Expr], goal: Expr, 
          config: Optional[SearchConfig] = None) -> SearchResult:
    """
    便捷证明函数
    
    Args:
        axioms: 公理列表
        goal: 目标
        config: 搜索配置
        
    Returns:
        搜索结果
    """
    searcher = ProofSearcher(config)
    return searcher.search(axioms, goal)


def prove_from_strings(axiom_strs: List[str], goal_str: str,
                       config: Optional[SearchConfig] = None) -> SearchResult:
    """
    从字符串证明
    
    Args:
        axiom_strs: 公理字符串列表
        goal_str: 目标字符串
        config: 搜索配置
        
    Returns:
        搜索结果
    """
    from ..logic.parser import parse
    
    axioms = [parse(s) for s in axiom_strs]
    goal = parse(goal_str)
    
    return prove(axioms, goal, config)

