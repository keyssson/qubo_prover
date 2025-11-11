#!/bin/bash
# 三段论示例
# 从 P, P->Q, Q->R 证明 R

set -euo pipefail

PY=${PY:-python}
DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$DIR"

echo "=== 三段论示例 ==="
echo "公理: P, P->Q, Q->R"
echo "目标: R"
echo ""

$PY -m qubo_prover_v2.cli \
    --axioms "P; P->Q; Q->R" \
    --goal "R" \
    --backend neal \
    --reads 150

