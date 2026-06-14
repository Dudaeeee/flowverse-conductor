# Bootstrap

새 프로젝트는 이 GitHub-hosted template source의 파일을 받아 시작합니다.

## Agent-assisted path

1. GitHub에서 `Download ZIP`을 받거나 release archive를 내려받는다.
2. 새 project repository directory에 archive 내용을 풀어 넣는다.
3. Codex나 Claude Code에서 `starter` 스킬을 요청해 README 기반 첫 세팅을 agent와 함께 진행한다.
4. agent가 `./scripts/check-harness.sh`를 실행하고, `docs/harness/rename-checklist.md`, `docs/harness/project-profile.md`, `CONTEXT.md`, `AGENTS.md`를 프로젝트에 맞게 갱신하게 한다.
5. 필요하면 `harness/skills/`와 `harness/agents/`에서 프로젝트별 workflow를 추가하고 `./scripts/sync-agent-skills.sh`를 실행한다.
6. agent가 `./scripts/check-harness.sh`를 다시 실행해 남은 warning을 보고한다.
7. 필요하면 새 repository에서 `git init`을 실행하고 첫 커밋을 만든다.

`starter` 스킬은 이 절차를 agent가 실행하기 위한 첫 실행 workflow다. README와 repository files를 읽고 현재 상태를 점검한 뒤, 프로젝트 의도와 운영 계약을 확정하기 위한 질문을 하나씩 던진다. 사용자의 답변으로 결정된 내용은 안전한 초기 파일 수정으로 반영하고, 프로젝트 이름, 제품 설명, stack, 명령어처럼 repository에서 확인할 수 없는 정보는 추천안과 함께 사용자에게 확인한다.

## Manual path

1. `./scripts/check-harness.sh`를 실행한다.
2. `docs/harness/rename-checklist.md`를 따라 starter 이름과 placeholder를 바꾼다.
3. `docs/harness/project-profile.md`와 `CONTEXT.md`를 프로젝트에 맞게 갱신한다.
4. `AGENTS.md`의 repository-specific section을 실제 stack과 명령어에 맞게 조정한다.
5. 필요하면 `harness/skills/`와 `harness/agents/`에서 프로젝트별 workflow를 추가하고 `./scripts/sync-agent-skills.sh`를 실행한다.
6. `./scripts/check-harness.sh`를 다시 실행한다.
7. 필요하면 새 repository에서 `git init`을 실행하고 첫 커밋을 만든다.

## Codex에서 바로 읽히는 것

- `AGENTS.md`: repository instruction
- `.agents/skills/`: repo-scoped skills
- `.codex/agents/`: project custom agents
- `.agents/plugins/marketplace.json`: optional local plugin marketplace

Codex plugin 설치는 필수가 아닙니다. plugin은 같은 skill bundle을 다른 repo나 workspace에 배포하고 싶을 때 사용합니다.

## Claude Code에서 바로 읽히는 것

- `CLAUDE.md`: `AGENTS.md` import adapter
- `.claude/skills/`: project-local skills
- `.claude/agents/`: project-local subagents

## 피할 것

- 이 template repository를 upstream remote로 유지하지 않는다.
- Template 업데이트를 자동으로 pull하지 않는다.
- GitHub Template Repository 기능을 전제로 하지 않는다.
- `git clone`을 기본 bootstrap 방식으로 쓰지 않는다.

`git clone`을 임시로 사용했다면 새 프로젝트로 옮기기 전에 template repo의 `.git` history와 upstream remote를 제거해야 합니다.
