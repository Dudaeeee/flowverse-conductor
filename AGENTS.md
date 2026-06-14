# Agent Operating Guide

이 파일은 이 저장소의 canonical agent 지침입니다. 항상 context에 올라가므로 최소한의 harness 규칙과 project profile pointer만 둡니다. Codex는 이 파일을 직접 읽고, Claude Code는 `CLAUDE.md`를 통해 이 파일을 import합니다.

## Repository Profile

- 프로젝트 이름: Flowverse Conductor Agent Harness
- 목적: 새 프로젝트 file bootstrap용 agent-harness-only template source 제공
- 주요 사용 도구: Codex, Claude Code
- 프로젝트 profile: `docs/harness/project-profile.md` (agent 운영 계약)
- skill 원본: `harness/skills/`
- agent 원본: `harness/agents/`
- Codex repo skill mirror: `.agents/skills/`
- Codex adapter: `plugins/company-agent-harness/`
- Claude adapter: `.claude/skills/`

새 프로젝트를 이 repo의 파일로 bootstrap한 뒤에는 위 항목과 `docs/harness/project-profile.md`를 실제 제품, stack, test command에 맞게 갱신한다.

## Working Rules

- 사용자에게 설명할 때는 한국어를 기본으로 쓴다.
- 작업 전 agent 운영 계약인 `docs/harness/project-profile.md`와 repository files를 함께 보고 실제 stack, command, convention을 확인한다.
- project profile과 실제 repository files가 충돌하면 추정하지 말고 충돌을 사용자에게 알린다.
- 사용자의 최신 요청이 문서나 이전 handoff보다 우선한다.
- 사용자나 다른 agent가 만든 변경을 되돌리거나 삭제하지 않는다.
- 검색은 `rg` 또는 `rg --files`를 우선 사용한다.
- destructive git command는 사용자가 명시적으로 요청하지 않는 한 실행하지 않는다.
- secret, token, private key, credential을 파일에 쓰지 않는다.
- 변경 후 가능한 가장 가까운 검증을 실행하고, 실행하지 못한 검증은 이유를 밝힌다.

## Harness Maintenance

- skill은 `harness/skills/<skill-name>/SKILL.md`에서 수정한다.
- agent는 `harness/agents/<agent-name>.md`에서 수정한다.
- 수정 후 `./scripts/sync-agent-skills.sh`를 실행해 Codex와 Claude mirror를 갱신한다.
- Codex plugin metadata는 `plugins/company-agent-harness/.codex-plugin/plugin.json`에서 관리한다.
- Codex repo skill은 `.agents/skills/`, Codex custom agent는 `.codex/agents/` mirror를 통해 제공한다.
- Claude Code project-local skill은 `.claude/skills/` mirror를 통해 제공한다.
- Claude Code project-local subagent는 `.claude/agents/` mirror를 통해 제공한다.
- 세부 workflow는 `harness/skills/`와 `docs/harness/`에 둔다. `AGENTS.md`에는 항상 필요한 최소 규칙만 둔다.
