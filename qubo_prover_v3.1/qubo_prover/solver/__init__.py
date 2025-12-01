"""
求解器层

提供 QUBO 问题的求解和结果解码功能：
- backends: 采样后端（模拟退火等）
- decoder: 结果解码
- verifier: 证明验证
"""

from .backends import SamplerBackend, NealBackend, make_backend
from .decoder import decode_result, extract_assignment, verify_proof
from .verifier import ProofVerifier, VerificationResult

__all__ = [
    # Backends
    "SamplerBackend", "NealBackend", "make_backend",
    # Decoder
    "decode_result", "extract_assignment", "verify_proof",
    # Verifier
    "ProofVerifier", "VerificationResult",
]

