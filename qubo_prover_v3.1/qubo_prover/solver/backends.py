"""
采样后端

支持多种 QUBO 求解后端：
- Neal: D-Wave 的模拟退火
- OpenJij: 日本量子退火模拟器
- 未来支持: D-Wave 真实量子硬件
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from dataclasses import dataclass


@dataclass
class SampleResult:
    """
    采样结果
    """
    samples: list                # 样本列表
    energies: list              # 能量列表
    num_reads: int              # 采样次数
    timing: Optional[Dict] = None  # 计时信息
    info: Optional[Dict] = None    # 其他信息


class SamplerBackend(ABC):
    """采样后端基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """后端名称"""
        pass
    
    @abstractmethod
    def sample(self, bqm: Any, num_reads: int = 100, **kwargs) -> SampleResult:
        """
        对 BQM 进行采样
        
        Args:
            bqm: Binary Quadratic Model
            num_reads: 采样次数
            **kwargs: 其他参数
            
        Returns:
            采样结果
        """
        pass
    
    def is_available(self) -> bool:
        """检查后端是否可用"""
        return True


class NealBackend(SamplerBackend):
    """
    Neal 后端
    
    使用 D-Wave Ocean SDK 的模拟退火采样器。
    """
    
    def __init__(self, 
                 num_sweeps: int = 1000,
                 beta_range: Optional[tuple] = None,
                 seed: Optional[int] = None):
        """
        初始化 Neal 后端
        
        Args:
            num_sweeps: 每次采样的扫描次数
            beta_range: 温度范围 (beta_min, beta_max)
            seed: 随机种子
        """
        self.num_sweeps = num_sweeps
        self.beta_range = beta_range
        self.seed = seed
        self._sampler = None
    
    @property
    def name(self) -> str:
        return "neal"
    
    def _get_sampler(self):
        """延迟加载采样器"""
        if self._sampler is None:
            try:
                import neal
                self._sampler = neal.SimulatedAnnealingSampler()
            except ImportError:
                raise RuntimeError(
                    "neal 未安装。请运行: pip install dwave-neal"
                )
        return self._sampler
    
    def sample(self, bqm: Any, num_reads: int = 100, **kwargs) -> SampleResult:
        """模拟退火采样"""
        sampler = self._get_sampler()
        
        # 合并参数
        params = {
            "num_reads": num_reads,
            "num_sweeps": kwargs.get("num_sweeps", self.num_sweeps),
        }
        if self.beta_range:
            params["beta_range"] = self.beta_range
        if self.seed is not None:
            params["seed"] = self.seed
        
        # 执行采样
        sampleset = sampler.sample(bqm, **params)
        
        # 转换结果
        samples = []
        energies = []
        
        for sample, energy in zip(sampleset.record.sample, sampleset.record.energy):
            assignment = {
                v: int(sample[idx])
                for idx, v in enumerate(sampleset.variables)
            }
            samples.append(assignment)
            energies.append(float(energy))
        
        return SampleResult(
            samples=samples,
            energies=energies,
            num_reads=num_reads,
            timing=dict(sampleset.info.get("timing", {})) if hasattr(sampleset, "info") else None,
            info={"backend": self.name}
        )
    
    def is_available(self) -> bool:
        try:
            import neal
            return True
        except ImportError:
            return False


class OpenJijBackend(SamplerBackend):
    """
    OpenJij 后端
    
    使用 OpenJij 的模拟退火采样器。
    """
    
    def __init__(self,
                 num_sweeps: int = 1000,
                 beta_min: float = 0.1,
                 beta_max: float = 10.0):
        """
        初始化 OpenJij 后端
        
        Args:
            num_sweeps: 扫描次数
            beta_min: 最小 beta
            beta_max: 最大 beta
        """
        self.num_sweeps = num_sweeps
        self.beta_min = beta_min
        self.beta_max = beta_max
        self._sampler = None
    
    @property
    def name(self) -> str:
        return "openjij"
    
    def _get_sampler(self):
        """延迟加载采样器"""
        if self._sampler is None:
            try:
                import openjij as oj
                self._sampler = oj.SASampler()
            except ImportError:
                raise RuntimeError(
                    "openjij 未安装。请运行: pip install openjij"
                )
        return self._sampler
    
    def sample(self, bqm: Any, num_reads: int = 100, **kwargs) -> SampleResult:
        """模拟退火采样"""
        sampler = self._get_sampler()
        
        # 转换为 QUBO 格式
        Q = bqm.to_qubo()[0]
        
        # 执行采样
        response = sampler.sample_qubo(
            Q,
            num_reads=num_reads,
            num_sweeps=kwargs.get("num_sweeps", self.num_sweeps),
        )
        
        # 转换结果
        samples = []
        energies = []
        
        states = getattr(response, "states", None)
        energy_list = getattr(response, "energies", None)
        
        if states is not None and energy_list is not None:
            for st, en in zip(states, energy_list):
                if isinstance(st, dict):
                    samples.append({str(k): int(v) for k, v in st.items()})
                    energies.append(float(en))
        
        return SampleResult(
            samples=samples,
            energies=energies,
            num_reads=num_reads,
            info={"backend": self.name}
        )
    
    def is_available(self) -> bool:
        try:
            import openjij
            return True
        except ImportError:
            return False


class ExactBackend(SamplerBackend):
    """
    精确求解后端
    
    用于小规模问题的精确求解（穷举）。
    """
    
    @property
    def name(self) -> str:
        return "exact"
    
    def sample(self, bqm: Any, num_reads: int = 1, **kwargs) -> SampleResult:
        """精确求解"""
        try:
            import dimod
            sampler = dimod.ExactSolver()
            sampleset = sampler.sample(bqm)
            
            samples = []
            energies = []
            
            # 只返回最优解
            best = sampleset.first
            samples.append(dict(best.sample))
            energies.append(float(best.energy))
            
            return SampleResult(
                samples=samples,
                energies=energies,
                num_reads=1,
                info={"backend": self.name, "is_exact": True}
            )
        except ImportError:
            raise RuntimeError("dimod 未安装")
    
    def is_available(self) -> bool:
        try:
            import dimod
            return True
        except ImportError:
            return False


# 后端注册表
_BACKENDS: Dict[str, type] = {
    "neal": NealBackend,
    "openjij": OpenJijBackend,
    "exact": ExactBackend,
}


def make_backend(name: str, **kwargs) -> SamplerBackend:
    """
    创建采样后端
    
    Args:
        name: 后端名称
        **kwargs: 后端参数
        
    Returns:
        采样后端实例
        
    Raises:
        ValueError: 未知的后端名称
    """
    if name not in _BACKENDS:
        available = ", ".join(_BACKENDS.keys())
        raise ValueError(
            f"未知的后端: {name}。可用后端: {available}"
        )
    
    backend_class = _BACKENDS[name]
    return backend_class(**kwargs)


def list_backends() -> list:
    """列出所有可用后端"""
    result = []
    for name, cls in _BACKENDS.items():
        backend = cls()
        result.append({
            "name": name,
            "available": backend.is_available()
        })
    return result

