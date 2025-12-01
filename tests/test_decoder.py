import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qubo_prover_v3.core.qubo_builder import QUBOBuilder
from qubo_prover_v3.core.sampler import NealBackend
from qubo_prover_v3.core.decoder import (
    decode_sampleset,
    best_by_lowest_energy,
    verify_assignment,
    extract_proof_path,
)


def _solve(axioms, goal, reads=80):
    builder = QUBOBuilder()
    model, var_map, _ = builder.build(axioms, goal)
    qubo, bqm, _ = builder.compile_qubo(model)
    backend = NealBackend()
    sampleset = backend.sample_bqm(bqm, num_reads=reads)
    rows = decode_sampleset(sampleset)
    assignment, energy = best_by_lowest_energy(rows)
    var_info = builder.get_variable_info()
    return assignment, var_info


def test_verify_assignment_success_and_path():
    assignment, var_info = _solve(["P", "P->Q"], "Q")
    axiom_vars = var_info["axiom_vars"]
    goal_var = var_info["goal_var"]
    success, message = verify_assignment(assignment, axiom_vars, goal_var, var_info)
    assert success
    steps = extract_proof_path(assignment, var_info)
    assert any("步骤 1" in s for s in steps)
    assert any("步骤 2" in s for s in steps)
    assert any("步骤 3" in s for s in steps)
    assert any("步骤 4" in s for s in steps)


def test_verify_assignment_failure_message():
    assignment, var_info = _solve(["P", "P->Q"], "~Q")
    axiom_vars = var_info["axiom_vars"]
    goal_var = var_info["goal_var"]
    success, message = verify_assignment(assignment, axiom_vars, goal_var, var_info)
    assert not success
    assert ("公理" in message) or ("目标" in message) or ("结构约束" in message)

