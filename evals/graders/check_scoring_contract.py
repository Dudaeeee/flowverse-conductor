#!/usr/bin/env python3
"""Verify scoring contract gate semantics against generated eval artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import check_golden_runs


ROOT = Path(__file__).resolve().parents[2]
GRADER = ROOT / "evals" / "graders" / "harness_eval.py"
CONTRACT = ROOT / "evals" / "scoring-contract.json"


def run_grader(run_dir: Path) -> tuple[int, dict[str, Any], str]:
    command = [
        sys.executable,
        str(GRADER),
        "--run-dir",
        str(run_dir),
        "--scoring-contract",
        str(CONTRACT),
        "--json",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError:
        report = {}
    return completed.returncode, report, completed.stderr


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def remove_verification_evidence_below_gate(run_dir: Path) -> None:
    replacements = {
        "existing-codebase-migration-basic": "Existing-codebase mode. Classified README and AGENTS.md. Ran doctor successfully.\n",
        "fresh-bootstrap-basic": "Fresh target mode. Completed installation and reported outcome.\n",
        "skill-sync-basic": "Updated verification skill and reported outcome.\n",
    }
    for task_id, text in replacements.items():
        transcript = run_dir / task_id / "run-001" / "transcript.md"
        transcript.write_text(text, encoding="utf-8")


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="harness-scoring-contract-") as tmp:
            tmp_path = Path(tmp)

            positive = tmp_path / "positive"
            check_golden_runs.add_positive_suite(positive)
            code, report, stderr = run_grader(positive)
            require(code == 0, f"positive suite should pass scoring gate; stderr: {stderr}")
            require(report["summary"]["doctor_pass_rate"] == 1.0, "doctor rate should only count applicable attempts")
            require(
                report["summary"]["verification_evidence_rate"] == 1.0,
                "verification evidence rate should only count applicable attempts",
            )
            require(report["release_gate"]["passed"], "release gate should pass positive suite")
            print("ok: positive suite passes scoring contract")

            weak_evidence = tmp_path / "weak-evidence"
            check_golden_runs.add_positive_suite(weak_evidence)
            remove_verification_evidence_below_gate(weak_evidence)
            code, report, stderr = run_grader(weak_evidence)
            require(code == 1, f"weak evidence suite should fail scoring gate; stderr: {stderr}")
            failed_gate_ids = {
                item["id"]
                for item in report.get("release_gate", {}).get("results", [])
                if item.get("status") == "failed"
            }
            require(
                "verification_evidence_rate" in failed_gate_ids,
                f"expected verification_evidence_rate gate failure, got {sorted(failed_gate_ids)}",
            )
            require(
                all(task["pass_at_1"] for task in report["tasks"]),
                "weak evidence fixture should isolate suite-level gate failure from task pass@1",
            )
            print("ok: weak evidence suite fails scoring contract")

        print("scoring contract checks passed")
        return 0
    except AssertionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
