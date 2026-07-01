#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ERRORS=0
WARNINGS=0

info() {
  printf 'info: %s\n' "$1"
}

pass() {
  printf 'ok: %s\n' "$1"
}

warn() {
  WARNINGS=$((WARNINGS + 1))
  printf 'warn: %s\n' "$1"
}

fail() {
  ERRORS=$((ERRORS + 1))
  printf 'error: %s\n' "$1"
}

require_file() {
  if [ -f "$ROOT/$1" ]; then
    pass "found $1"
  else
    fail "missing $1"
  fi
}

require_dir() {
  if [ -d "$ROOT/$1" ]; then
    pass "found $1"
  else
    fail "missing $1"
  fi
}

info "checking harness in $ROOT"

require_file "AGENTS.md"
require_file "CLAUDE.md"
require_file "CONTEXT.md"
require_file "README.md"
require_file ".github/workflows/harness.yml"
require_file ".github/workflows/harness-weekly.yml"
require_file "docs/harness/project-profile.md"
require_file "scripts/sync-agent-skills.sh"
require_file "scripts/render-agent-mirrors.py"
require_file "scripts/run-harness-eval.py"
require_file "scripts/report-harness-eval.py"
require_file "scripts/update-eval-dashboard.py"
require_file "docs/harness/eval-dashboard/index.html"
require_file "docs/harness/eval-dashboard/history.json"
require_dir "docs/adr"
require_dir "harness/skills"
require_dir "harness/agents"
require_dir ".agents/skills"
require_dir ".claude/skills"
require_dir ".claude/agents"
require_dir ".codex/agents"
require_dir "plugins/company-agent-harness/skills"

for script in "$ROOT/scripts/sync-agent-skills.sh" "$ROOT/scripts/check-harness.sh"; do
  if bash -n "$script"; then
    pass "shell syntax ok: ${script#$ROOT/}"
  else
    fail "shell syntax failed: ${script#$ROOT/}"
  fi
done

if [ -f "$ROOT/CLAUDE.md" ] && grep -qx '@AGENTS.md' "$ROOT/CLAUDE.md"; then
  pass "CLAUDE.md imports AGENTS.md"
else
  fail "CLAUDE.md should contain @AGENTS.md on its own line"
fi

if [ -x "$ROOT/scripts/sync-agent-skills.sh" ]; then
  pass "sync-agent-skills.sh is executable"
else
  fail "scripts/sync-agent-skills.sh is not executable"
fi

if [ -x "$ROOT/scripts/render-agent-mirrors.py" ]; then
  pass "render-agent-mirrors.py is executable"
else
  fail "scripts/render-agent-mirrors.py is not executable"
fi

if [ -x "$ROOT/scripts/run-harness-eval.py" ]; then
  pass "run-harness-eval.py is executable"
else
  fail "scripts/run-harness-eval.py is not executable"
fi

if [ -x "$ROOT/scripts/report-harness-eval.py" ]; then
  pass "report-harness-eval.py is executable"
else
  fail "scripts/report-harness-eval.py is not executable"
fi

if [ -x "$ROOT/scripts/update-eval-dashboard.py" ]; then
  pass "update-eval-dashboard.py is executable"
else
  fail "scripts/update-eval-dashboard.py is not executable"
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 -m py_compile "$ROOT/scripts/render-agent-mirrors.py" >/dev/null 2>&1; then
    pass "render-agent-mirrors.py compiles"
  else
    fail "render-agent-mirrors.py failed py_compile"
  fi

  if python3 -m py_compile "$ROOT/scripts/run-harness-eval.py" >/dev/null 2>&1; then
    pass "run-harness-eval.py compiles"
  else
    fail "run-harness-eval.py failed py_compile"
  fi

  if python3 -m py_compile "$ROOT/scripts/report-harness-eval.py" >/dev/null 2>&1; then
    pass "report-harness-eval.py compiles"
  else
    fail "report-harness-eval.py failed py_compile"
  fi

  if python3 -m py_compile "$ROOT/scripts/update-eval-dashboard.py" >/dev/null 2>&1; then
    pass "update-eval-dashboard.py compiles"
  else
    fail "update-eval-dashboard.py failed py_compile"
  fi

  if python3 -m py_compile "$ROOT/evals/graders/check_eval_dashboard.py" >/dev/null 2>&1; then
    pass "check_eval_dashboard.py compiles"
  else
    fail "check_eval_dashboard.py failed py_compile"
  fi

  if python3 -m json.tool "$ROOT/docs/harness/eval-dashboard/history.json" >/dev/null 2>&1; then
    pass "eval dashboard seed history JSON parses"
  else
    fail "invalid JSON: docs/harness/eval-dashboard/history.json"
  fi

  if python3 -m json.tool "$ROOT/.agents/plugins/marketplace.json" >/dev/null 2>&1; then
    pass "Codex marketplace JSON parses"
  else
    fail "invalid JSON: .agents/plugins/marketplace.json"
  fi

  if python3 -m json.tool "$ROOT/plugins/company-agent-harness/.codex-plugin/plugin.json" >/dev/null 2>&1; then
    pass "Codex plugin JSON parses"
  else
    fail "invalid JSON: plugins/company-agent-harness/.codex-plugin/plugin.json"
  fi

  if python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
