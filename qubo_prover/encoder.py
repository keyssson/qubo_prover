from typing import Dict, Tuple
from pyqubo import Binary, Placeholder


class ModusPonensEncoder:
    """
    PyQUBO-based encoder with multiple rules:
    - Modus Ponens (MP): variables P, Imp, Q, R
      H_mp = M * [ R*(1-P) + R*(1-Imp) + R*(1-Q) + Q*(1-R) ]
    - And-Elimination Left (And-EL): from And -> A
      Variables: A, B, And, RL
      H_andl = M * [ RL*(1-And) + RL*(1-A) + A*(1-RL) ]
    - And-Elimination Right (And-ER): from And -> B
      Variables: A, B, And, RR
      H_andr = M * [ RR*(1-And) + RR*(1-B) + B*(1-RR) ]
    - Or-Introduction (Or-Intro): from X -> (X or Y)
      Variables: X, Y, Or, RI
      H_ori = M * [ RI*(1-X) + RI*(1-Or) + Or*(1-RI) ]
    - Modus Tollens (MT): from (P->Q) and ~Q infer ~P
      Variables: Imp, NQ, NP, RMT
      H_mt = M * [ RMT*(1-Imp) + RMT*(1-NQ) + RMT*(1-NP) + NP*(1-RMT) ]
    - Double Negation Elimination (DNE): from ~~X infer X
      Variables: NNX (~~X), X, RDN
      H_dne = M * [ RDN*(1-NNX) + RDN*(1-X) + X*(1-RDN) ]
    - De Morgan (DM1): from ~(A & B) infer (~A or ~B)
      Variables: NAnd, OrNeg, RDM (reuses NA, NB if needed)
      H_dm = M * [ RDM*(1-NAnd) + RDM*(1-OrNeg) + OrNeg*(1-RDM) ]
    - Double Negation Introduction (DNI): from X infer ~~X
      Variables: X, NNX, RDI
      H_dni = M * [ RDI*(1-X) + RDI*(1-NNX) + NNX*(1-RDI) ]
    - De Morgan 2 (DM2): from ~(A | B) infer (~A & ~B)
      Variables: NOr, AndNeg, RDM2
      H_dm2 = M * [ RDM2*(1-NOr) + RDM2*(1-AndNeg) + AndNeg*(1-RDM2) ]
    - Or-Elimination (Orel): from Or(A,B), A->C, B->C infer C
      Variables: Or, IAC, IBC, C, ROE
      H_orel = M * [ ROE*(1-Or) + ROE*(1-IAC) + ROE*(1-IBC) + ROE*(1-C) + C*(1-ROE) ]
    - Resolution (RES): from Or(A,X), Or(~A,Y) infer Or(X,Y)
      Variables: OrAX, OrNAY, OrXY, RRES
      H_res = M * [ RRES*(1-OrAX) + RRES*(1-OrNAY) + RRES*(1-OrXY) + OrXY*(1-RRES) ]
    - Implication Transitivity (TR): from (A->B),(B->C) infer (A->C)
      Variables: IAB, IBC, IAC2, RTR
      H_tr = M * [ RTR*(1-IAB) + RTR*(1-IBC) + RTR*(1-IAC2) + IAC2*(1-RTR) ]
    - Or Commutation (ORC): from Or(A,B) infer Or(B,A)
      Variables: OrAB, OrBA, RORC
      H_orc = M * [ RORC*(1-OrAB) + RORC*(1-OrBA) + OrBA*(1-RORC) ]
    - Contraposition (CP): from (P->Q) infer (~Q -> ~P)
      Variables: Imp, INQNP, RCP
      H_cp = M * [ RCP*(1-Imp) + RCP*(1-INQNP) + INQNP*(1-RCP) ]
    - And Commutation (ANDC): from And(A,B) infer And(B,A)
      Variables: AndAB, AndBA, RANDC
      H_andc = M * [ RANDC*(1-AndAB) + RANDC*(1-AndBA) + AndBA*(1-RANDC) ]
    - Or Associativity (ORAS): from Or(A, Or(B,C)) infer Or(Or(A,B), C)
      Variables: OrA_BC, OrAB_C, RORAS
      H_oras = M * [ RORAS*(1-OrA_BC) + RORAS*(1-OrAB_C) + OrAB_C*(1-RORAS) ]
    - Or Idempotence (ORI): from Or(A,A) infer A
      Variables: OrAA, A, RORI
      H_ori2 = M * [ RORI*(1-OrAA) + RORI*(1-A) + A*(1-RORI) ]
    - And Idempotence (ANDI): from And(A,A) infer A
      Variables: AndAA, A, RANDI
      H_andi2 = M * [ RANDI*(1-AndAA) + RANDI*(1-A) + A*(1-RANDI) ]
    """

    def __init__(self, penalty_name: str = "M") -> None:
        self.penalty = Placeholder(penalty_name)

    def build(self) -> Tuple[object, Dict[str, Binary]]:
        # MP variables
        P = Binary("P")
        Imp = Binary("Imp")
        Q = Binary("Q")
        R = Binary("R")

        # And-Elim variables
        A = Binary("A")
        B = Binary("B")
        And = Binary("And")
        RL = Binary("RL")  # And-Elim Left
        RR = Binary("RR")  # And-Elim Right

        # Or-Intro variables
        X = Binary("X")
        Y = Binary("Y")
        Or = Binary("Or")
        RI = Binary("RI")

        # And-Introduction control variable (reuses A, B, And)
        RAI = Binary("RAI")

        # Modus Tollens variables (reuses Imp; adds NP, NQ, control RMT)
        NP = Binary("NP")
        NQ = Binary("NQ")
        RMT = Binary("RMT")

        # Double Negation Elimination variables (reuses X; adds NNX, control RDN)
        NNX = Binary("NNX")
        RDN = Binary("RDN")

        # De Morgan variables (treat inputs as literals; no structural tying in MVP)
        NA = Binary("NA")
        NB = Binary("NB")
        NAnd = Binary("NAnd")
        OrNeg = Binary("OrNeg")
        RDM = Binary("RDM")

        # Double Negation Introduction control
        RDI = Binary("RDI")

        # De Morgan 2 variables
        NOr = Binary("NOr")
        AndNeg = Binary("AndNeg")
        RDM2 = Binary("RDM2")

        # Or-Elimination variables (reuse Or; add implications and goal C)
        IAC = Binary("IAC")
        IBC = Binary("IBC")
        C = Binary("C")
        ROE = Binary("ROE")

        # Resolution variables (treat as abstract literals)
        OrAX = Binary("OrAX")
        OrNAY = Binary("OrNAY")
        OrXY = Binary("OrXY")
        RRES = Binary("RRES")

        # Implication transitivity variables
        IAB = Binary("IAB")
        IBC = Binary("IBC")
        IAC2 = Binary("IAC2")
        RTR = Binary("RTR")

        # Or-commutation variables
        OrAB = Binary("OrAB")
        OrBA = Binary("OrBA")
        RORC = Binary("RORC")

        # Contraposition variables
        INQNP = Binary("INQNP")
        RCP = Binary("RCP")

        # And commutation variables
        AndAB = Binary("AndAB")
        AndBA = Binary("AndBA")
        RANDC = Binary("RANDC")

        # Or associativity variables
        OrA_BC = Binary("OrA_BC")
        OrAB_C = Binary("OrAB_C")
        RORAS = Binary("RORAS")

        # Idempotence variables (reuse A)
        OrAA = Binary("OrAA")
        RORI = Binary("RORI")
        AndAA = Binary("AndAA")
        RANDI = Binary("RANDI")

        # Energy terms
        term_mp = R * (1 - P) + R * (1 - Imp) + R * (1 - Q) + Q * (1 - R)
        term_andl = RL * (1 - And) + RL * (1 - A) + A * (1 - RL)
        term_andr = RR * (1 - And) + RR * (1 - B) + B * (1 - RR)
        term_ori = RI * (1 - X) + RI * (1 - Or) + Or * (1 - RI)
        term_andi = RAI * (1 - A) + RAI * (1 - B) + RAI * (1 - And) + And * (1 - RAI)
        term_mt = RMT * (1 - Imp) + RMT * (1 - NQ) + RMT * (1 - NP) + NP * (1 - RMT)
        term_dne = RDN * (1 - NNX) + RDN * (1 - X) + X * (1 - RDN)
        term_dm = RDM * (1 - NAnd) + RDM * (1 - OrNeg) + OrNeg * (1 - RDM)
        term_dni = RDI * (1 - X) + RDI * (1 - NNX) + NNX * (1 - RDI)
        term_dm2 = RDM2 * (1 - NOr) + RDM2 * (1 - AndNeg) + AndNeg * (1 - RDM2)
        term_orel = ROE * (1 - Or) + ROE * (1 - IAC) + ROE * (1 - IBC) + ROE * (1 - C) + C * (1 - ROE)
        term_res = RRES * (1 - OrAX) + RRES * (1 - OrNAY) + RRES * (1 - OrXY) + OrXY * (1 - RRES)
        term_tr = RTR * (1 - IAB) + RTR * (1 - IBC) + RTR * (1 - IAC2) + IAC2 * (1 - RTR)
        term_orc = RORC * (1 - OrAB) + RORC * (1 - OrBA) + OrBA * (1 - RORC)
        term_cp = RCP * (1 - Imp) + RCP * (1 - INQNP) + INQNP * (1 - RCP)
        term_andc = RANDC * (1 - AndAB) + RANDC * (1 - AndBA) + AndBA * (1 - RANDC)
        term_oras = RORAS * (1 - OrA_BC) + RORAS * (1 - OrAB_C) + OrAB_C * (1 - RORAS)
        term_ori2 = RORI * (1 - OrAA) + RORI * (1 - A) + A * (1 - RORI)
        term_andi2 = RANDI * (1 - AndAA) + RANDI * (1 - A) + A * (1 - RANDI)

        H = self.penalty * (term_mp + term_andl + term_andr + term_ori + term_andi + term_mt + term_dne + term_dm + term_dni + term_dm2 + term_orel + term_res + term_tr + term_orc + term_cp + term_andc + term_oras + term_ori2 + term_andi2)
        vars_map = {
            "P": P, "Imp": Imp, "Q": Q, "R": R,
            "A": A, "B": B, "And": And, "RL": RL, "RR": RR,
            "X": X, "Y": Y, "Or": Or, "RI": RI,
            "RAI": RAI,
            "NP": NP, "NQ": NQ, "RMT": RMT,
            "NNX": NNX, "RDN": RDN,
            "NA": NA, "NB": NB, "NAnd": NAnd, "OrNeg": OrNeg, "RDM": RDM,
            "RDI": RDI,
            "NOr": NOr, "AndNeg": AndNeg, "RDM2": RDM2,
            "IAC": IAC, "IBC": IBC, "C": C, "ROE": ROE,
            "OrAX": OrAX, "OrNAY": OrNAY, "OrXY": OrXY, "RRES": RRES,
            "IAB": IAB, "IBC": IBC, "IAC2": IAC2, "RTR": RTR,
            "OrAB": OrAB, "OrBA": OrBA, "RORC": RORC,
            "INQNP": INQNP, "RCP": RCP,
            "AndAB": AndAB, "AndBA": AndBA, "RANDC": RANDC,
            "OrA_BC": OrA_BC, "OrAB_C": OrAB_C, "RORAS": RORAS,
            "OrAA": OrAA, "RORI": RORI, "AndAA": AndAA, "RANDI": RANDI,
        }
        return H, vars_map

    def compile_qubo(self, M_value: float = 4.0):
        H, _ = self.build()
        model = H.compile()
        qubo, offset = model.to_qubo(feed_dict={"M": M_value})
        bqm = model.to_bqm(feed_dict={"M": M_value})
        return model, qubo, bqm, offset
