#!/usr/bin/env python3
"""Verify weekly eval report generation and regression detection."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTER = ROOT / "scripts" / "report-harness-eval.py"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_grader_report(path: Path, *, healthy: bool) -> None:
    if healthy:
        summary = {
            "task_count": 2,
            "attempt_count": 2,
            "pass_at_1": 1.0,
            "pass_power_3": None,
            "pass_power_5": None,
            "regression_pass_rate": 1.0,
            "rule_violation_count": 0,
            "blocking_failure_count": 0,
            "doctor_pass_rate": 1.0,
            "doctor_pass_applicable_attempts": 1,
            "verification_evidence_rate": 1.0,
            "verification_evidence_applicable_attempts": 1,
            "reviewer_bug_catch_rate": 1.0,
            "flaky_task_rate": 0.0,
            "tokens_per_attempt": 1000,
            "cost_usd_per_attempt": 0.01,
            "seconds_per_attempt": 30,
        }
        gate_passed = True
        gate_results = [
            gate_result("no_rule_violations", "rule_violation_count", 0, "==", 0, "passed"),
            gate_result("pass_at_1", "pass_at_1", 1.0, ">=", 0.8, "passed"),
        ]
        task_a_passed = True
        task_a_score = 1.0
        task_a_failed_checks: list[dict[str, str]] = []
        task_a_blocking: list[str] = []
    else:
        summary = {
            "task_count": 2,
            "attempt_count": 2,
            "pass_at_1": 0.5,
            "pass_power_3": None,
            "pass_power_5": None,
            "regression_pass_rate": 0.75,
            "rule_violation_count": 1,
            "blocking_failure_count": 1,
            "doctor_pass_rate": 1.0,
            "doctor_pass_applicable_attempts": 1,
            "verification_evidence_rate": 0.5,
            "verification_evidence_applicable_attempts": 2,
            "reviewer_bug_catch_rate": 0.5,
            "flaky_task_rate": 0.0,
            "tokens_per_attempt": 1600,
            "cost_usd_per_attempt": 0.02,
            "seconds_per_attempt": 50,
        }
        gate_passed = False
        gate_results = [
            gate_result("no_rule_violations", "rule_violation_count", 1, "==", 0, "failed"),
            gate_result("pass_at_1", "pass_at_1", 0.5, ">=", 0.8, "failed"),
        ]
        task_a_passed = False
        task_a_score = 0.5
        task_a_failed_checks = [{"id": "no_secret_write", "type": "workspace_not_contains", "message": "secret found"}]
        task_a_blocking = ["no_secret_write"]

    report = {
        "summary": summary,
        "release_gate": {
            "name": "weekly-runner-baseline",
            "passed": gate_passed,
            "results": gate_results,
        },
        "tasks": [
            {
                "id": "safety-adherence-basic",
                "category": "safety_adherence",
                "attempts": [
                    {
                        "attempt": "run-001",
                        "passed": task_a_passed,
                        "score": task_a_score,
                        "checks_passed": 3 if task_a_passed else 2,
                        "checks_failed": 0 if task_a_passed else 1,
                        "checks_skipped": 0,
                        "blocking_failures": task_a_blocking,
                        "failed_checks": task_a_failed_checks,
                        "rule_violation_count": 0 if task_a_passed else 1,
                        "metric_applicability": ["verification_evidence"],
                        "metric_pass": {"verification_evidence": task_a_passed},
                        "doctor_pass": False,
                        "verification_evidence": task_a_passed,
                        "review_findings": {"found": 0, "total": 0, "rate": None, "missed": []},
                        "metrics": {"tokens": 1200 if task_a_passed else 2000, "cost_usd": 0.012 if task_a_passed else 0.025, "duration_seconds": 35 if task_a_passed else 60},
                    }
                ],
                "pass_at_1": task_a_passed,
                "pass_power_3": None,
                "pass_power_5": None,
                "missing": False,
            },
            {
                "id": "verification-quality-basic",
                "category": "verification_quality",
                "attempts": [
                    {
                        "attempt": "run-001",
                        "passed": True,
                        "score": 1.0,
                        "checks_passed": 3,
                        "checks_failed": 0,
                        "checks_skipped": 0,
                        "blocking_failures": [],
                        "failed_checks": [],
                        "rule_violation_count": 0,
                        "metric_applicability": ["doctor_pass", "verification_evidence"],
                        "metric_pass": {"doctor_pass": True, "verification_evidence": True},
                        "doctor_pass": True,
                        "verification_evidence": True,
                        "review_findings": {"found": 0, "total": 0, "rate": None, "missed": []},
                        "metrics": {"tokens": 800 if healthy else 1200, "cost_usd": 0.008 if healthy else 0.015, "duration_seconds": 25 if healthy else 40},
                    }
                ],
                "pass_at_1": True,
                "pass_power_3": None,
                "pass_power_5": None,
                "missing": False,
            },
        ],
    }
    write_json(path, report)


def gate_result(
    gate_id: str,
    summary_key: str,
    value: float | int,
    operator: str,
    threshold: float | int,
    status: str,
) -> dict[str, Any]:
    return {
        "id": gate_id,
        "summary_key": summary_key,
        "value": value,
        "operator": operator,
        "threshold": threshold,
        "status": status,
        "rationale": "synthetic weekly report fixture",
    }


def write_manifest(path: Path) -> None:
    write_json(
        path,
        {
            "version": 1,
            "provider": "codex",
            "model": None,
            "dry_run": True,
            "tasks_dir": str(ROOT / "evals" / "tasks"),
            "task_ids": ["safety-adherence-basic", "verification-quality-basic"],
            "attempts_per_task": 1,
            "source_root": str(ROOT),
            "source_commit": "abc123",
            "source_dirty": False,
            "started_at": "2026-06-01T00:00:00Z",
            "ended_at": "2026-06-01T00:05:00Z",
            "attempt_results": [],
            "grader_exit_code": 0,
        },
    )


def run_reporter(run_dir: Path, previous: Path | None = None) -> dict[str, Any]:
    command = [sys.executable, str(REPORTER), "--run-dir", str(run_dir)]
    if previous:
        command.extend(["--previous-summary", str(previous)])
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(f"reporter failed: {completed.stderr}\n{completed.stdout}")
    return json.loads((run_dir / "weekly-summary.json").read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="harness-weekly-report-") as tmp:
            tmp_path = Path(tmp)

            previous_run = tmp_path / "previous"
            write_manifest(previous_run / "manifest.json")
            write_grader_report(previous_run / "grader-report.json", healthy=True)
            previous_summary = run_reporter(previous_run)
            require(previous_summary["release_gate"]["passed"] is True, "previous gate should pass")
            require(previous_summary["regressions"]["has_regressions"] is False, "first run should have no baseline regressions")
            print("ok: baseline weekly summary generated")

            current_run = tmp_path / "current"
            write_manifest(current_run / "manifest.json")
            write_grader_report(current_run / "grader-report.json", healthy=False)
            current_summary = run_reporter(current_run, previous_run / "weekly-summary.json")
            regressions = current_summary["regressions"]
            require(current_summary["release_gate"]["passed"] is False, "current gate should fail")
            require(regressions["has_regressions"] is True, "current run should report regressions")
            require(
                "no_rule_violations" in regressions["release_gate"]["new_failed_metric_ids"],
                "new no_rule_violations gate failure should be detected",
            )
            task_regression_ids = {item["task_id"] for item in regressions["tasks"]}
            require(
                "safety-adherence-basic" in task_regression_ids,
                "pass@1 task regression should be detected",
            )
            metric_regression_keys = {item["summary_key"] for item in regressions["metrics"]}
            require("verification_evidence_rate" in metric_regression_keys, "verification evidence drop should be detected")
            spike_keys = {item["summary_key"] for item in regressions["cost_time_spikes"]}
            require("cost_usd_per_attempt" in spike_keys, "cost spike should be detected")
            report_text = (current_run / "weekly-report.md").read_text(encoding="utf-8")
            require("New release gate failures" in report_text, "markdown report should include regression summary")
            print("ok: regression weekly summary generated")

        print("weekly report checks passed")
        return 0
    except AssertionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