skill_roots = [
    root / "harness" / "skills",
    root / ".agents" / "skills",
    root / ".claude" / "skills",
    root / "plugins" / "company-agent-harness" / "skills",
]
errors = []

for skill_root in skill_roots:
    if not skill_root.is_dir():
        errors.append(f"missing skill directory: {skill_root}")
        continue

    seen = {}
    for path in sorted(skill_root.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            errors.append(f"{path} must start with YAML frontmatter")
            continue
        end = text.find("\n---\n", 4)
        if end == -1:
            errors.append(f"{path} is missing closing frontmatter marker")
            continue

        fields = {}
        for line in text[4:end].splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" not in line:
                errors.append(f"{path} frontmatter line is not key: value: {line}")
                continue
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"').strip("'")

        for required in ("name", "description"):
            if not fields.get(required):
                errors.append(f"{path} missing required frontmatter field: {required}")

        name = fields.get("name")
        if name:
            if name != path.parent.name:
                errors.append(f"{path} name {name!r} does not match directory {path.parent.name!r}")
            if name in seen:
                errors.append(f"duplicate skill name {name!r}: {seen[name]} and {path}")
            seen[name] = path

    if not seen:
        errors.append(f"no skills found in {skill_root}")
    if "starter" not in seen:
        errors.append(f"starter skill missing from {skill_root}")

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    raise SystemExit(1)
PY
  then
    pass "skill frontmatter validates"
  else
    fail "invalid skill frontmatter"
  fi

  if python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
agent_dir = root / ".codex" / "agents"
required = {"name", "description", "developer_instructions"}

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

for path in sorted(agent_dir.glob("*.toml")):
    text = path.read_text(encoding="utf-8")
    if tomllib is not None:
        data = tomllib.loads(text)
    else:
        data = {}
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                raise SystemExit(f"{path} contains unsupported TOML line: {line}")
            key, raw_value = stripped.split("=", 1)
            key = key.strip()
            raw_value = raw_value.strip()
            if not (raw_value.startswith('"') and raw_value.endswith('"')):
                raise SystemExit(f"{path} value for {key} is not a basic string")
            data[key] = raw_value[1:-1]
    missing = required - data.keys()
    if missing:
        raise SystemExit(f"{path} missing {sorted(missing)}")
PY
  then
    pass "Codex agent TOML parses"
  else
    fail "invalid Codex agent TOML"
  fi
else
  warn "python3 not found; skipped JSON/TOML/Python validation"
fi

if command -v diff >/dev/null 2>&1; then
  if diff -qr "$ROOT/harness/skills" "$ROOT/.agents/skills" >/dev/null 2>&1; then
    pass "Codex repo skill mirror matches harness/skills"
  else
    fail "Codex repo skill mirror differs; run ./scripts/sync-agent-skills.sh"
  fi

  if diff -qr "$ROOT/harness/skills" "$ROOT/.claude/skills" >/dev/null 2>&1; then
    pass "Claude skill mirror matches harness/skills"
  else
    fail "Claude skill mirror differs; run ./scripts/sync-agent-skills.sh"
  fi

  if diff -qr "$ROOT/harness/skills" "$ROOT/plugins/company-agent-harness/skills" >/dev/null 2>&1; then
    pass "Codex skill mirror matches harness/skills"
  else
    fail "Codex skill mirror differs; run ./scripts/sync-agent-skills.sh"
  fi

else
  warn "diff not found; skipped mirror validation"
fi

if command -v python3 >/dev/null 2>&1; then
  if python3 "$ROOT/scripts/render-agent-mirrors.py" --check >/dev/null 2>&1; then
    pass "agent mirrors are current"
  else
    fail "agent mirrors differ; run ./scripts/sync-agent-skills.sh"
  fi
fi

PROFILE="$ROOT/docs/harness/project-profile.md"
if [ -f "$PROFILE" ]; then
  if grep -Eq '^- [^:]+:[[:space:]]*$' "$PROFILE"; then
    warn "project profile still has blank fields"
  else
    pass "project profile fields appear filled"
  fi
fi

if command -v rg >/dev/null 2>&1; then
  if rg -q --hidden 'Flowverse|flowverse-conductor|Your Company' \
    --glob '!**/.git/**' \
    --glob '!MIGRATE_EXISTING_CODEBASE.md' \
    --glob '!**/MIGRATE_EXISTING_CODEBASE.md' \
    --glob '!**/docs/harness/rename-checklist.md' \
    --glob '!**/scripts/check-harness.sh' \
    "$ROOT"; then
    warn "starter names or placeholder publisher metadata remain; see docs/harness/rename-checklist.md"
  else
    pass "no starter name placeholders found"
  fi
else
  warn "rg not found; skipped starter name placeholder check"
fi

if [ "$ERRORS" -gt 0 ]; then
  printf 'failed: %d error(s), %d warning(s)\n' "$ERRORS" "$WARNINGS"
  exit 1
fi

printf 'passed: %d error(s), %d warning(s)\n' "$ERRORS" "$WARNINGS"
