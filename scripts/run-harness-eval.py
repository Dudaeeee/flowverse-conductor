#!/usr/bin/env python3
"""Run Flowverse Conductor harness eval tasks and write grader artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS_DIR = ROOT / "evals" / "tasks"
GRADER = ROOT / "evals" / "graders" / "harness_eval.py"
LOCAL_ONLY_NAMES = {
    ".DS_Store",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "runs",
}


@dataclass
class AttemptResult:
    task_id: str
    attempt: str
    exit_code: int
    timed_out: bool

    @property
    def failed(self) -> bool:
        return self.exit_code != 0 or self.timed_out


class RunnerError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def today_slug() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RunnerError(f"{path}: invalid JSON: {error}") from error


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_tasks(tasks_dir: Path, task_ids: list[str] | None) -> list[dict[str, Any]]:
    if not tasks_dir.is_dir():
        raise RunnerError(f"tasks directory does not exist: {tasks_dir}")
    tasks = [read_json(path) for path in sorted(tasks_dir.glob("*.json"))]
    if not tasks:
        raise RunnerError(f"no task JSON files found in {tasks_dir}")

    if not task_ids:
        return tasks

    requested = set(task_ids)
    selected = [task for task in tasks if task.get("id") in requested]
    found = {task.get("id") for task in selected}
    missing = sorted(requested - found)
    if missing:
        raise RunnerError(f"unknown task id(s): {', '.join(missing)}")
    return selected


def suite_name(tasks_dir: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    try:
        if tasks_dir.resolve() == DEFAULT_TASKS_DIR.resolve():
            return "public"
    except FileNotFoundError:
        pass
    parent_name = tasks_dir.parent.name
    return parent_name if parent_name else "suite"


def default_run_dir(provider: str, tasks_dir: Path, explicit_suite_name: str | None) -> Path:
    return ROOT / "runs" / today_slug() / provider / suite_name(tasks_dir, explicit_suite_name)


def ignore_local_artifacts(directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    parent_name = Path(directory).name
    for name in names:
        if name in LOCAL_ONLY_NAMES:
            ignored.add(name)
        elif parent_name == "evals" and name in {"private", "private-suite", "runs"}:
            ignored.add(name)
        elif name in {"CLAUDE.local.md", "settings.local.json"}:
            ignored.add(name)
        elif name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            ignored.add(name)
        elif name.endswith(".log"):
            ignored.add(name)
    return ignored


def copy_tree(source: Path, dest: Path) -> None:
    shutil.copytree(source, dest, ignore=ignore_local_artifacts)


def git_output(args: list[str], cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def file_tree_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    hasher = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    for file_path in files:
        if any(part in LOCAL_ONLY_NAMES for part in file_path.parts):
            continue
        rel = file_path.relative_to(path).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(file_path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def task_digest(task: dict[str, Any]) -> str:
    encoded = json.dumps(task, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resolve_fixture(tasks_dir: Path, task: dict[str, Any]) -> Path | None:
    raw = task.get("fixture")
    if not raw:
        return None
    fixture = Path(raw)
    if fixture.is_absolute() or ".." in fixture.parts:
        raise RunnerError(f"{task.get('id')}: fixture must be relative to tasks parent: {raw}")
    path = (tasks_dir.parent / fixture).resolve()
    if not path.exists():
        raise RunnerError(f"{task.get('id')}: fixture does not exist: {path}")
    return path


def prepare_workspace(task: dict[str, Any], tasks_dir: Path, source_root: Path, workspace: Path) -> Path | None:
    fixture = resolve_fixture(tasks_dir, task)
    source = fixture if fixture else source_root
    copy_tree(source, workspace)
    return fixture


def artifact_contract(task: dict[str, Any]) -> dict[str, str]:
    contract = {
        "workspace": "workspace",
        "transcript": "transcript.md",
        "review": "review.md",
        "metrics": "metrics.json",
    }
    contract.update(task.get("artifact_contract", {}))
    return contract


def build_prompt(
    task: dict[str, Any],
    workspace: Path,
    source_root: Path,
    fixture: Path | None,
    attempt_id: str,
) -> str:
    fixture_line = f"Fixture copied from: {fixture}" if fixture else "Fixture: none; workspace is a copy of the source harness."
    return f"""You are running a Flowverse Conductor harness eval attempt.

