#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE="$ROOT/harness/skills"
AGENT_SOURCE="$ROOT/harness/agents"
CODEX_REPO_DEST="$ROOT/.agents/skills"
CODEX_DEST="$ROOT/plugins/company-agent-harness/skills"
CLAUDE_DEST="$ROOT/.claude/skills"

if [ ! -d "$SOURCE" ]; then
  echo "Missing skill source directory: $SOURCE" >&2
  exit 1
fi

if [ ! -d "$AGENT_SOURCE" ]; then
  echo "Missing agent source directory: $AGENT_SOURCE" >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required to mirror skills safely." >&2
  exit 1
fi

mkdir -p "$CODEX_REPO_DEST" "$CODEX_DEST" "$CLAUDE_DEST"

rsync -a --delete --exclude ".DS_Store" "$SOURCE/" "$CODEX_REPO_DEST/"
rsync -a --delete --exclude ".DS_Store" "$SOURCE/" "$CODEX_DEST/"
rsync -a --delete --exclude ".DS_Store" "$SOURCE/" "$CLAUDE_DEST/"

python3 "$ROOT/scripts/render-agent-mirrors.py"

echo "Synced skills:"
echo "  source: $SOURCE"
echo "  codex repo:   $CODEX_REPO_DEST"
echo "  codex plugin: $CODEX_DEST"
echo "  claude: $CLAUDE_DEST"
