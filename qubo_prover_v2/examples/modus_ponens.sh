#!/bin/bash
# Modus Ponens 示例
# 从 P 和 P->Q 证明 Q

set -euo pipefail

PY=${PY:-python}
DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$DIR"

echo "=== Modus Ponens 示例 ==="
echo "公理: P, P->Q"
echo "目标: Q"
echo ""

$PY -m qubo_prover_v2.cli \
    --axioms "P; P->Q" \
    --goal "Q" \
    --backend neal \
    --reads 100

