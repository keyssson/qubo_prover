import sys
import os
import subprocess


def test_cli_smoke_no_backend_run():
    root = os.path.dirname(os.path.dirname(__file__))
    cmd = [sys.executable, "-m", "qubo_prover_v3.cli", "--axioms", "P;P->Q", "--goal", "Q", "--reads", "5"]
    try:
        proc = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        out = proc.stdout.decode(errors="ignore")
        err = proc.stderr.decode(errors="ignore")
        assert proc.returncode in (0, 1, 2)
        assert "QUBO Prover V3" in out or "错误" in err
    except Exception:
        assert False