Task id: {task["id"]}
Category: {task["category"]}
Attempt: {attempt_id}

Workspace:
{workspace}

Source harness:
{source_root}

{fixture_line}

User task:
{task["prompt"]}

Runner rules:
- Work only in the workspace unless the user task explicitly requires reading the source harness.
- For bootstrap or migration tasks, copy harness files from the source harness into the workspace as needed.
- Do not copy local-only source artifacts such as .git, node_modules, runs, caches, logs, or real .env files.
- Preserve fixture content unless the task explicitly asks for a safe, non-conflicting change.
- At the end, report the commands you ran, their results, skipped checks, refusals, and remaining risk.
- For review tasks, put the code-review findings in your final answer. The runner will save that final answer as review.md.
"""


def codex_command(args: argparse.Namespace, attempt_dir: Path) -> list[str]:
    command = [
        args.codex_command,
        "-a",
        args.codex_approval_policy,
        "exec",
        "--cd",
        str(attempt_dir / "workspace"),
        "--skip-git-repo-check",
        "--sandbox",
        args.codex_sandbox,
        "--ephemeral",
        "--json",
        "--output-last-message",
        str(attempt_dir / "final.md"),
    ]
    if args.model:
        command.extend(["--model", args.model])
    if args.codex_ignore_user_config:
        command.append("--ignore-user-config")
    command.append("-")
    return command


def claude_command(args: argparse.Namespace, _attempt_dir: Path) -> list[str]:
    command = [
        args.claude_command,
        "-p",
        "--output-format",
        args.claude_output_format,
        "--permission-mode",
        args.claude_permission_mode,
    ]
    if args.model:
        command.extend(["--model", args.model])
    command.extend(args.claude_arg)
    return command


def provider_command(args: argparse.Namespace, attempt_dir: Path) -> list[str]:
    if args.provider == "codex":
        return codex_command(args, attempt_dir)
    if args.provider == "claude":
        return claude_command(args, attempt_dir)
    raise RunnerError(f"unsupported provider: {args.provider}")


def run_process(
    command: list[str],
    prompt: str,
    cwd: Path,
    timeout_seconds: int,
) -> tuple[int, bool, str, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        return completed.returncode, False, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else ""
        return 124, True, stdout, stderr
    except FileNotFoundError as error:
        return 127, False, "", str(error)


def dry_run_output(task: dict[str, Any], attempt_id: str) -> tuple[int, bool, str, str, str]:
    final = (
        f"Dry run for {task['id']} {attempt_id}. "
        "No agent provider was executed, so this artifact only verifies runner structure."
    )
    stdout = json.dumps(
        {
            "type": "dry_run",
            "task_id": task["id"],
            "attempt": attempt_id,
            "message": final,
        }
    )
    return 0, False, stdout + "\n", "", final + "\n"


def final_message(attempt_dir: Path, stdout: str) -> str:
    final_path = attempt_dir / "final.md"
    text = final_path.read_text(encoding="utf-8") if final_path.is_file() else ""
    if text.strip():
        return text

    last_message = ""
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            value = event.get("message") or event.get("content") or event.get("text")
            if isinstance(value, str) and value.strip():
                last_message = value
    return last_message


def numeric_usage_from_jsonl(stdout: str) -> dict[str, float]:
    totals = {"tokens": 0.0, "cost_usd": 0.0}
    found = {"tokens": False, "cost_usd": False}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"total_tokens", "tokens"} and isinstance(item, (int, float)):
                    totals["tokens"] += float(item)
                    found["tokens"] = True
                elif key in {"cost_usd", "total_cost_usd"} and isinstance(item, (int, float)):
                    totals["cost_usd"] += float(item)
                    found["cost_usd"] = True
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for line in stdout.splitlines():
        try:
            visit(json.loads(line))
        except json.JSONDecodeError:
            continue

    metrics: dict[str, float] = {}
    for key, was_found in found.items():
        if was_found:
            metrics[key] = totals[key]
    return metrics


def write_transcript(
    path: Path,
    task: dict[str, Any],
    provider: str,
    model: str | None,
    command: list[str],
    exit_code: int,
    timed_out: bool,
    duration_seconds: float,
    final_text: str,
) -> None:
    safe_command = " ".join(command)
    transcript = f"""# Harness Eval Transcript

