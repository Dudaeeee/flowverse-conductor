# Adapter Strategy

이 starter는 한 가지 원천을 두고 tool별 adapter를 둡니다.

## Instruction Adapter

- Canonical instruction: `AGENTS.md`
- Claude adapter: `CLAUDE.md`
- Claude Code는 `@AGENTS.md` import syntax로 같은 지침을 읽습니다.
- Codex는 repository scope의 `AGENTS.md`를 직접 읽습니다.
- First-class adapter는 Codex와 Claude Code뿐입니다.

## Skill Adapter

- Canonical skill source: `harness/skills/`
- Codex repo mirror: `.agents/skills/`
- Codex plugin mirror: `plugins/company-agent-harness/skills/`
- Claude mirror: `.claude/skills/`
- Sync command: `./scripts/sync-agent-skills.sh`

Codex는 `.agents/skills/`를 repository-scoped skill 위치로 읽습니다. 그래서 file bootstrap 직후 plugin 설치 없이도 기본 workflow skill을 사용할 수 있습니다.

Codex plugin은 installable distribution unit입니다. 이 repo는 `plugins/company-agent-harness/.codex-plugin/plugin.json`과 `.agents/plugins/marketplace.json`을 포함해 local repo marketplace로 노출할 수 있게 합니다. 여러 repo나 팀에 같은 harness를 배포할 때 plugin adapter를 사용합니다.

Claude Code는 repository 안의 `.claude/skills/*/SKILL.md`를 project-local skill로 읽습니다. 같은 skill 본문을 유지하기 위해 mirror를 script로 생성합니다.

Codex plugin package name `company-agent-harness`는 file bootstrap 후에도 기본적으로 유지합니다. 이 이름은 프로젝트 제품명이 아니라 사내 harness adapter를 뜻합니다. 프로젝트별로 이름을 바꾸면 Codex skill namespace와 설치명이 달라지므로, 명확한 이유가 있을 때만 변경합니다.

## Agent Adapter

- Canonical agent source: `harness/agents/`
- Codex custom agent mirror: `.codex/agents/*.toml`
- Claude Code subagent mirror: `.claude/agents/*.md`
- Render command: `./scripts/render-agent-mirrors.py`
- Sync command: `./scripts/sync-agent-skills.sh`

`harness/agents/*.md`는 회사가 읽고 수정하기 쉬운 Markdown source입니다. Claude Code subagent 형식과 가깝지만 Codex 전용 metadata도 포함할 수 있습니다. Sync script는 Claude mirror에서는 Codex 전용 field를 제거하고, Codex mirror에서는 TOML custom agent로 변환합니다.

기본 agent:

- `explorer`: read-only repository exploration
- `implementer`: scoped implementation
- `spec-reviewer`: plan/spec compliance review
- `code-reviewer`: correctness and risk review
- `verifier`: validation runner and evidence reporter

Agent는 workflow를 대체하지 않습니다. Skill은 "어떤 절차를 따를지"를 정의하고, agent는 "어떤 specialist에게 위임할지"를 정의합니다.

## Committed Mirrors

Codex mirror와 Claude mirror는 repo에 실제 파일로 commit합니다. 이 template은 file bootstrap 직후 작동해야 하므로 adapter를 별도 setup step으로 미루지 않습니다.

Mirror는 build artifact처럼 취급합니다. 프로젝트는 file bootstrap 후 모든 파일을 수정할 수 있지만, 일관성을 유지하려면 `harness/skills/`나 `harness/agents/`를 먼저 수정하고 `./scripts/sync-agent-skills.sh`로 mirror를 재생성하는 방식을 권장합니다.

## Other Tools

Cursor, Devin, Gemini CLI 같은 다른 agent tool은 이 template의 first-class adapter 범위에 포함하지 않습니다. 필요한 경우 `AGENTS.md`와 `docs/harness/`를 읽는 best-effort 방식으로 사용하고, 전용 adapter 파일은 실제 도입 요구가 생길 때 추가합니다.

## Skill 추가 절차

1. `harness/skills/<skill-name>/SKILL.md`를 만든다.
2. frontmatter에 `name`과 `description`을 넣는다.
3. 본문은 agent가 실제로 따라야 할 workflow만 적는다.
4. `./scripts/sync-agent-skills.sh`를 실행한다.
5. Codex plugin과 Claude Code에서 skill 이름이 충돌하지 않는지 확인한다.

## Agent 추가 절차

1. `harness/agents/<agent-name>.md`를 만든다.
2. frontmatter에 `name`, `description`, Claude용 `tools`/`model`, 필요한 Codex용 `codex_*` field를 넣는다.
3. 본문은 specialist role, workflow, boundary, output을 짧게 적는다.
4. `./scripts/sync-agent-skills.sh`를 실행한다.
5. `./scripts/check-harness.sh`로 `.codex/agents/*.toml` parse와 mirror drift를 확인한다.

## Upstream 참고 기준

- upstream skill pack은 workflow category와 좋은 습관을 참고한다.
- upstream repository의 contributor 지침을 회사 starter 지침으로 그대로 쓰지 않는다.
- 외부 내용을 가져올 때는 license, source URL, 수정 여부를 `source-map.md`에 기록한다.
