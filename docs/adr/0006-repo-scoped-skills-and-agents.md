# Repo-Scoped Skills And Agents

Codex repo-scoped skills live in `.agents/skills/`, Codex custom agents live in `.codex/agents/`, and Claude Code project skills/subagents live in `.claude/skills/` and `.claude/agents/`.

Canonical sources remain under `harness/skills/` and `harness/agents/`. Mirrors are committed so a project created from a GitHub archive works immediately without requiring plugin installation or a generation step before the first agent session.

Skill mirrors are byte-for-byte copies. Agent mirrors are rendered because Codex and Claude Code use different custom agent formats: Codex uses TOML files with `developer_instructions`, while Claude Code uses Markdown files with YAML frontmatter and a prompt body.

This adds a small maintenance script, `scripts/render-agent-mirrors.py`, instead of asking humans to hand-maintain two divergent agent formats. The script is intentionally narrow: it only renders project agent files and checks drift.
