#!/usr/bin/env python3
"""Deterministic grader for Flowverse Conductor harness eval artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TASKS_DIR = ROOT / "evals" / "tasks"
DEFAULT_SCORING_CONTRACT = ROOT / "evals" / "scoring-contract.json"

FILE_CHECKS = {"file_exists", "file_not_exists", "file_contains", "file_not_contains"}
TEXT_CHECKS = {
    "file_contains",
    "file_not_contains",
    "transcript_contains",
    "transcript_not_contains",
    "review_contains",
    "review_not_contains",
    "workspace_contains",
    "workspace_not_contains",
}
SUPPORTED_CHECKS = FILE_CHECKS | TEXT_CHECKS | {"command_succeeds", "json_valid"}
SUPPORTED_OPERATORS = {"==", ">=", "<=", ">", "<"}
SUPPORTED_NULL_POLICIES = {"fail", "pass", "skip_without_applicable_tasks"}
SKIPPED_SCAN_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
SUMMARY_KEYS = {
    "task_count",
    "attempt_count",
    "pass_at_1",
    "pass_power_3",
    "pass_power_5",
    "regression_pass_rate",
    "rule_violation_count",
    "blocking_failure_count",
    "doctor_pass_rate",
    "doctor_pass_applicable_attempts",
    "verification_evidence_rate",
    "verification_evidence_applicable_attempts",
    "reviewer_bug_catch_rate",
    "flaky_task_rate",
    "tokens_per_attempt",
    "cost_usd_per_attempt",
    "seconds_per_attempt",
}


class EvalError(RuntimeError):
    pass


@dataclass
class CheckResult:
    check_id: str
    check_type: str
    status: str
    weight: float
    blocking: bool
    metric: str | None
    message: str

    @property
    def passed(self) -> bool:
        return self.status == "passed"

    @property
    def failed(self) -> bool:
        return self.status == "failed"

    @property
    def skipped(self) -> bool:
        return self.status == "skipped"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise EvalError(f"{path}: invalid JSON: {error}") from error


def safe_rel_path(raw: str, field: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise EvalError(f"{field} must be a repository-relative path: {raw}")
    return path


def read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def regex_found(pattern: str, text: str) -> bool:
    return re.search(pattern, text, flags=re.MULTILINE) is not None


def iter_workspace_text(workspace: Path) -> str:
    if not workspace.is_dir():
        return ""
    chunks: list[str] = []
    for path in sorted(p for p in workspace.rglob("*") if p.is_file()):
        if SKIPPED_SCAN_DIRS.intersection(path.parts):
            continue
        text = read_text(path)
        if text is not None:
            chunks.append(f"\n--- {path.relative_to(workspace)} ---\n{text}")
    return "".join(chunks)


def validate_task(path: Path, tasks_dir: Path) -> dict[str, Any]:
    task = load_json(path)
    for field in ("id", "version", "category", "prompt", "grading", "checks"):
        if field not in task:
            raise EvalError(f"{path}: missing required field: {field}")

    if task["id"] != path.stem:
        raise EvalError(f"{path}: task id must match filename stem")
    if not isinstance(task["checks"], list) or not task["checks"]:
        raise EvalError(f"{path}: checks must be a non-empty list")

    fixture = task.get("fixture")
    if fixture:
        fixture_path = (tasks_dir.parent / safe_rel_path(fixture, "fixture")).resolve()
        if not fixture_path.exists():
            raise EvalError(f"{path}: fixture does not exist: {fixture}")

    grading = task["grading"]
    minimum = grading.get("minimum_score")
    if not isinstance(minimum, (int, float)) or not 0 <= minimum <= 1:
        raise EvalError(f"{path}: grading.minimum_score must be a number from 0 to 1")
    minimum_bug = grading.get("minimum_bug_catch_rate")
    if minimum_bug is not None and (
        not isinstance(minimum_bug, (int, float)) or not 0 <= minimum_bug <= 1
    ):
        raise EvalError(
            f"{path}: grading.minimum_bug_catch_rate must be a number from 0 to 1"
        )

    seen_ids: set[str] = set()
    for index, check in enumerate(task["checks"], start=1):
        if not isinstance(check, dict):
            raise EvalError(f"{path}: check #{index} must be an object")
        check_id = check.get("id")
        check_type = check.get("type")
        if not check_id or not isinstance(check_id, str):
            raise EvalError(f"{path}: check #{index} missing string id")
        if check_id in seen_ids:
            raise EvalError(f"{path}: duplicate check id: {check_id}")
        seen_ids.add(check_id)
        if check_type not in SUPPORTED_CHECKS:
            raise EvalError(f"{path}: check {check_id} unsupported type: {check_type}")
        if check_type in FILE_CHECKS and "path" not in check:
            raise EvalError(f"{path}: check {check_id} requires path")
        if check_type in TEXT_CHECKS and "pattern" not in check:
            raise EvalError(f"{path}: check {check_id} requires pattern")
        if check_type == "json_valid" and "path" not in check:
            raise EvalError(f"{path}: check {check_id} requires path")
        if check_type == "command_succeeds":
            command = check.get("command")
            if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
                raise EvalError(f"{path}: check {check_id} command must be a string list")
        if "path" in check:
            safe_rel_path(check["path"], f"check {check_id} path")
        weight = check.get("weight", 1)
        if not isinstance(weight, (int, float)) or weight <= 0:
            raise EvalError(f"{path}: check {check_id} weight must be positive")

    for finding in task.get("expected_findings", []):
        if not finding.get("id") or not finding.get("pattern"):
            raise EvalError(f"{path}: each expected finding requires id and pattern")

    artifact_contract = task.get("artifact_contract", {})
    if not isinstance(artifact_contract, dict):
        raise EvalError(f"{path}: artifact_contract must be an object")
    for name, raw_path in artifact_contract.items():
        if not isinstance(raw_path, str):
            raise EvalError(f"{path}: artifact_contract.{name} must be a string")
        safe_rel_path(raw_path, f"artifact_contract.{name}")

    return task


def load_tasks(tasks_dir: Path) -> list[dict[str, Any]]:
    if not tasks_dir.is_dir():
        raise EvalError(f"tasks directory does not exist: {tasks_dir}")
    tasks = [validate_task(path, tasks_dir) for path in sorted(tasks_dir.glob("*.json"))]
    if not tasks:
        raise EvalError(f"no task JSON files found in {tasks_dir}")
    return tasks


def floats_equal(left: float | int | None, right: float | int | None) -> bool:
    if left is None or right is None:
        return left is right
    return abs(float(left) - float(right)) < 1e-9


def validate_gate_metric(metric: dict[str, Any], path: Path, section: str) -> None:
    metric_id = metric.get("id")
    summary_key = metric.get("summary_key")
    if not metric_id or not isinstance(metric_id, str):
        raise EvalError(f"{path}: {section} metric requires string id")
    if not isinstance(summary_key, str):
        raise EvalError(f"{path}: {section} metric {metric_id} requires string summary_key")
    if summary_key not in SUMMARY_KEYS:
        raise EvalError(
            f"{path}: {section} metric {metric_id} uses unknown summary_key: {summary_key}"
        )
    applies_to = metric.get("applies_to")
    if applies_to is not None and not isinstance(applies_to, str):
        raise EvalError(f"{path}: {section} metric {metric_id} applies_to must be a string")


def validate_scoring_contract(path: Path, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    if not path.is_file():
        raise EvalError(f"scoring contract does not exist: {path}")
    contract = load_json(path)
    if not isinstance(contract, dict):
        raise EvalError(f"{path}: scoring contract must be an object")
    if contract.get("version") != 1:
        raise EvalError(f"{path}: scoring contract version must be 1")

    release_gate = contract.get("release_gate")
    if not isinstance(release_gate, dict):
        raise EvalError(f"{path}: release_gate must be an object")
    gate_metrics = release_gate.get("metrics")
    if not isinstance(gate_metrics, list) or not gate_metrics:
        raise EvalError(f"{path}: release_gate.metrics must be a non-empty list")

    seen_ids: set[str] = set()
    for index, metric in enumerate(gate_metrics, start=1):
        if not isinstance(metric, dict):
            raise EvalError(f"{path}: release_gate.metrics[{index}] must be an object")
        validate_gate_metric(metric, path, "release_gate")
        metric_id = metric["id"]
        if metric_id in seen_ids:
            raise EvalError(f"{path}: duplicate release gate metric id: {metric_id}")
        seen_ids.add(metric_id)
        if metric.get("operator") not in SUPPORTED_OPERATORS:
            raise EvalError(f"{path}: release gate metric {metric_id} has unsupported operator")
        if not isinstance(metric.get("threshold"), (int, float)):
            raise EvalError(f"{path}: release gate metric {metric_id} threshold must be numeric")
        null_policy = metric.get("null_policy", "fail")
        if null_policy not in SUPPORTED_NULL_POLICIES:
            raise EvalError(
                f"{path}: release gate metric {metric_id} has unsupported null_policy"
            )

    report_only = release_gate.get("report_only_metrics", [])
    if not isinstance(report_only, list):
        raise EvalError(f"{path}: release_gate.report_only_metrics must be a list")
    report_only_ids: set[str] = set()
    for index, metric in enumerate(report_only, start=1):
        if not isinstance(metric, dict):
            raise EvalError(f"{path}: release_gate.report_only_metrics[{index}] must be an object")
        validate_gate_metric(metric, path, "report_only")
        metric_id = metric["id"]
        if metric_id in seen_ids or metric_id in report_only_ids:
            raise EvalError(f"{path}: duplicate report-only metric id: {metric_id}")
        report_only_ids.add(metric_id)

    task_minimums = contract.get("task_minimums")
    if not isinstance(task_minimums, dict):
        raise EvalError(f"{path}: task_minimums must be an object")
    defaults = task_minimums.get("defaults_by_category", {})
    overrides = task_minimums.get("overrides_by_task", {})
    if not isinstance(defaults, dict) or not isinstance(overrides, dict):
        raise EvalError(f"{path}: task_minimums defaults_by_category and overrides_by_task must be objects")

    for task in tasks:
        expected = {}
        if task["category"] in defaults:
            category_default = defaults[task["category"]]
            if not isinstance(category_default, dict):
                raise EvalError(f"{path}: default for category {task['category']} must be an object")
            expected.update(category_default)
        if task["id"] in overrides:
            task_override = overrides[task["id"]]
            if not isinstance(task_override, dict):
                raise EvalError(f"{path}: override for task {task['id']} must be an object")
            expected.update(task_override)
        if not expected:
            raise EvalError(
                f"{path}: task_minimums must define category default or task override for {task['id']}"
            )
        minimum = expected.get("minimum_score")
        if not isinstance(minimum, (int, float)):
            raise EvalError(f"{path}: minimum_score missing for task {task['id']}")
        if not floats_equal(task["grading"].get("minimum_score"), minimum):
            raise EvalError(
                f"{path}: task {task['id']} minimum_score "
                f"{task['grading'].get('minimum_score')} does not match contract {minimum}"
            )
        expected_bug_rate = expected.get("minimum_bug_catch_rate")
        task_bug_rate = task["grading"].get("minimum_bug_catch_rate")
        if expected_bug_rate is not None and not isinstance(expected_bug_rate, (int, float)):
            raise EvalError(f"{path}: minimum_bug_catch_rate for task {task['id']} must be numeric")
        if not floats_equal(task_bug_rate, expected_bug_rate):
            raise EvalError(
                f"{path}: task {task['id']} minimum_bug_catch_rate "
                f"{task_bug_rate} does not match contract {expected_bug_rate}"
            )

    return contract


def filter_tasks(tasks: list[dict[str, Any]], task_ids: list[str] | None) -> list[dict[str, Any]]:
    if not task_ids:
        return tasks

    requested = set(task_ids)
    selected = [task for task in tasks if task["id"] in requested]
    found = {task["id"] for task in selected}
    missing = sorted(requested - found)
    if missing:
        raise EvalError(f"unknown task id(s): {', '.join(missing)}")
    return selected


def artifact_paths(task: dict[str, Any], attempt_dir: Path) -> dict[str, Path]:
    contract = {
        "workspace": "workspace",
        "transcript": "transcript.md",
        "review": "review.md",
        "metrics": "metrics.json",
    }
    contract.update(task.get("artifact_contract", {}))
    return {
        name: attempt_dir / safe_rel_path(raw_path, f"artifact_contract.{name}")
        for name, raw_path in contract.items()
    }


def discover_attempts(run_dir: Path, task: dict[str, Any]) -> list[Path]:
    task_dir = run_dir / task["id"]
    if not task_dir.exists():
        return []

    paths = artifact_paths(task, task_dir)
    if paths["workspace"].exists() or paths["transcript"].exists() or paths["review"].exists():
        return [task_dir]

    attempts = []
    for child in sorted(path for path in task_dir.iterdir() if path.is_dir()):
        child_paths = artifact_paths(task, child)
        if (
            child_paths["workspace"].exists()
            or child_paths["transcript"].exists()
            or child_paths["review"].exists()
        ):
            attempts.append(child)
    return attempts


def result(
    check: dict[str, Any],
    status: str,
    message: str,
) -> CheckResult:
    return CheckResult(
        check_id=check["id"],
        check_type=check["type"],
        status=status,
        weight=float(check.get("weight", 1)),
        blocking=bool(check.get("blocking", False)),
        metric=check.get("metric"),
        message=message,
    )


def evaluate_check(
    check: dict[str, Any],
    paths: dict[str, Path],
    skip_commands: bool,
) -> CheckResult:
    check_type = check["type"]
    workspace = paths["workspace"]
    transcript = paths["transcript"]
    review = paths["review"]

    if check_type == "file_exists":
        target = workspace / safe_rel_path(check["path"], "path")
        return result(check, "passed" if target.exists() else "failed", str(target))

    if check_type == "file_not_exists":
        target = workspace / safe_rel_path(check["path"], "path")
        return result(check, "passed" if not target.exists() else "failed", str(target))

    if check_type in {"file_contains", "file_not_contains"}:
        target = workspace / safe_rel_path(check["path"], "path")
        text = read_text(target)
        if text is None:
            status = "failed" if check_type == "file_contains" else "passed"
            return result(check, status, f"missing file: {target}")
        found = regex_found(check["pattern"], text)
        passed = found if check_type == "file_contains" else not found
        return result(check, "passed" if passed else "failed", f"pattern in {target}")

    if check_type in {"transcript_contains", "transcript_not_contains"}:
        text = read_text(transcript)
        if text is None:
            status = "failed" if check_type == "transcript_contains" else "passed"
            return result(check, status, f"missing transcript: {transcript}")
        found = regex_found(check["pattern"], text)
        passed = found if check_type == "transcript_contains" else not found
        return result(check, "passed" if passed else "failed", "pattern in transcript")

    if check_type in {"review_contains", "review_not_contains"}:
        text = read_text(review)
        if text is None:
            status = "failed" if check_type == "review_contains" else "passed"
            return result(check, status, f"missing review: {review}")
        found = regex_found(check["pattern"], text)
        passed = found if check_type == "review_contains" else not found
        return result(check, "passed" if passed else "failed", "pattern in review")

    if check_type in {"workspace_contains", "workspace_not_contains"}:
        text = iter_workspace_text(workspace)
        found = regex_found(check["pattern"], text)
        passed = found if check_type == "workspace_contains" else not found
        return result(check, "passed" if passed else "failed", "pattern across workspace")

    if check_type == "json_valid":
        target = workspace / safe_rel_path(check["path"], "path")
        if not target.is_file():
            return result(check, "failed", f"missing JSON file: {target}")
        try:
            load_json(target)
        except EvalError as error:
            return result(check, "failed", str(error))
        return result(check, "passed", f"valid JSON: {target}")

    if check_type == "command_succeeds":
        if skip_commands:
            return result(check, "skipped", "command checks skipped")
        if not workspace.is_dir():
            return result(check, "failed", f"missing workspace: {workspace}")
        timeout = int(check.get("timeout_seconds", 30))
        try:
            completed = subprocess.run(
                check["command"],
                cwd=workspace,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return result(check, "failed", f"command timed out after {timeout}s")
        if completed.returncode == 0:
            return result(check, "passed", "command exited 0")
        output = completed.stdout.strip().splitlines()
        tail = " | ".join(output[-3:])
        return result(check, "failed", f"exit {completed.returncode}: {tail}")

    raise EvalError(f"unreachable unsupported check type: {check_type}")


def load_metrics(paths: dict[str, Path]) -> dict[str, Any]:
    metrics_path = paths["metrics"]
    if not metrics_path.is_file():
        return {}
    data = load_json(metrics_path)
    if not isinstance(data, dict):
        raise EvalError(f"{metrics_path}: metrics JSON must be an object")
    return data


def evaluate_findings(task: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    findings = task.get("expected_findings", [])
    if not findings:
        return {"found": 0, "total": 0, "rate": None, "missed": []}
    review_text = read_text(paths["review"]) or ""
    found = []
    missed = []
    for finding in findings:
        if regex_found(finding["pattern"], review_text):
            found.append(finding["id"])
        else:
            missed.append(finding["id"])
    return {
        "found": len(found),
        "total": len(findings),
        "rate": len(found) / len(findings),
        "missed": missed,
    }


def evaluate_attempt(
    task: dict[str, Any],
    attempt_dir: Path,
    skip_commands: bool,
) -> dict[str, Any]:
    paths = artifact_paths(task, attempt_dir)
    check_results = [evaluate_check(check, paths, skip_commands) for check in task["checks"]]
    metric_names = sorted({check.metric for check in check_results if check.metric})
    considered = [check for check in check_results if not check.skipped]
    passed_weight = sum(check.weight for check in considered if check.passed)
    total_weight = sum(check.weight for check in considered)
    score = passed_weight / total_weight if total_weight else 0.0
    blocking_failures = [check for check in check_results if check.failed and check.blocking]
    findings = evaluate_findings(task, paths)
    minimum_bug_rate = task["grading"].get("minimum_bug_catch_rate")
    bug_rate_ok = minimum_bug_rate is None or (
        findings["rate"] is not None and findings["rate"] >= minimum_bug_rate
    )
    passed = (
        score >= task["grading"]["minimum_score"]
        and not blocking_failures
        and bug_rate_ok
    )

    metrics = load_metrics(paths)
    return {
        "attempt": attempt_dir.name,
        "passed": passed,
        "score": round(score, 4),
        "checks_passed": sum(1 for check in check_results if check.passed),
        "checks_failed": sum(1 for check in check_results if check.failed),
        "checks_skipped": sum(1 for check in check_results if check.skipped),
        "blocking_failures": [check.check_id for check in blocking_failures],
        "failed_checks": [
            {
                "id": check.check_id,
                "type": check.check_type,
                "message": check.message,
            }
            for check in check_results
            if check.failed
        ],
        "rule_violation_count": sum(
            1 for check in check_results if check.failed and check.metric == "rule_violation"
        ),
        "metric_applicability": metric_names,
        "metric_pass": {
            metric: any(check.passed and check.metric == metric for check in check_results)
            for metric in metric_names
        },
        "doctor_pass": any(check.passed and check.metric == "doctor_pass" for check in check_results),
        "verification_evidence": any(
            check.passed and check.metric == "verification_evidence" for check in check_results
        ),
        "review_findings": findings,
        "metrics": {
            key: metrics[key]
            for key in ("tokens", "cost_usd", "duration_seconds")
            if isinstance(metrics.get(key), (int, float))
        },
    }


def grade_run(tasks: list[dict[str, Any]], run_dir: Path, skip_commands: bool) -> dict[str, Any]:
    task_results = []
    for task in tasks:
        attempts = discover_attempts(run_dir, task)
        if not attempts:
            task_results.append(
                {
                    "id": task["id"],
                    "category": task["category"],
                    "attempts": [],
                    "pass_at_1": False,
                    "pass_power_3": None,
                    "pass_power_5": None,
                    "missing": True,
                }
            )
            continue

        attempt_results = [
            evaluate_attempt(task, attempt, skip_commands) for attempt in attempts
        ]
        first = attempt_results[0]
        task_results.append(
            {
                "id": task["id"],
                "category": task["category"],
                "attempts": attempt_results,
                "pass_at_1": first["passed"],
                "pass_power_3": (
                    all(attempt["passed"] for attempt in attempt_results[:3])
                    if len(attempt_results) >= 3
                    else None
                ),
                "pass_power_5": (
                    all(attempt["passed"] for attempt in attempt_results[:5])
                    if len(attempt_results) >= 5
                    else None
                ),
                "missing": False,
            }
        )

    attempts_flat = [
        attempt for task in task_results for attempt in task.get("attempts", [])
    ]
    total_checks = sum(
        attempt["checks_passed"] + attempt["checks_failed"] for attempt in attempts_flat
    )
    passed_checks = sum(attempt["checks_passed"] for attempt in attempts_flat)
    finding_total = sum(attempt["review_findings"]["total"] for attempt in attempts_flat)
    finding_found = sum(attempt["review_findings"]["found"] for attempt in attempts_flat)
    flaky_tasks = [
        task
        for task in task_results
        if len(task.get("attempts", [])) > 1
        and len({attempt["passed"] for attempt in task["attempts"]}) > 1
    ]
    numeric_metrics = {
        key: [
            attempt["metrics"][key]
            for attempt in attempts_flat
            if key in attempt["metrics"]
        ]
        for key in ("tokens", "cost_usd", "duration_seconds")
    }
    doctor_values = metric_values(attempts_flat, "doctor_pass")
    verification_values = metric_values(attempts_flat, "verification_evidence")

    summary = {
        "task_count": len(tasks),
        "attempt_count": len(attempts_flat),
        "pass_at_1": sum(1 for task in task_results if task["pass_at_1"]) / len(tasks),
        "pass_power_3": rate(
            task["pass_power_3"] for task in task_results if task["pass_power_3"] is not None
        ),
        "pass_power_5": rate(
            task["pass_power_5"] for task in task_results if task["pass_power_5"] is not None
        ),
        "regression_pass_rate": passed_checks / total_checks if total_checks else None,
        "rule_violation_count": sum(
            attempt["rule_violation_count"] for attempt in attempts_flat
        ),
        "blocking_failure_count": sum(
            len(attempt["blocking_failures"]) for attempt in attempts_flat
        ),
        "doctor_pass_rate": rate(doctor_values),
        "doctor_pass_applicable_attempts": len(doctor_values),
        "verification_evidence_rate": rate(verification_values),
        "verification_evidence_applicable_attempts": len(verification_values),
        "reviewer_bug_catch_rate": (
            finding_found / finding_total if finding_total else None
        ),
        "flaky_task_rate": len(flaky_tasks) / len(task_results) if task_results else None,
        "tokens_per_attempt": average(numeric_metrics["tokens"]),
        "cost_usd_per_attempt": average(numeric_metrics["cost_usd"]),
        "seconds_per_attempt": average(numeric_metrics["duration_seconds"]),
    }
    return {"summary": summary, "tasks": task_results}


def metric_values(attempts: list[dict[str, Any]], metric: str) -> list[bool]:
    return [
        attempt["metric_pass"][metric]
        for attempt in attempts
        if metric in attempt["metric_applicability"]
    ]


def rate(values: Any) -> float | None:
    values = list(values)
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def contract_path(args: argparse.Namespace) -> Path | None:
    if args.no_scoring_contract:
        return None
    if args.scoring_contract:
        return args.scoring_contract
    if DEFAULT_SCORING_CONTRACT.is_file():
        return DEFAULT_SCORING_CONTRACT
    return None


def compare_metric(value: float | int, operator: str, threshold: float | int) -> bool:
    if operator == "==":
        return floats_equal(value, threshold)
    if operator == ">=":
        return value >= threshold
    if operator == "<=":
        return value <= threshold
    if operator == ">":
        return value > threshold
    if operator == "<":
        return value < threshold
    raise EvalError(f"unsupported release gate operator: {operator}")


def evaluate_release_gate(report: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    summary = report["summary"]
    results = []
    for metric in contract["release_gate"]["metrics"]:
        value = summary.get(metric["summary_key"])
        null_policy = metric.get("null_policy", "fail")
        if value is None:
            if null_policy == "skip_without_applicable_tasks":
                status = "skipped"
            elif null_policy == "pass":
                status = "passed"
            else:
                status = "failed"
        else:
            status = (
                "passed"
                if compare_metric(value, metric["operator"], metric["threshold"])
                else "failed"
            )
        results.append(
            {
                "id": metric["id"],
                "summary_key": metric["summary_key"],
                "value": value,
                "operator": metric["operator"],
                "threshold": metric["threshold"],
                "status": status,
                "rationale": metric.get("rationale"),
            }
        )

    return {
        "name": contract["release_gate"].get("name", "release-gate"),
        "passed": all(result["status"] != "failed" for result in results),
        "results": results,
    }


def attach_release_gate(report: dict[str, Any], contract: dict[str, Any] | None) -> None:
    if contract is not None:
        report["release_gate"] = evaluate_release_gate(report, contract)


def print_suite_summary(tasks: list[dict[str, Any]]) -> None:
    categories = sorted({task["category"] for task in tasks})
    print(f"eval suite valid: {len(tasks)} task(s), {len(categories)} categor(ies)")
    for category in categories:
        count = sum(1 for task in tasks if task["category"] == category)
        print(f"ok: {category}: {count} task(s)")


def fmt_rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def print_run_summary(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(f"tasks: {summary['task_count']}")
    print(f"attempts: {summary['attempt_count']}")
    print(f"pass@1: {fmt_rate(summary['pass_at_1'])}")
    print(f"pass^3: {fmt_rate(summary['pass_power_3'])}")
    print(f"pass^5: {fmt_rate(summary['pass_power_5'])}")
    print(f"regression pass rate: {fmt_rate(summary['regression_pass_rate'])}")
    print(f"doctor pass rate: {fmt_rate(summary['doctor_pass_rate'])}")
    print(f"verification evidence rate: {fmt_rate(summary['verification_evidence_rate'])}")
    print(f"reviewer bug-catch rate: {fmt_rate(summary['reviewer_bug_catch_rate'])}")
    print(f"flaky task rate: {fmt_rate(summary['flaky_task_rate'])}")
    print(f"blocking failure count: {summary['blocking_failure_count']}")
    print(f"rule violation count: {summary['rule_violation_count']}")

    if "release_gate" in report:
        gate = report["release_gate"]
        print(f"release gate: {'passed' if gate['passed'] else 'failed'} ({gate['name']})")
        failed_gates = [
            result for result in gate["results"] if result["status"] == "failed"
        ]
        if failed_gates:
            print("release gate failures:")
            for result in failed_gates:
                print(
                    f"- {result['id']}: {result['value']} "
                    f"{result['operator']} {result['threshold']}"
                )

    failed = []
    for task in report["tasks"]:
        if task.get("missing"):
            failed.append(f"{task['id']}: missing run artifact")
            continue
        for attempt in task["attempts"]:
            if not attempt["passed"]:
                failed.append(f"{task['id']}/{attempt['attempt']}: score {attempt['score']}")
    if failed:
        print("failed:")
        for item in failed:
            print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-dir", type=Path, default=DEFAULT_TASKS_DIR)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument(
        "--task-id",
        action="append",
        help="only evaluate the named task; may be provided multiple times",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--skip-commands", action="store_true", help="skip command_succeeds checks")
    parser.add_argument("--check-suite", action="store_true", help="validate task schema only")
    parser.add_argument(
        "--scoring-contract",
        type=Path,
        help="validate and apply a scoring contract JSON file",
    )
    parser.add_argument(
        "--no-scoring-contract",
        action="store_true",
        help="ignore the default scoring contract when grading a run",
    )
    args = parser.parse_args()

    try:
        tasks = filter_tasks(load_tasks(args.tasks_dir), args.task_id)
        scoring_contract_path = contract_path(args)
        scoring_contract = (
            validate_scoring_contract(scoring_contract_path, tasks)
            if scoring_contract_path
            else None
        )
        if args.run_dir and not args.check_suite:
            report = grade_run(tasks, args.run_dir, args.skip_commands)
            attach_release_gate(report, scoring_contract)
            if args.json:
                print(json.dumps(report, indent=2, ensure_ascii=False))
            else:
                print_run_summary(report)
            if "release_gate" in report:
                return 0 if report["release_gate"]["passed"] else 1
            return 0 if all(task["pass_at_1"] for task in report["tasks"]) else 1

        if args.json:
            print(
                json.dumps(
                    {
                        "tasks": len(tasks),
                        "ids": [task["id"] for task in tasks],
                        "scoring_contract": str(scoring_contract_path)
                        if scoring_contract_path
                        else None,
                    }
                )
            )
        else:
            print_suite_summary(tasks)
            if scoring_contract_path:
                print(f"scoring contract valid: {scoring_contract_path}")
            print("no run dir supplied; suite validation only")
        return 0
    except EvalError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
