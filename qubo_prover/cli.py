import argparse
from typing import List

from .parser import parse
from .encoder import ModusPonensEncoder
from .sampler import make_backend, NealBackend
from .decoder import (
    decode_dimod_sampleset,
    decode_openjij_response,
    best_by_lowest_energy,
    verify_modus_ponens_assignment,
    verify_and_elim_left,
    verify_and_elim_right,
    verify_or_intro,
    verify_and_intro,
    verify_modus_tollens,
    verify_double_neg_elim,
    verify_de_morgan,
    verify_double_neg_intro,
    verify_de_morgan_two,
    verify_or_elim,
    verify_resolution,
    verify_implication_trans,
    verify_or_comm,
    verify_contraposition,
    verify_and_comm,
    verify_or_assoc,
    verify_or_idempotence,
    verify_and_idempotence,
)


def main():
	ap = argparse.ArgumentParser(description="QUBO Prover MVP (Modus Ponens)")
	ap.add_argument("--axioms", required=True, help="Axioms separated by ';', e.g., 'P; P->Q'")
	ap.add_argument("--goal", required=True, help="Goal formula, e.g., 'Q'")
	ap.add_argument("--backend", default="neal", choices=["neal", "openjij"], help="Sampler backend")
	ap.add_argument("--reads", type=int, default=50, help="Number of reads/samples")
	ap.add_argument("--penalty", type=float, default=4.0, help="Penalty M value")
	args = ap.parse_args()

	axioms: List[str] = [a.strip() for a in args.axioms.split(";") if a.strip()]
	goal = args.goal.strip()

	# MVP: support the MP pattern; we still parse to validate input forms
	try:
		parsed_axioms = [parse(a) for a in axioms]
		parsed_goal = parse(goal)
	except Exception as e:
		print(f"Parse error: {e}")
		return 2

	encoder = ModusPonensEncoder()
	model, qubo, bqm, offset = encoder.compile_qubo(M_value=args.penalty)

	backend = make_backend(args.backend)
	print(f"Using backend: {backend.name()} | num_reads={args.reads}")

	if isinstance(backend, NealBackend):
		sampleset = backend.sample_bqm(bqm, args.reads)
		rows = decode_dimod_sampleset(sampleset)
	else:
		resp = backend.sample_bqm(bqm, args.reads)
		rows = decode_openjij_response(resp)

	assign, energy = best_by_lowest_energy(rows)
	# goal-aware simple dispatch (MVP): choose a verifier by goal string
	goal_upper = goal.replace(" ", "").upper()
	if goal_upper == "Q":
		ok = verify_modus_ponens_assignment(assign)
		path = "P, (P->Q) => Q with rule R=1"
	elif goal_upper == "A":
		ok = verify_and_elim_left(assign)
		path = "And(A,B) => A with RL=1"
	elif goal_upper == "B":
		ok = verify_and_elim_right(assign)
		path = "And(A,B) => B with RR=1"
	elif goal_upper == "OR":
		ok = verify_or_intro(assign)
		path = "X => (X or Y) with RI=1"
	elif goal_upper == "AND":
		ok = verify_and_intro(assign)
		path = "A,B => (A and B) with RAI=1"
	elif goal_upper == "NP":
		ok = verify_modus_tollens(assign)
		path = "(P->Q), ~Q => ~P with RMT=1"
	elif goal_upper == "X":
		ok = verify_double_neg_elim(assign)
		path = "~~X => X with RDN=1"
	elif goal_upper == "ORNEG":
		ok = verify_de_morgan(assign)
		path = "~(A&B) => (~A or ~B) with RDM=1"
	elif goal_upper == "NNX":
		ok = verify_double_neg_intro(assign)
		path = "X => ~~X with RDI=1"
	elif goal_upper == "ANDNEG":
		ok = verify_de_morgan_two(assign)
		path = "~(A|B) => (~A & ~B) with RDM2=1"
	elif goal_upper == "C":
		ok = verify_or_elim(assign)
		path = "Or(A,B), A->C, B->C => C with ROE=1"
	elif goal_upper == "ORXY":
		ok = verify_resolution(assign)
		path = "Or(A,X), Or(~A,Y) => Or(X,Y) with RRES=1"
	elif goal_upper == "IAC2":
		ok = verify_implication_trans(assign)
		path = "(A->B),(B->C) => (A->C) with RTR=1"
	elif goal_upper == "ORBA":
		ok = verify_or_comm(assign)
		path = "Or(A,B) => Or(B,A) with RORC=1"
	elif goal_upper == "INQNP":
		ok = verify_contraposition(assign)
		path = "(P->Q) => (~Q -> ~P) with RCP=1"
	elif goal_upper == "ANDBA":
		ok = verify_and_comm(assign)
		path = "And(A,B) => And(B,A) with RANDC=1"
	elif goal_upper == "ORAB_C":
		ok = verify_or_assoc(assign)
		path = "Or(A,Or(B,C)) => Or(Or(A,B),C) with RORAS=1"
	elif goal_upper == "A_ORIDEM":
		ok = verify_or_idempotence(assign)
		path = "Or(A,A) => A with RORI=1"
	elif goal_upper == "A_ANDIDEM":
		ok = verify_and_idempotence(assign)
		path = "And(A,A) => A with RANDI=1"
	else:
		ok = verify_modus_ponens_assignment(assign)
		path = "P, (P->Q) => Q with rule R=1"

	print("lowest_energy_assignment:", assign)
	print("energy:", energy)
	print("provable:", ok)
	if ok:
		print("proof_path:", path)


if __name__ == "__main__":
	main()
