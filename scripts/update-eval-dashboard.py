#!/usr/bin/env python3
"""Update the static harness eval dashboard history."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "docs" / "harness" / "eval-dashboard"


class DashboardError(RuntimeError):
    """Dashboard history could not be updated."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, *, required: bool) -> Any:
    if not path.exists():
        if required:
            raise DashboardError(f"missing JSON file: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DashboardError(f"{path}: invalid JSON: {error}") from error


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_history(path: Path) -> list[dict[str, Any]]:
    raw = read_json(path, required=False)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        runs = raw.get("runs", [])
        if isinstance(runs, list):
            return [item for item in runs if isinstance(item, dict)]
    raise DashboardError(f"{path}: expected a JSON object with runs[] or an array")


def github_run_metadata(args: argparse.Namespace) -> dict[str, Any]:
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    run_attempt = os.environ.get("GITHUB_RUN_ATTEMPT")
    ref_name = os.environ.get("GITHUB_REF_NAME")
    sha = os.environ.get("GITHUB_SHA")

    run_url = None
    if repository and run_id:
        run_url = f"{server_url}/{repository}/actions/runs/{run_id}"

    return {
        "github_run_id": run_id,
        "github_run_attempt": run_attempt,
        "github_run_url": args.github_run_url or run_url,
        "github_ref_name": ref_name,
        "github_sha": sha,
        "artifact_name": args.artifact_name,
        "provider": args.provider,
        "suite_name": args.suite_name,
    }


def run_key(summary: dict[str, Any]) -> str:
    dashboard = summary.get("dashboard", {})
    if isinstance(dashboard, dict) and dashboard.get("github_run_id"):
        attempt = dashboard.get("github_run_attempt") or "1"
        provider = dashboard.get("provider") or summary.get("run", {}).get("provider") or "unknown"
        suite = dashboard.get("suite_name") or "unknown"
        return f"github:{provider}:{suite}:{dashboard['github_run_id']}:{attempt}"

    run = summary.get("run", {})
    provider = run.get("provider") if isinstance(run, dict) else "unknown"
    source_commit = run.get("source_commit") if isinstance(run, dict) else "unknown"
    return ":".join(
        [
            "summary",
            str(provider or "unknown"),
            str(summary.get("run_dir") or "unknown"),
            str(source_commit or "unknown"),
            str(summary.get("generated_at") or "unknown"),
        ]
    )


def decorate_summary(summary: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    decorated = dict(summary)
    dashboard = dict(decorated.get("dashboard", {})) if isinstance(decorated.get("dashboard"), dict) else {}
    dashboard.update({key: value for key, value in github_run_metadata(args).items() if value not in (None, "")})
    dashboard["published_at"] = utc_now()
    decorated["dashboard"] = dashboard
    return decorated


def merge_runs(
    existing: list[dict[str, Any]],
    current: dict[str, Any],
    *,
    max_runs: int,
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in existing:
        merged[run_key(item)] = item
    merged[run_key(current)] = current
    runs = sorted(
        merged.values(),
        key=lambda item: (
            item.get("run", {}).get("started_at")
            if isinstance(item.get("run"), dict)
            else None
        )
        or item.get("generated_at")
        or "",
    )
    return runs[-max_runs:]


def build_history(runs: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    latest = runs[-1] if runs else {}
    latest_dashboard = latest.get("dashboard", {}) if isinstance(latest.get("dashboard"), dict) else {}
    return {
        "version": 1,
        "kind": "harness_eval_dashboard_history",
        "generated_at": utc_now(),
        "provider": latest_dashboard.get("provider"),
        "suite_name": latest_dashboard.get("suite_name"),
        "max_runs": args.max_runs,
        "runs": runs,
    }


def copy_site(source: Path, output: Path) -> None:
    if not source.is_dir():
        raise DashboardError(f"dashboard source directory does not exist: {source}")
    if output.exists():
        shutil.rmtree(output)
    ignore = shutil.ignore_patterns("history.json")
    shutil.copytree(source, output, ignore=ignore)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--site-source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--site-out", type=Path, required=True)
    parser.add_argument("--max-runs", type=int, default=104)
    parser.add_argument("--provider")
    parser.add_argument("--suite-name")
    parser.add_argument("--artifact-name")
    parser.add_argument("--github-run-url")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_runs < 1:
        raise DashboardError("--max-runs must be at least 1")

    summary = read_json(args.summary, required=True)
    if not isinstance(summary, dict):
        raise DashboardError(f"{args.summary}: expected JSON object")

    current = decorate_summary(summary, args)
    runs = merge_runs(load_history(args.history), current, max_runs=args.max_runs)
    history = build_history(runs, args)

    write_json(args.history, history)
    copy_site(args.site_source, args.site_out)
    write_json(args.site_out / "history.json", history)

    print(f"dashboard history: {args.history}")
    print(f"dashboard site: {args.site_out}")
    print(f"dashboard runs: {len(runs)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DashboardError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
