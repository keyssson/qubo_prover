from typing import Any, Dict, List, Tuple


def decode_dimod_sampleset(sampleset: Any) -> List[Tuple[Dict[str, int], float]]:
	rows: List[Tuple[Dict[str, int], float]] = []
	for sample, energy in zip(sampleset.record.sample, sampleset.record.energy):
		assignment = {v: int(sample[idx]) for idx, v in enumerate(sampleset.variables)}
		rows.append((assignment, float(energy)))
	return rows


def decode_openjij_response(resp: Any) -> List[Tuple[Dict[str, int], float]]:
	rows: List[Tuple[Dict[str, int], float]] = []
	# OpenJij SASampler returns a Response with .states (list of dict or arrays) and .energies
	states = getattr(resp, "states", None)
	energies = getattr(resp, "energies", None)
	if states is None or energies is None:
		raise ValueError("Unexpected OpenJij response format")
	for st, en in zip(states, energies):
		if isinstance(st, dict):
			assignment = {str(k): int(v) for k, v in st.items()}
		else:
			# if ndarray like [0,1,0,...], we do not know variable names; skip in MVP
			continue
		rows.append((assignment, float(en)))
	return rows


def verify_modus_ponens_assignment(assign: Dict[str, int]) -> bool:
	P = assign.get("P", 0)
	Imp = assign.get("Imp", 0)
	Q = assign.get("Q", 0)
	R = assign.get("R", 0)
	if R == 1:
		return P == 1 and Imp == 1 and Q == 1
	else:
		# If not using the rule, Q must be 0 in our encoding
		return Q == 0


def best_by_lowest_energy(rows: List[Tuple[Dict[str, int], float]]) -> Tuple[Dict[str, int], float]:
	return min(rows, key=lambda t: t[1])


def verify_and_elim_left(assign: Dict[str, int]) -> bool:
    And = assign.get("And", 0)
    A = assign.get("A", 0)
    RL = assign.get("RL", 0)
    if RL == 1:
        return And == 1 and A == 1
    else:
        return A == 0


def verify_and_elim_right(assign: Dict[str, int]) -> bool:
    And = assign.get("And", 0)
    B = assign.get("B", 0)
    RR = assign.get("RR", 0)
    if RR == 1:
        return And == 1 and B == 1
    else:
        return B == 0


def verify_or_intro(assign: Dict[str, int]) -> bool:
    X = assign.get("X", 0)
    Or = assign.get("Or", 0)
    RI = assign.get("RI", 0)
    if RI == 1:
        return X == 1 and Or == 1
    else:
        return Or == 0


def verify_and_intro(assign: Dict[str, int]) -> bool:
    A = assign.get("A", 0)
    B = assign.get("B", 0)
    And = assign.get("And", 0)
    RAI = assign.get("RAI", 0)
    if RAI == 1:
        return A == 1 and B == 1 and And == 1
    else:
        return And == 0


def verify_modus_tollens(assign: Dict[str, int]) -> bool:
    Imp = assign.get("Imp", 0)
    NQ = assign.get("NQ", 0)
    NP = assign.get("NP", 0)
    RMT = assign.get("RMT", 0)
    if RMT == 1:
        return Imp == 1 and NQ == 1 and NP == 1
    else:
        return NP == 0


def verify_double_neg_elim(assign: Dict[str, int]) -> bool:
    NNX = assign.get("NNX", 0)
    X = assign.get("X", 0)
    RDN = assign.get("RDN", 0)
    if RDN == 1:
        return NNX == 1 and X == 1
    else:
        return X == 0


def verify_de_morgan(assign: Dict[str, int]) -> bool:
    NAnd = assign.get("NAnd", 0)
    OrNeg = assign.get("OrNeg", 0)
    RDM = assign.get("RDM", 0)
    if RDM == 1:
        return NAnd == 1 and OrNeg == 1
    else:
        return OrNeg == 0


def verify_double_neg_intro(assign: Dict[str, int]) -> bool:
    X = assign.get("X", 0)
    NNX = assign.get("NNX", 0)
    RDI = assign.get("RDI", 0)
    if RDI == 1:
        return X == 1 and NNX == 1
    else:
        return NNX == 0


def verify_de_morgan_two(assign: Dict[str, int]) -> bool:
    NOr = assign.get("NOr", 0)
    AndNeg = assign.get("AndNeg", 0)
    RDM2 = assign.get("RDM2", 0)
    if RDM2 == 1:
        return NOr == 1 and AndNeg == 1
    else:
        return AndNeg == 0


def verify_or_elim(assign: Dict[str, int]) -> bool:
    Or = assign.get("Or", 0)
    IAC = assign.get("IAC", 0)
    IBC = assign.get("IBC", 0)
    C = assign.get("C", 0)
    ROE = assign.get("ROE", 0)
    if ROE == 1:
        return Or == 1 and IAC == 1 and IBC == 1 and C == 1
    else:
        return C == 0


def verify_resolution(assign: Dict[str, int]) -> bool:
    OrAX = assign.get("OrAX", 0)
    OrNAY = assign.get("OrNAY", 0)
    OrXY = assign.get("OrXY", 0)
    RRES = assign.get("RRES", 0)
    if RRES == 1:
        return OrAX == 1 and OrNAY == 1 and OrXY == 1
    else:
        return OrXY == 0


def verify_implication_trans(assign: Dict[str, int]) -> bool:
    IAB = assign.get("IAB", 0)
    IBC = assign.get("IBC", 0)
    IAC2 = assign.get("IAC2", 0)
    RTR = assign.get("RTR", 0)
    if RTR == 1:
        return IAB == 1 and IBC == 1 and IAC2 == 1
    else:
        return IAC2 == 0


def verify_or_comm(assign: Dict[str, int]) -> bool:
    OrAB = assign.get("OrAB", 0)
    OrBA = assign.get("OrBA", 0)
    RORC = assign.get("RORC", 0)
    if RORC == 1:
        return OrAB == 1 and OrBA == 1
    else:
        return OrBA == 0


def verify_contraposition(assign: Dict[str, int]) -> bool:
    Imp = assign.get("Imp", 0)
    INQNP = assign.get("INQNP", 0)
    RCP = assign.get("RCP", 0)
    if RCP == 1:
        return Imp == 1 and INQNP == 1
    else:
        return INQNP == 0


def verify_and_comm(assign: Dict[str, int]) -> bool:
    AndAB = assign.get("AndAB", 0)
    AndBA = assign.get("AndBA", 0)
    RANDC = assign.get("RANDC", 0)
    if RANDC == 1:
        return AndAB == 1 and AndBA == 1
    else:
        return AndBA == 0


def verify_or_assoc(assign: Dict[str, int]) -> bool:
    OrA_BC = assign.get("OrA_BC", 0)
    OrAB_C = assign.get("OrAB_C", 0)
    RORAS = assign.get("RORAS", 0)
    if RORAS == 1:
        return OrA_BC == 1 and OrAB_C == 1
    else:
        return OrAB_C == 0


def verify_or_idempotence(assign: Dict[str, int]) -> bool:
    OrAA = assign.get("OrAA", 0)
    A = assign.get("A", 0)
    RORI = assign.get("RORI", 0)
    if RORI == 1:
        return OrAA == 1 and A == 1
    else:
        return A == 0


def verify_and_idempotence(assign: Dict[str, int]) -> bool:
    AndAA = assign.get("AndAA", 0)
    A = assign.get("A", 0)
    RANDI = assign.get("RANDI", 0)
    if RANDI == 1:
        return AndAA == 1 and A == 1
    else:
        return A == 0
