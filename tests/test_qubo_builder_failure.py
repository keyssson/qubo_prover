import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import pytest
except Exception:
    pytest = None

from qubo_prover_v3.core.qubo_builder import QUBOBuilder
from qubo_prover_v3.core.sampler import NealBackend
from qubo_prover_v3.core.decoder import (
    decode_sampleset,
    best_by_lowest_energy,
    verify_assignment,
)


def _prove(axioms, goal, reads=80):
    builder = QUBOBuilder()
    model, var_map, _ = builder.build(axioms, goal)
    qubo, bqm, _ = builder.compile_qubo(model)
    backend = NealBackend()
    sampleset = backend.sample_bqm(bqm, num_reads=reads)
    rows = decode_sampleset(sampleset)
    assignment, energy = best_by_lowest_energy(rows)
    var_info = builder.get_variable_info()
    axiom_vars = var_info["axiom_vars"]
    goal_var = var_info["goal_var"]
    success, message = verify_assignment(assignment, axiom_vars, goal_var, var_info)
    return success, message


def test_goal_contradiction_should_fail():
    success, message = _prove(["P", "P->Q"], "~Q")
    assert not success


def test_unrelated_goal_should_fail():
    success, message = _prove(["P&Q"], "R")
    assert not success


def test_contradictory_axioms_should_fail():
    success, message = _prove(["P", "~P"], "Q")
    assert not success


def test_known_limitation_unprovable_but_satisfiable():
    if pytest is None:
        return
    success, message = _prove(["P"], "R")
    pytest.xfail("当前体系检查的是可满足性而非可导性")
    assert not success


def test_known_limitation_tautology_goal():
    if pytest is None:
        return
    success, message = _prove([], "P|~P")
    pytest.xfail("当前体系无公理也可满足部分目标")
    assert not success

