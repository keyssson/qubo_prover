#!/bin/bash
set -euo pipefail

PY=${PY:-python}
DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$DIR"

$PY -m qubo_prover.cli \
	--axioms "P; P->Q" \
	--goal "Q" \
	--backend neal \
	--reads 50
