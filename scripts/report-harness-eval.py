#!/usr/bin/env python3
"""Create weekly reports from Flowverse Conductor harness eval artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCORING_CONTRACT = ROOT / "evals" / "scoring-contract.json"

RATE_KEYS = [
    "pass_at_1",
    "pass_power_3",
    "pass_power_5",
    "regression_pass_rate",
    "doctor_pass_rate",
    "verification_evidence_rate",
    "reviewer_bug_catch_rate",
]
COUNT_KEYS = [
    "blocking_failure_count",
    "rule_violation_count",
]
SPIKE_KEYS = [
    "flaky_task_rate",
    "tokens_per_attempt",
    "cost_usd_per_attempt",
    "seconds_per_attempt",
]
HEADLINE_KEYS = [
    "pass_at_1",
    "regression_pass_rate",
    "doctor_pass_rate",
    "verification_evidence_rate",
    "reviewer_bug_catch_rate",
    "blocking_failure_count",
    "rule_violation_count",
    "flaky_task_rate",
    "cost_usd_per_attempt",
    "seconds_per_attempt",
]


class ReportError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path, *, required: bool = True) -> Any:
    if not path.is_file():
        if required:
            raise ReportError(f"missing JSON file: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ReportError(f"{path}: invalid JSON: {error}") from error


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_mapping(items: dict[str, str | None]) -> str | None:
    if not items:
        return None
    hasher = hashlib.sha256()
    for key in sorted(items):
        hasher.update(key.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update((items[key] or "").encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


def safe_number(value: Any) -> float | int | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def fmt_value(value: Any, key: str | None = None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "pass" if value else "fail"
    if isinstance(value, (int, float)):
        if key and ("rate" in key or key in {"pass_at_1", "pass_power_3", "pass_power_5", "flaky_task_rate"}):
            return f"{value:.2%}"
        if key and "cost" in key:
            return f"${value:.4f}"
        if key and ("seconds" in key or "duration" in key):
            return f"{value:.1f}s"
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.4f}"
    return str(value)


def fmt_delta(current: Any, previous: Any, key: str) -> str:
    current_number = safe_number(current)
    previous_number = safe_number(previous)
    if current_number is None or previous_number is None:
        return "n/a"
    delta = float(current_number) - float(previous_number)
    if abs(delta) < 1e-12:
        return "0"
    if "rate" in key or key in {"pass_at_1", "pass_power_3", "pass_power_5", "flaky_task_rate"}:
        return f"{delta:+.2%}"
    if "cost" in key:
        return f"{delta:+.4f}"
    if "seconds" in key or "duration" in key:
        return f"{delta:+.1f}s"
    return f"{delta:+.4f}"


def empty_grader_report(manifest: dict[str, Any]) -> dict[str, Any]:
    task_ids = manifest.get("task_ids") if isinstance(manifest.get("task_ids"), list) else []
    tasks = [
        {
            "id": task_id,
            "category": "unknown",
            "attempts": [],
            "pass_at_1": False,
            "pass_power_3": None,
            "pass_power_5": None,
            "missing": True,
        }
        for task_id in task_ids
        if isinstance(task_id, str)
    ]
    return {
        "summary": {
            "task_count": len(tasks),
            "attempt_count": 0,
            "pass_at_1": 0.0 if tasks else None,
            "pass_power_3": None,
            "pass_power_5": None,
            "regression_pass_rate": None,
            "rule_violation_count": 0,
            "blocking_failure_count": 0,
            "doctor_pass_rate": None,
            "doctor_pass_applicable_attempts": 0,
            "verification_evidence_rate": None,
            "verification_evidence_applicable_attempts": 0,
            "reviewer_bug_catch_rate": None,
            "flaky_task_rate": None,
            "tokens_per_attempt": None,
            "cost_usd_per_attempt": None,
            "seconds_per_attempt": None,
        },
        "tasks": tasks,
        "report_errors": ["grader-report.json is missing; created manifest-only report"],
    }


def load_attempt_digests(run_dir: Path) -> dict[str, str | None]:
    digests: dict[str, str | None] = {}
    for attempt_path in sorted(run_dir.glob("*/run-*/attempt.json")):
        data = read_json(attempt_path, required=False)
        if not isinstance(data, dict):
            continue
        task_id = data.get("task_id")
        if isinstance(task_id, str) and task_id not in digests:
            digest = data.get("task_digest")
            digests[task_id] = digest if isinstance(digest, str) else None
    return digests


def load_task_file_digests(tasks_dir: Path, task_ids: list[str]) -> dict[str, str | None]:
    digests: dict[str, str | None] = {}
    if not tasks_dir.is_dir():
        return digests
    for task_id in task_ids:
        digest = sha256_file(tasks_dir / f"{task_id}.json")
        if digest is not None:
            digests[task_id] = digest
    return digests


def build_identity(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    task_ids = [task_id for task_id in manifest.get("task_ids", []) if isinstance(task_id, str)]
    task_digests = load_attempt_digests(run_dir)
    tasks_dir_raw = manifest.get("tasks_dir")
    if isinstance(tasks_dir_raw, str):
        task_digests.update(
            {
                task_id: digest
                for task_id, digest in load_task_file_digests(Path(tasks_dir_raw), task_ids).items()
                if task_id not in task_digests
            }
        )

    return {
        "suite_digest": digest_mapping(task_digests),
        "task_digests": task_digests,
        "scoring_contract_digest": sha256_file(DEFAULT_SCORING_CONTRACT),
    }


def failed_attempts(report: dict[str, Any]) -> list[dict[str, Any]]:
    failures = []
    for task in report.get("tasks", []):
        task_id = task.get("id")
        if task.get("missing"):
            failures.append(
                {
                    "task_id": task_id,
                    "attempt": None,
                    "category": task.get("category"),
                    "score": None,
                    "blocking_failures": [],
                    "failed_checks": [],
                    "reason": "missing run artifact",
                }
            )
            continue
        for attempt in task.get("attempts", []):
            if attempt.get("passed"):
                continue
            failures.append(
                {
                    "task_id": task_id,
                    "attempt": attempt.get("attempt"),
                    "category": task.get("category"),
                    "score": attempt.get("score"),
                    "blocking_failures": attempt.get("blocking_failures", []),
                    "failed_checks": [
                        item.get("id")
                        for item in attempt.get("failed_checks", [])
                        if isinstance(item, dict)
                    ],
                    "reason": "attempt failed",
                }
            )
    return failures


def summarize_tasks(report: dict[str, Any]) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for task in report.get("tasks", []):
        attempts = task.get("attempts", [])
        first = attempts[0] if attempts else {}
        summaries[task["id"]] = {
            "category": task.get("category"),
            "missing": bool(task.get("missing", False)),
            "pass_at_1": task.get("pass_at_1"),
            "pass_power_3": task.get("pass_power_3"),
            "pass_power_5": task.get("pass_power_5"),
            "attempt_count": len(attempts),
            "first_score": first.get("score"),
            "failed_attempt_count": sum(1 for attempt in attempts if not attempt.get("passed")),
            "blocking_failure_count": sum(
                len(attempt.get("blocking_failures", [])) for attempt in attempts
            ),
            "rule_violation_count": sum(
                attempt.get("rule_violation_count", 0) for attempt in attempts
            ),
        }
    return summaries


def summarize_categories(report: dict[str, Any]) -> dict[str, Any]:
    categories: dict[str, dict[str, Any]] = {}
    for task in report.get("tasks", []):
        category = task.get("category") or "unknown"
        entry = categories.setdefault(
            category,
            {
                "task_count": 0,
                "pass_at_1_count": 0,
                "missing_count": 0,
                "failed_attempt_count": 0,
                "blocking_failure_count": 0,
                "rule_violation_count": 0,
                "first_scores": [],
            },
        )
        attempts = task.get("attempts", [])
        entry["task_count"] += 1
        entry["pass_at_1_count"] += 1 if task.get("pass_at_1") else 0
        entry["missing_count"] += 1 if task.get("missing") else 0
        for attempt in attempts:
            entry["failed_attempt_count"] += 1 if not attempt.get("passed") else 0
            entry["blocking_failure_count"] += len(attempt.get("blocking_failures", []))
            entry["rule_violation_count"] += attempt.get("rule_violation_count", 0)
        if attempts and safe_number(attempts[0].get("score")) is not None:
            entry["first_scores"].append(attempts[0]["score"])

    for entry in categories.values():
        scores = entry.pop("first_scores")
        entry["pass_at_1_rate"] = (
            entry["pass_at_1_count"] / entry["task_count"] if entry["task_count"] else None
        )
        entry["average_first_score"] = sum(scores) / len(scores) if scores else None
    return categories


def summarize_cost_time(report: dict[str, Any]) -> dict[str, Any]:
    attempts = [
        attempt
        for task in report.get("tasks", [])
        for attempt in task.get("attempts", [])
    ]
    totals = {"tokens": 0.0, "cost_usd": 0.0, "duration_seconds": 0.0}
    coverage = {"tokens": 0, "cost_usd": 0, "duration_seconds": 0}
    for attempt in attempts:
        metrics = attempt.get("metrics", {})
        for key in totals:
            value = safe_number(metrics.get(key))
            if value is not None:
                totals[key] += float(value)
                coverage[key] += 1

    attempt_count = len(attempts)
    return {
        "attempt_count": attempt_count,
        "total_tokens": int(totals["tokens"]) if coverage["tokens"] else None,
        "total_cost_usd": round(totals["cost_usd"], 6) if coverage["cost_usd"] else None,
        "total_duration_seconds": round(totals["duration_seconds"], 3)
        if coverage["duration_seconds"]
        else None,
        "metric_coverage": {
            key: {
                "attempts_with_metric": count,
                "attempt_count": attempt_count,
                "rate": count / attempt_count if attempt_count else None,
            }
            for key, count in coverage.items()
        },
    }


def release_gate_summary(report: dict[str, Any]) -> dict[str, Any]:
    gate = report.get("release_gate")
    if not isinstance(gate, dict):
        return {
            "name": None,
            "passed": None,
            "failed_metric_ids": [],
            "results": [],
        }
    results = gate.get("results", [])
    failed_ids = [
        item.get("id")
        for item in results
        if isinstance(item, dict) and item.get("status") == "failed"
    ]
    return {
        "name": gate.get("name"),
        "passed": gate.get("passed"),
        "failed_metric_ids": failed_ids,
        "results": results,
    }


def compare_summaries(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    if not previous:
        return {
            "has_regressions": False,
            "baseline": "none",
            "release_gate": {},
            "tasks": [],
            "metrics": [],
            "cost_time_spikes": [],
        }

    regressions: dict[str, Any] = {
        "has_regressions": False,
        "baseline": previous.get("generated_at"),
        "release_gate": {
            "previous_passed": previous.get("release_gate", {}).get("passed"),
            "current_passed": current.get("release_gate", {}).get("passed"),
            "new_failed_metric_ids": [],
        },
        "tasks": [],
        "metrics": [],
        "cost_time_spikes": [],
    }

    previous_failed_gate = set(previous.get("release_gate", {}).get("failed_metric_ids", []))
    current_failed_gate = set(current.get("release_gate", {}).get("failed_metric_ids", []))
    regressions["release_gate"]["new_failed_metric_ids"] = sorted(
        current_failed_gate - previous_failed_gate
    )
    if (
        previous.get("release_gate", {}).get("passed") is True
        and current.get("release_gate", {}).get("passed") is False
    ):
        regressions["release_gate"]["status_regressed"] = True

    previous_tasks = previous.get("tasks", {})
    for task_id, task in current.get("tasks", {}).items():
        old_task = previous_tasks.get(task_id, {})
        if old_task.get("pass_at_1") is True and task.get("pass_at_1") is False:
            regressions["tasks"].append(
                {
                    "task_id": task_id,
                    "category": task.get("category"),
                    "previous_pass_at_1": True,
                    "current_pass_at_1": task.get("pass_at_1"),
                    "current_first_score": task.get("first_score"),
                    "missing": task.get("missing"),
                }
            )

    current_metrics = current.get("metrics", {})
    previous_metrics = previous.get("metrics", {})
    for key in RATE_KEYS:
        current_value = safe_number(current_metrics.get(key))
        previous_value = safe_number(previous_metrics.get(key))
        if current_value is not None and previous_value is not None and current_value < previous_value:
            regressions["metrics"].append(
                {
                    "summary_key": key,
                    "direction": "down",
                    "previous": previous_value,
                    "current": current_value,
                    "delta": current_value - previous_value,
                }
            )
    for key in COUNT_KEYS:
        current_value = safe_number(current_metrics.get(key))
        previous_value = safe_number(previous_metrics.get(key))
        if current_value is not None and previous_value is not None and current_value > previous_value:
            regressions["metrics"].append(
                {
                    "summary_key": key,
                    "direction": "up",
                    "previous": previous_value,
                    "current": current_value,
                    "delta": current_value - previous_value,
                }
            )
    for key in SPIKE_KEYS:
        current_value = safe_number(current_metrics.get(key))
        previous_value = safe_number(previous_metrics.get(key))
        if (
            current_value is not None
            and previous_value is not None
            and previous_value > 0
            and current_value > previous_value * 1.2
        ):
            regressions["cost_time_spikes"].append(
                {
                    "summary_key": key,
                    "previous": previous_value,
                    "current": current_value,
                    "delta": current_value - previous_value,
                    "relative_delta": (current_value - previous_value) / previous_value,
                }
            )

    regressions["has_regressions"] = bool(
        regressions["release_gate"].get("new_failed_metric_ids")
        or regressions["release_gate"].get("status_regressed")
        or regressions["tasks"]
        or regressions["metrics"]
        or regressions["cost_time_spikes"]
    )
    return regressions


def build_weekly_summary(
    run_dir: Path,
    manifest: dict[str, Any],
    grader_report: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    gate = release_gate_summary(grader_report)
    weekly = {
        "version": 1,
        "kind": "harness_weekly_eval_summary",
        "generated_at": utc_now(),
        "run_dir": str(run_dir),
        "run": {
            "provider": manifest.get("provider"),
            "model": manifest.get("model"),
            "dry_run": manifest.get("dry_run"),
            "tasks_dir": manifest.get("tasks_dir"),
            "task_ids": manifest.get("task_ids", []),
            "attempts_per_task": manifest.get("attempts_per_task"),
            "source_root": manifest.get("source_root"),
            "source_commit": manifest.get("source_commit"),
            "source_dirty": manifest.get("source_dirty"),
            "started_at": manifest.get("started_at"),
            "ended_at": manifest.get("ended_at"),
            "grader_exit_code": manifest.get("grader_exit_code"),
        },
        "identity": build_identity(run_dir, manifest),
        "release_gate": gate,
        "metrics": grader_report.get("summary", {}),
        "categories": summarize_categories(grader_report),
        "tasks": summarize_tasks(grader_report),
        "failures": {
            "release_gate_failures": [
                item for item in gate["results"] if item.get("status") == "failed"
            ],
            "failed_attempts": failed_attempts(grader_report),
        },
        "cost_time": summarize_cost_time(grader_report),
        "report_errors": grader_report.get("report_errors", []),
    }
    weekly["regressions"] = compare_summaries(weekly, previous)
    return weekly


def render_markdown(summary: dict[str, Any], previous: dict[str, Any] | None) -> str:
    gate = summary["release_gate"]
    gate_status = "unknown"
    if gate.get("passed") is True:
        gate_status = "passed"
    elif gate.get("passed") is False:
        gate_status = "failed"

    lines = [
        "# Harness Weekly Eval Report",
        "",
        f"Generated: {summary['generated_at']}",
        f"Release gate: {gate_status}",
        f"Provider: {summary['run'].get('provider') or 'unknown'}",
        f"Model: {summary['run'].get('model') or 'default'}",
        f"Source commit: {summary['run'].get('source_commit') or 'unknown'}",
        f"Source dirty: {summary['run'].get('source_dirty')}",
        f"Previous baseline: {previous.get('generated_at') if previous else 'none'}",
        "",
        "## Headline Metrics",
        "",
        "| Metric | Current | Previous | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    previous_metrics = previous.get("metrics", {}) if previous else {}
    for key in HEADLINE_KEYS:
        current_value = summary["metrics"].get(key)
        previous_value = previous_metrics.get(key)
        lines.append(
            f"| `{key}` | {fmt_value(current_value, key)} | "
            f"{fmt_value(previous_value, key)} | {fmt_delta(current_value, previous_value, key)} |"
        )

    lines.extend(["", "## Release Gate", ""])
    if gate["results"]:
        lines.extend(["| Gate | Status | Value | Target |", "| --- | --- | ---: | --- |"])
        for item in gate["results"]:
            target = f"{item.get('operator')} {fmt_value(item.get('threshold'), item.get('summary_key'))}"
            lines.append(
                f"| `{item.get('id')}` | {item.get('status')} | "
                f"{fmt_value(item.get('value'), item.get('summary_key'))} | {target} |"
            )
    else:
        lines.append("No release gate results were found.")

    regressions = summary["regressions"]
    lines.extend(["", "## Regressions", ""])
    if not previous:
        lines.append("No previous weekly summary was supplied.")
    elif not regressions["has_regressions"]:
        lines.append("No regressions detected against the previous weekly summary.")
    else:
        if regressions["release_gate"].get("new_failed_metric_ids"):
            joined = ", ".join(f"`{item}`" for item in regressions["release_gate"]["new_failed_metric_ids"])
            lines.append(f"- New release gate failures: {joined}")
        if regressions["tasks"]:
            lines.append("- Tasks regressed from pass@1 to fail:")
            for item in regressions["tasks"]:
                lines.append(
                    f"  - `{item['task_id']}` ({item.get('category')}), "
                    f"score {fmt_value(item.get('current_first_score'))}"
                )
        if regressions["metrics"]:
            lines.append("- Metric regressions:")
            for item in regressions["metrics"]:
                lines.append(
                    f"  - `{item['summary_key']}` {fmt_value(item['previous'], item['summary_key'])} "
                    f"-> {fmt_value(item['current'], item['summary_key'])}"
                )
        if regressions["cost_time_spikes"]:
            lines.append("- Cost/time spikes over 20%:")
            for item in regressions["cost_time_spikes"]:
                lines.append(
                    f"  - `{item['summary_key']}` {fmt_value(item['previous'], item['summary_key'])} "
                    f"-> {fmt_value(item['current'], item['summary_key'])}"
                )

    failures = summary["failures"]["failed_attempts"]
    lines.extend(["", "## Failed Attempts", ""])
    if failures:
        for item in failures:
            attempt = item.get("attempt") or "missing"
            checks = ", ".join(f"`{check}`" for check in item.get("failed_checks", []) if check)
            blocking = ", ".join(f"`{check}`" for check in item.get("blocking_failures", []) if check)
            details = []
            if blocking:
                details.append(f"blocking: {blocking}")
            if checks:
                details.append(f"failed checks: {checks}")
            suffix = f" ({'; '.join(details)})" if details else ""
            lines.append(
                f"- `{item.get('task_id')}/{attempt}` score {fmt_value(item.get('score'))}: "
                f"{item.get('reason')}{suffix}"
            )
    else:
        lines.append("No failed attempts.")

    cost_time = summary["cost_time"]
    lines.extend(
        [
            "",
            "## Cost And Time",
            "",
            f"- Attempts: {cost_time['attempt_count']}",
            f"- Total tokens: {fmt_value(cost_time['total_tokens'])}",
            f"- Total cost: {fmt_value(cost_time['total_cost_usd'], 'cost_usd')}",
            f"- Total duration: {fmt_value(cost_time['total_duration_seconds'], 'duration_seconds')}",
        ]
    )

    if summary.get("report_errors"):
        lines.extend(["", "## Report Errors", ""])
        for error in summary["report_errors"]:
            lines.append(f"- {error}")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--previous-summary", type=Path)
    parser.add_argument("--summary-out", type=Path)
    parser.add_argument("--report-out", type=Path)
    parser.add_argument("--regressions-out", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-gate", action="store_true")
    parser.add_argument("--fail-on-regression", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    if not run_dir.is_dir():
        raise ReportError(f"run directory does not exist: {run_dir}")

    manifest = read_json(run_dir / "manifest.json", required=False)
    if manifest is None:
        manifest = {}
    if not isinstance(manifest, dict):
        raise ReportError(f"{run_dir / 'manifest.json'}: expected JSON object")

    grader_report = read_json(run_dir / "grader-report.json", required=False)
    if grader_report is None:
        grader_report = empty_grader_report(manifest)
    if not isinstance(grader_report, dict):
        raise ReportError(f"{run_dir / 'grader-report.json'}: expected JSON object")

    previous = None
    if args.previous_summary:
        previous = read_json(args.previous_summary, required=False)
        if previous is not None and not isinstance(previous, dict):
            raise ReportError(f"{args.previous_summary}: expected JSON object")

    summary = build_weekly_summary(run_dir, manifest, grader_report, previous)
    summary_out = args.summary_out or run_dir / "weekly-summary.json"
    report_out = args.report_out or run_dir / "weekly-report.md"
    regressions_out = args.regressions_out or run_dir / "regressions.json"

    write_json(summary_out, summary)
    write_text(report_out, render_markdown(summary, previous))
    write_json(regressions_out, summary["regressions"])

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"weekly summary: {summary_out}")
        print(f"weekly report: {report_out}")
        print(f"regressions: {regressions_out}")

    gate_failed = summary["release_gate"].get("passed") is False
    regressed = summary["regressions"].get("has_regressions") is True
    if args.fail_on_gate and gate_failed:
        return 1
    if args.fail_on_regression and regressed:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReportError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
