#!/usr/bin/env python3
"""Render harness agent definitions into Codex and Claude mirror formats."""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "harness" / "agents"
CODEX_DEST = ROOT / ".codex" / "agents"
CLAUDE_DEST = ROOT / ".claude" / "agents"


class AgentError(RuntimeError):
    pass


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AgentError(f"{path} must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AgentError(f"{path} is missing closing frontmatter marker")

    raw_frontmatter = text[4:end]
    body = text[end + len("\n---\n") :]
    fields: dict[str, str] = {}
    for line in raw_frontmatter.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            raise AgentError(f"{path} frontmatter line is not key: value: {line}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")

    for required in ("name", "description"):
        if not fields.get(required):
            raise AgentError(f"{path} missing required frontmatter field: {required}")

    return fields, body


def toml_value(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_codex_agent(path: Path) -> str:
    fields, body = parse_frontmatter(path)
    output = [
        "# Generated from harness/agents. Do not edit directly.",
        f"name = {toml_value(fields['name'])}",
        f"description = {toml_value(fields['description'])}",
    ]

    if fields.get("codex_model"):
        output.append(f"model = {toml_value(fields['codex_model'])}")
    if fields.get("codex_model_reasoning_effort"):
        output.append(
            f"model_reasoning_effort = {toml_value(fields['codex_model_reasoning_effort'])}"
        )
    if fields.get("codex_sandbox_mode"):
        output.append(f"sandbox_mode = {toml_value(fields['codex_sandbox_mode'])}")

    output.append(f"developer_instructions = {toml_value(body.strip() + chr(10))}")
    output.append("")
    return "\n".join(output)


def render_claude_agent(path: Path) -> str:
    fields, body = parse_frontmatter(path)
    ordered_keys = ("name", "description", "tools", "model", "permissionMode", "skills", "color")
    frontmatter = ["---"]
    for key in ordered_keys:
        if fields.get(key):
            frontmatter.append(f"{key}: {fields[key]}")
    for key in sorted(fields):
        if key in ordered_keys or key.startswith("codex_"):
            continue
        frontmatter.append(f"{key}: {fields[key]}")
    frontmatter.append("---")
    frontmatter.append("")
    frontmatter.append(body.lstrip())
    return "\n".join(frontmatter)


def copy_tree(source: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for item in sorted(source.iterdir()):
        if item.name == ".DS_Store":
            continue
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=shutil.ignore_patterns(".DS_Store"))
        else:
            shutil.copy2(item, target)


def render(source: Path, codex_dest: Path, claude_dest: Path) -> None:
    if not source.is_dir():
        raise AgentError(f"Missing agent source directory: {source}")

    if claude_dest.exists():
        shutil.rmtree(claude_dest)
    claude_dest.mkdir(parents=True, exist_ok=True)

    if codex_dest.exists():
        shutil.rmtree(codex_dest)
    codex_dest.mkdir(parents=True, exist_ok=True)

    for source_file in sorted(source.glob("*.md")):
        fields, _ = parse_frontmatter(source_file)
        claude_file = claude_dest / source_file.name
        claude_file.write_text(render_claude_agent(source_file), encoding="utf-8")
        codex_file = codex_dest / f"{fields['name']}.toml"
        codex_file.write_text(render_codex_agent(source_file), encoding="utf-8")


def compare_dirs(expected: Path, actual: Path) -> list[str]:
    expected_files = sorted(p.relative_to(expected) for p in expected.rglob("*") if p.is_file())
    actual_files = sorted(p.relative_to(actual) for p in actual.rglob("*") if p.is_file())
    messages: list[str] = []
    if expected_files != actual_files:
        messages.append(f"file list differs: expected {expected_files}, actual {actual_files}")
        return messages

    for rel in expected_files:
        expected_text = (expected / rel).read_text(encoding="utf-8")
        actual_text = (actual / rel).read_text(encoding="utf-8")
        if expected_text != actual_text:
            diff = "\n".join(
                difflib.unified_diff(
                    expected_text.splitlines(),
                    actual_text.splitlines(),
                    fromfile=f"expected/{rel}",
                    tofile=f"actual/{rel}",
                    lineterm="",
                )
            )
            messages.append(diff)
    return messages


def check() -> int:
    with tempfile.TemporaryDirectory(prefix="agent-mirrors-") as tmp:
        tmp_path = Path(tmp)
        expected_codex = tmp_path / "codex"
        expected_claude = tmp_path / "claude"
        render(SOURCE, expected_codex, expected_claude)

        failures = []
        failures.extend(f"Codex agent mirror drift: {msg}" for msg in compare_dirs(expected_codex, CODEX_DEST))
        failures.extend(f"Claude agent mirror drift: {msg}" for msg in compare_dirs(expected_claude, CLAUDE_DEST))

        if failures:
            for failure in failures:
                print(failure, file=sys.stderr)
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify committed mirrors are current")
    args = parser.parse_args()

    try:
        if args.check:
            return check()
        render(SOURCE, CODEX_DEST, CLAUDE_DEST)
        print("Synced agents:")
        print(f"  source: {SOURCE}")
        print(f"  codex:  {CODEX_DEST}")
        print(f"  claude: {CLAUDE_DEST}")
        return 0
    except AgentError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
