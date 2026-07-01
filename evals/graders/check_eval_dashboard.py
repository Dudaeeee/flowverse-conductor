#!/usr/bin/env python3
"""Verify eval dashboard history and static site generation."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "scripts" / "update-eval-dashboard.py"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_summary(path: Path, *, run_dir: Path, started_at: str, gate_passed: bool) -> None:
    write_json(
        path,
        {
            "generated_at": started_at,
            "run_dir": str(run_dir),
            "run": {
                "provider": "codex",
                "model": None,
                "source_commit": "abc123",
                "source_dirty": False,
                "started_at": started_at,
                "task_ids": ["verification-quality-basic"],
                "attempts_per_task": 1,
            },
            "release_gate": {
                "passed": gate_passed,
                "failed_metric_ids": [] if gate_passed else ["pass_at_1"],
            },
            "metrics": {
                "pass_at_1": 1.0 if gate_passed else 0.0,
                "regression_pass_rate": 1.0 if gate_passed else 0.5,
            },
            "regressions": {
                "has_regressions": not gate_passed,
            },
        },
    )


def run_dashboard(summary: Path, history: Path, site_out: Path, *, max_runs: int = 104) -> None:
    command = [
        sys.executable,
        str(DASHBOARD),
        "--summary",
        str(summary),
        "--history",
        str(history),
        "--site-out",
        str(site_out),
        "--provider",
        "codex",
        "--suite-name",
        "public-weekly",
        "--artifact-name",
        "dashboard-smoke",
        "--max-runs",
        str(max_runs),
    ]
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_RUN_ID": "12345",
            "GITHUB_RUN_ATTEMPT": summary.stem.removeprefix("summary-") or "1",
            "GITHUB_REPOSITORY": "example/flowverse-conductor",
            "GITHUB_SERVER_URL": "https://github.com",
            "GITHUB_REF_NAME": "main",
            "GITHUB_SHA": "abc123",
        }
    )
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(f"dashboard update failed: {completed.stderr}\n{completed.stdout}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="harness-dashboard-") as tmp:
            tmp_path = Path(tmp)
            history = tmp_path / "history" / "dashboard-history.json"
            site_out = tmp_path / "site"
            first_summary = tmp_path / "summary-1.json"
            second_summary = tmp_path / "summary-2.json"

            write_summary(
                first_summary,
                run_dir=tmp_path / "runs" / "first",
                started_at="2026-06-01T00:00:00Z",
                gate_passed=True,
            )
            run_dashboard(first_summary, history, site_out)

            history_data = read_json(history)
            site_history = read_json(site_out / "history.json")
            require(history_data == site_history, "site history should match persisted history")
            require(history_data["version"] == 1, "history version should be 1")
            require(history_data["provider"] == "codex", "history provider should be decorated")
            require(history_data["suite_name"] == "public-weekly", "history suite should be decorated")
            require(len(history_data["runs"]) == 1, "first dashboard run should create one history entry")
            require((site_out / "index.html").is_file(), "dashboard index.html should be copied")
            print("ok: dashboard history and site generated")

            write_summary(
                second_summary,
                run_dir=tmp_path / "runs" / "second",
                started_at="2026-06-08T00:00:00Z",
                gate_passed=False,
            )
            run_dashboard(second_summary, history, site_out)

            updated = read_json(history)
            require(len(updated["runs"]) == 2, "second dashboard run should append history")
            require(updated["runs"][-1]["release_gate"]["passed"] is False, "latest run should be last")
            require(
                updated["runs"][-1]["dashboard"]["github_run_url"]
                == "https://github.com/example/flowverse-conductor/actions/runs/12345",
                "dashboard should include GitHub run URL",
            )
            print("ok: dashboard history appends decorated run metadata")

            pruned_site = tmp_path / "site-pruned"
            run_dashboard(second_summary, history, pruned_site, max_runs=1)
            pruned = read_json(history)
            require(len(pruned["runs"]) == 1, "max-runs should prune older history")
            require(read_json(pruned_site / "history.json") == pruned, "pruned site history should match")
            print("ok: dashboard history pruning works")

        print("eval dashboard checks passed")
        return 0
    except AssertionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
