from typing import Any, Dict, Optional


class SamplerBackend:
	def sample_bqm(self, bqm: Any, num_reads: int):
		raise NotImplementedError

	def name(self) -> str:
		raise NotImplementedError


class NealBackend(SamplerBackend):
	def __init__(self) -> None:
		import neal  # lazy import
		self._neal = neal

	def sample_bqm(self, bqm: Any, num_reads: int):
		sampler = self._neal.SimulatedAnnealingSampler()
		return sampler.sample(bqm, num_reads=num_reads)

	def name(self) -> str:
		return "neal"


class OpenJijBackend(SamplerBackend):
	def __init__(self) -> None:
		try:
			import openjij as oj  # type: ignore
			self._oj = oj
		except Exception as e:
			raise RuntimeError("openjij is not installed. Please install openjij to use this backend.") from e

	def sample_bqm(self, bqm: Any, num_reads: int):
		Q = bqm.to_qubo()[0]
		sampler = self._oj.SASampler()
		resp = sampler.sample_qubo(Q, num_reads=num_reads)
		# convert OpenJij response to dimod SampleSet via dimod.AdjVectorBQM for consistency if needed
		# For MVP, return the raw response; CLI will branch when handling this backend
		return resp

	def name(self) -> str:
		return "openjij"


def make_backend(name: str) -> SamplerBackend:
	if name == "neal":
		return NealBackend()
	if name == "openjij":
		return OpenJijBackend()
	raise ValueError(f"Unknown backend: {name}")
