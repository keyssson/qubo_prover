#!/bin/bash
# Modus Tollens 示例
# 从 P->Q 和 ~Q 证明 ~P

set -euo pipefail

PY=${PY:-python}
DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$DIR"

echo "=== Modus Tollens 示例 ==="
echo "公理: P->Q, ~Q"
echo "目标: ~P"
echo ""

$PY -m qubo_prover_v2.cli \
    --axioms "P->Q; ~Q" \
    --goal "~P" \
    --backend neal \
    --reads 150