Task: {task["id"]}
Category: {task["category"]}
Provider: {provider}
Model: {model or "default"}
Command: {safe_command}
Exit code: {exit_code}
Timed out: {str(timed_out).lower()}
Duration seconds: {duration_seconds:.3f}

## Final Report

{final_text.strip()}
"""
    write_text(path, transcript + "\n")


def run_attempt(
    args: argparse.Namespace,
    task: dict[str, Any],
    tasks_dir: Path,
    run_dir: Path,
    source_root: Path,
    attempt_number: int,
) -> AttemptResult:
    attempt_id = f"run-{attempt_number:03d}"
    attempt_dir = run_dir / task["id"] / attempt_id
    if attempt_dir.exists():
        if not args.overwrite:
            raise RunnerError(f"attempt already exists; pass --overwrite to replace: {attempt_dir}")
        shutil.rmtree(attempt_dir)

    attempt_dir.mkdir(parents=True)
    workspace = attempt_dir / "workspace"
    fixture = prepare_workspace(task, tasks_dir, source_root, workspace)
    prompt = build_prompt(task, workspace, source_root, fixture, attempt_id)
    write_text(attempt_dir / "prompt.md", prompt)

    command = provider_command(args, attempt_dir)
    started_at = utc_now()
    start = time.monotonic()
    if args.dry_run:
        exit_code, timed_out, stdout, stderr, final_text = dry_run_output(task, attempt_id)
    else:
        exit_code, timed_out, stdout, stderr = run_process(
            command,
            prompt,
            workspace if args.provider == "claude" else ROOT,
            args.timeout_seconds,
        )
        final_text = final_message(attempt_dir, stdout)
    duration = time.monotonic() - start
    ended_at = utc_now()

    write_text(attempt_dir / "agent-stdout.log", stdout)
    write_text(attempt_dir / "agent-stderr.log", stderr)
    if final_text and not (attempt_dir / "final.md").is_file():
        write_text(attempt_dir / "final.md", final_text)

    contract = artifact_contract(task)
    transcript_path = attempt_dir / contract["transcript"]
    write_transcript(
        transcript_path,
        task,
        args.provider,
        args.model,
        command,
        exit_code,
        timed_out,
        duration,
        final_text,
    )

    if (
        (task.get("category") == "review_quality" or "review" in task.get("artifact_contract", {}))
        and final_text.strip()
    ):
        write_text(attempt_dir / contract["review"], final_text)

    metrics: dict[str, Any] = {"duration_seconds": round(duration, 3)}
    metrics.update(numeric_usage_from_jsonl(stdout))
    write_json(attempt_dir / contract["metrics"], metrics)

    write_json(
        attempt_dir / "attempt.json",
        {
            "version": 1,
            "task_id": task["id"],
            "category": task["category"],
            "attempt": attempt_id,
            "provider": args.provider,
            "model": args.model,
            "dry_run": args.dry_run,
            "workspace": str(workspace),
            "source_root": str(source_root),
            "fixture": str(fixture) if fixture else None,
            "task_digest": task_digest(task),
            "fixture_digest": file_tree_digest(fixture) if fixture else None,
            "command": command,
            "exit_code": exit_code,
            "timed_out": timed_out,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_seconds": round(duration, 3),
        },
    )
    return AttemptResult(task["id"], attempt_id, exit_code, timed_out)


def run_grader(args: argparse.Namespace, tasks_dir: Path, run_dir: Path) -> int:
    command = [
        sys.executable,
        str(GRADER),
        "--tasks-dir",
        str(tasks_dir),
        "--run-dir",
        str(run_dir),
        "--json",
    ]
    for task_id in args.task_id or []:
        command.extend(["--task-id", task_id])
    if args.skip_command_checks:
        command.append("--skip-commands")

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    write_text(run_dir / "grader-report.json", completed.stdout)
    write_text(run_dir / "grader-stderr.log", completed.stderr)
    return completed.returncode


def check_attempt_collisions(
    tasks: list[dict[str, Any]],
    attempts: int,
    run_dir: Path,
    overwrite: bool,
) -> None:
    if overwrite:
        return
    collisions = []
    for task in tasks:
        for attempt_number in range(1, attempts + 1):
            path = run_dir / task["id"] / f"run-{attempt_number:03d}"
            if path.exists():
                collisions.append(path)
    if collisions:
        first = collisions[0]
        suffix = "" if len(collisions) == 1 else f" and {len(collisions) - 1} more"
        raise RunnerError(f"attempt already exists; pass --overwrite to replace: {first}{suffix}")


def write_manifest(
    path: Path,
    args: argparse.Namespace,
    tasks: list[dict[str, Any]],
    source_root: Path,
    started_at: str,
    ended_at: str | None = None,
    attempt_results: list[AttemptResult] | None = None,
    grader_exit_code: int | None = None,
) -> None:
    attempt_results = attempt_results or []
    source_commit = git_output(["rev-parse", "HEAD"], source_root)
    source_status = git_output(["status", "--short"], source_root)
    write_json(
        path,
        {
            "version": 1,
            "provider": args.provider,
            "model": args.model,
            "dry_run": args.dry_run,
            "tasks_dir": str(args.tasks_dir),
            "task_ids": [task["id"] for task in tasks],
            "attempts_per_task": args.attempts,
            "source_root": str(source_root),
            "source_commit": source_commit,
            "source_dirty": bool(source_status),
            "started_at": started_at,
            "ended_at": ended_at,
            "attempt_results": [
                {
                    "task_id": result.task_id,
                    "attempt": result.attempt,
                    "exit_code": result.exit_code,
                    "timed_out": result.timed_out,
                }
                for result in attempt_results
            ],
            "grader_exit_code": grader_exit_code,
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["codex", "claude"], required=True)
    parser.add_argument("--tasks-dir", type=Path, default=DEFAULT_TASKS_DIR)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--suite-name")
    parser.add_argument("--task-id", action="append")
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--model")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--skip-grade", action="store_true")
    parser.add_argument("--skip-command-checks", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--codex-approval-policy", default="never")
    parser.add_argument("--codex-sandbox", default="workspace-write")
    parser.add_argument("--codex-ignore-user-config", action="store_true")
    parser.add_argument("--claude-command", default="claude")
    parser.add_argument("--claude-output-format", default="stream-json")
    parser.add_argument("--claude-permission-mode", default="bypassPermissions")
    parser.add_argument("--claude-arg", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.attempts < 1:
        raise RunnerError("--attempts must be at least 1")
    if args.timeout_seconds < 1:
        raise RunnerError("--timeout-seconds must be at least 1")

    tasks_dir = args.tasks_dir.resolve()
    source_root = args.source_root.resolve()
    if not source_root.is_dir():
        raise RunnerError(f"source root does not exist: {source_root}")

    tasks = load_tasks(tasks_dir, args.task_id)
    run_dir = (args.run_dir or default_run_dir(args.provider, tasks_dir, args.suite_name)).resolve()
    check_attempt_collisions(tasks, args.attempts, run_dir, args.overwrite)
    run_dir.mkdir(parents=True, exist_ok=True)

    started_at = utc_now()
    manifest_path = run_dir / "manifest.json"
    write_manifest(manifest_path, args, tasks, source_root, started_at)

    results: list[AttemptResult] = []
    for task in tasks:
        for attempt_number in range(1, args.attempts + 1):
            result = run_attempt(args, task, tasks_dir, run_dir, source_root, attempt_number)
            results.append(result)
            print(
                f"{task['id']}/{result.attempt}: exit={result.exit_code} timed_out={result.timed_out}",
                flush=True,
            )
            if args.fail_fast and result.failed:
                ended_at = utc_now()
                write_manifest(manifest_path, args, tasks, source_root, started_at, ended_at, results)
                return 1

    grader_exit_code = None
    if not args.skip_grade:
        grader_exit_code = run_grader(args, tasks_dir, run_dir)
        print(f"grader exit={grader_exit_code}; report={run_dir / 'grader-report.json'}", flush=True)

    ended_at = utc_now()
    write_manifest(manifest_path, args, tasks, source_root, started_at, ended_at, results, grader_exit_code)

    provider_failed = any(result.failed for result in results)
    if provider_failed:
        return 1
    if grader_exit_code is not None and grader_exit_code != 0:
        return grader_exit_code
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunnerError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
