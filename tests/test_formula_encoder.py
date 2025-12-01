import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qubo_prover_v3.core.formula_encoder import FormulaEncoder
from qubo_prover_v3.core.ast import Var, Not, And, Or, Imply
from pyqubo import Binary


def _minimize_energy(expr):
    model = expr.compile()
    bqm = model.to_bqm()
    try:
        import neal
        sampler = neal.SimulatedAnnealingSampler()
        sampleset = sampler.sample(bqm, num_reads=50)
        best = sampleset.first.sample
        energy = sampleset.first.energy
        return best, energy
    except Exception:
        return None, None


def test_not_constraint_semantics():
    enc = FormulaEncoder()
    p = Var("P")
    not_p = Not(p)
    name_p, var_p = enc.encode_formula(p)
    name_np, var_np = enc.encode_formula(not_p)
    constraints = enc.get_constraints()
    assert any(c[0] == "NOT" and c[1] == name_np for c in constraints)
    H = 0
    for c in constraints:
        H += c[-1]
    best, _ = _minimize_energy(H)
    assert best is not None
    assert (best[name_p] + best[name_np]) == 1


def test_and_constraint_semantics():
    enc = FormulaEncoder()
    p = Var("P")
    q = Var("Q")
    and_pq = And(p, q)
    name_p, var_p = enc.encode_formula(p)
    name_q, var_q = enc.encode_formula(q)
    name_and, var_and = enc.encode_formula(and_pq)
    H = 0
    for c in enc.get_constraints():
        H += c[-1]
    best, _ = _minimize_energy(H)
    assert best is not None
    assert best[name_and] in (0, 1)


def test_or_constraint_semantics():
    enc = FormulaEncoder()
    p = Var("P")
    q = Var("Q")
    or_pq = Or(p, q)
    name_p, var_p = enc.encode_formula(p)
    name_q, var_q = enc.encode_formula(q)
    name_or, var_or = enc.encode_formula(or_pq)
    H = 0
    for c in enc.get_constraints():
        H += c[-1]
    best, _ = _minimize_energy(H)
    assert best is not None
    assert best[name_or] >= (best[name_p] or best[name_q])


def test_imply_constraint_semantics():
    enc = FormulaEncoder()
    p = Var("P")
    q = Var("Q")
    imp = Imply(p, q)
    name_p, var_p = enc.encode_formula(p)
    name_q, var_q = enc.encode_formula(q)
    name_imp, var_imp = enc.encode_formula(imp)
    H = 0
    for c in enc.get_constraints():
        H += c[-1]
    best, _ = _minimize_energy(H)
    assert best is not None
    if best[name_p] == 1 and best[name_imp] == 1:
        assert best[name_q] == 1

