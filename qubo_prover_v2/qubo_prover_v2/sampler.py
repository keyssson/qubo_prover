"""
采样后端
支持多种模拟退火和量子退火采样器
"""

from typing import Any


class SamplerBackend:
    """采样器基类"""
    
    def sample_bqm(self, bqm: Any, num_reads: int):
        """
        对 BQM 进行采样
        
        Args:
            bqm: Binary Quadratic Model
            num_reads: 采样次数
            
        Returns:
            采样结果
        """
        raise NotImplementedError
    
    def name(self) -> str:
        """返回采样器名称"""
        raise NotImplementedError


class NealBackend(SamplerBackend):
    """
    Neal 后端（D-Wave Ocean SDK 的经典模拟退火）
    """
    
    def __init__(self):
        try:
            import neal
            self._neal = neal
        except ImportError:
            raise RuntimeError(
                "neal is not installed. "
                "Please install it with: pip install dwave-neal"
            )
    
    def sample_bqm(self, bqm: Any, num_reads: int):
        sampler = self._neal.SimulatedAnnealingSampler()
        return sampler.sample(bqm, num_reads=num_reads)
    
    def name(self) -> str:
        return "neal"


class OpenJijBackend(SamplerBackend):
    """
    OpenJij 后端（日本量子退火模拟器）
    """
    
    def __init__(self):
        try:
            import openjij as oj
            self._oj = oj
        except ImportError:
            raise RuntimeError(
                "openjij is not installed. "
                "Please install it with: pip install openjij"
            )
    
    def sample_bqm(self, bqm: Any, num_reads: int):
        # 转换为 QUBO 格式
        Q = bqm.to_qubo()[0]
        sampler = self._oj.SASampler()
        return sampler.sample_qubo(Q, num_reads=num_reads)
    
    def name(self) -> str:
        return "openjij"


def make_backend(name: str) -> SamplerBackend:
    """
    创建采样后端
    
    Args:
        name: 后端名称 ("neal" 或 "openjij")
        
    Returns:
        采样器实例
        
    Raises:
        ValueError: 未知的后端名称
    """
    if name == "neal":
        return NealBackend()
    elif name == "openjij":
        return OpenJijBackend()
    else:
        raise ValueError(
            f"Unknown backend: {name}. "
            f"Available backends: neal, openjij"
        )

