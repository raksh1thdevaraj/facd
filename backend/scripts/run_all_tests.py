"""Automated All-In-One Test & Evaluation Script (CHIP TST-10).

Executes the complete test suite, coverage auditing, benchmark evaluation,
chart generation, and formal report generation in a single unified command.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"


def run_step(step_name: str, cmd: list[str], cwd: Path = PROJECT_ROOT) -> None:
    """Run shell command with error checking and clear console output."""
    print(f"\n{'=' * 70}\n>>> {step_name}\n{'=' * 70}")
    res = subprocess.run(cmd, cwd=str(cwd), capture_output=False)
    if res.returncode != 0:
        print(f"\n[ERROR] Step '{step_name}' failed with exit code {res.returncode}")
        sys.exit(res.returncode)


def main() -> None:
    """Execute all test and evaluation phases sequentially."""
    python_exe = sys.executable

    # 1. Traceability audit
    run_step(
        "Traceability Matrix Audit",
        [python_exe, str(BACKEND_DIR / "scripts" / "verify_traceability.py")],
    )

    # 2. Pytest execution
    run_step(
        "Pytest Suite Execution",
        [python_exe, "-m", "pytest", "tests/", "-v"],
        cwd=BACKEND_DIR,
    )

    # 3. Model evaluation benchmark
    run_step(
        "Model Evaluation Benchmark",
        [python_exe, str(PROJECT_ROOT / "ml" / "evaluation" / "benchmark_runner.py")],
    )

    # 4. Chart rendering
    run_step(
        "Publication-Grade Chart Generator",
        [python_exe, str(PROJECT_ROOT / "ml" / "evaluation" / "chart_generator.py")],
    )

    # 5. Formal report synthesis
    run_step(
        "Formal Evaluation Report Synthesis",
        [python_exe, str(PROJECT_ROOT / "ml" / "evaluation" / "report_writer.py")],
    )

    print("\n" + "=" * 70)
    print("ALL TESTS & EVALUATION BENCHMARKS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
