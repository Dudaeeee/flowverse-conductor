# Source Map

이 starter는 외부 프로젝트를 그대로 복제한 것이 아니라, 공식 문서와 공개 workflow pack에서 확인한 pattern을 회사용 구조로 재작성한 것입니다.

Last reviewed: 2026-06-14

## Official References

- OpenAI Codex `AGENTS.md`: https://developers.openai.com/codex/guides/agents-md
- OpenAI Codex Skills: https://developers.openai.com/codex/skills
- OpenAI Codex Subagents and custom agents: https://developers.openai.com/codex/subagents
- OpenAI Codex Plugin build guide: https://developers.openai.com/codex/plugins/build
- Claude Code memory and `CLAUDE.md`: https://code.claude.com/docs/en/memory
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code parallel agents overview: https://code.claude.com/docs/en/agents
- Agent Skills standard overview: https://agentskills.io/home

## Upstream Inspiration

- Superpowers repository: https://github.com/obra/superpowers
- Superpowers license: MIT License, Copyright (c) 2025 Jesse Vincent

Adapted workflow categories:

- brainstorming
- writing plans
- test-driven development
- systematic debugging
- review
- verification
- worktrees
- using superpowers
- executing plans
- subagent-driven development
- dispatching parallel agents
- requesting code review
- receiving code review
- finishing a development branch
- writing skills

Adapted agent role categories:

- explorer
- implementer
- spec reviewer
- code reviewer
- verifier

## Adaptation Policy

- Upstream text is not vendored into this starter.
- Workflow names and categories may be retained when they describe common engineering practice.
- Instructions are rewritten for this company's Codex plus Claude Code harness.
- Superpowers concepts are absorbed as methodology, not as a vendored dependency.
- Local modifications include shorter company harness wording, stack-neutral workflow boundaries, Codex repo skill mirror support, Codex custom agent TOML generation, and Claude project subagent mirror generation.
- If future changes copy source text or scripts, add license attribution and a note describing local modifications.
