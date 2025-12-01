import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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


def test_modus_ponens():
    success, message = _prove(["P", "P->Q"], "Q")
    assert success


def test_modus_tollens():
    success, message = _prove(["P->Q", "~Q"], "~P")
    assert success


def test_and_elimination_left():
    success, message = _prove(["P&Q"], "P")
    assert success


def test_and_elimination_right():
    success, message = _prove(["P&Q"], "Q")
    assert success


def test_and_introduction():
    success, message = _prove(["P", "Q"], "P&Q")
    assert success


def test_or_introduction_from_p():
    success, message = _prove(["P"], "P|Q")
    assert success


def test_or_introduction_from_q():
    success, message = _prove(["Q"], "P|Q")
    assert success


def test_double_negation_elimination():
    success, message = _prove(["~~P"], "P")
    assert success

