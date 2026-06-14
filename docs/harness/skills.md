# Skill And Agent Policy

이 template의 기본 skill과 agent는 범용 engineering workflow만 포함합니다.

## Skill 포함 기준

포함할 수 있는 skill:

- 제품 도메인과 무관하다.
- application stack과 무관하다.
- 대부분의 새 프로젝트에서 반복적으로 필요하다.
- `AGENTS.md`에 넣기에는 긴 절차다.

현재 기본 skill:

- `brainstorming`
- `dispatching-parallel-agents`
- `executing-plans`
- `finishing-a-development-branch`
- `receiving-code-review`
- `requesting-code-review`
- `review`
- `starter`
- `subagent-driven-development`
- `systematic-debugging`
- `test-driven-development`
- `using-superpowers`
- `verification`
- `worktrees`
- `writing-plans`
- `writing-skills`

이 목록은 Superpowers의 development lifecycle을 회사 harness에 맞게 재작성한 baseline입니다. 외부 workflow text는 vendoring하지 않습니다.

## Agent 포함 기준

포함할 수 있는 agent:

- 대부분의 codebase에서 역할이 분명하다.
- product domain과 application stack에 묶이지 않는다.
- main agent의 context를 줄이거나 review 품질을 높인다.
- read/write 권한 boundary를 설명할 수 있다.

현재 기본 agent:

- `explorer`
- `implementer`
- `spec-reviewer`
- `code-reviewer`
- `verifier`

## 제외 기준

기본 template에 넣지 않는 skill 또는 agent:

- 특정 stack 전용 workflow
- 특정 product domain language에 의존하는 workflow
- 특정 deployment provider나 external service 전용 workflow
- 특정 팀의 local preference
- 특정 repo의 module ownership 또는 private architecture

이런 항목은 file bootstrap 후 각 프로젝트의 `harness/skills/` 또는 `harness/agents/`에 추가합니다. 추가 후 `./scripts/sync-agent-skills.sh`를 실행해 Codex와 Claude mirror를 갱신합니다.
