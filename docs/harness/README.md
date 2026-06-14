# Harness Overview

이 directory는 agent harness의 운영 문서입니다. 새 프로젝트가 이 repo의 파일로 bootstrap되면 이 문서들을 프로젝트 상황에 맞게 갱신합니다.

## 목표

- Codex와 Claude Code가 같은 repository 규칙을 읽는다.
- 반복 작업은 skill로 분리해 필요할 때만 context에 올린다.
- 반복되는 specialist 역할은 agent로 분리해 필요할 때만 위임한다.
- 회사 공통 workflow와 프로젝트별 운영 계약을 분리한다.
- upstream workflow pack은 참고하되, starter repo 자체와 tool adapter는 회사가 소유한다.
- application framework나 product code는 포함하지 않는다.
- template source repository는 GitHub에 올라가는 것을 전제로 한다.

## 주요 파일

- `project-profile.md`: agent가 우선 참조하는 프로젝트별 운영 계약이다.
- `bootstrap.md`: GitHub archive를 받아 새 프로젝트를 시작하는 절차를 설명한다.
- `adapters.md`: Codex와 Claude Code가 같은 지침과 skill을 읽는 방법을 설명한다.
- `skills.md`: 기본 skill/agent 포함 기준과 제외 기준을 설명한다.
- `context-and-decisions.md`: `CONTEXT.md`와 `docs/adr/` 사용 기준을 설명한다.
- `rename-checklist.md`: file bootstrap 후 starter 이름과 placeholder를 바꾸는 위치를 설명한다.
- `ci.md`: harness-only CI의 범위와 제외 대상을 설명한다.
- `source-map.md`: 외부 reference와 adaptation 정책을 기록한다.

## 운영 규칙

- `AGENTS.md`는 짧고 항상 읽혀도 좋은 내용만 둔다.
- 긴 절차와 상황별 작업 방식은 skill이나 `docs/harness/`로 분리한다.
- 기본 제공 skill은 범용 engineering workflow로 제한한다.
- 기본 제공 agent는 범용 engineering 역할로 제한한다.
- 제품, 도메인, stack별 skill과 agent는 template에 넣지 않고 file bootstrap 후 프로젝트가 추가한다.
- `CONTEXT.md`는 glossary로만 사용하고 구현 세부나 작업 계획을 넣지 않는다.
- `docs/adr/`에는 되돌리기 어렵고 맥락 없이는 놀라운 decision만 짧게 기록한다.
- 새 skill을 추가할 때는 `harness/skills/<name>/SKILL.md`에 먼저 작성한다.
- 새 agent를 추가할 때는 `harness/agents/<name>.md`에 먼저 작성한다.
- mirror directory는 손으로 직접 고치지 않고 `scripts/sync-agent-skills.sh`로 갱신한다.
- 프로젝트가 template 파일로 bootstrap된 뒤에는 모든 파일을 수정할 수 있다. 이 문서의 구조는 강제 정책이 아니라 좋은 기본값이다.
- 생성 이후 프로젝트는 template upstream을 추적하지 않는다. 이 starter는 dependency가 아니라 시작점이다.
- stack별 기본 앱이 필요하면 이 template에 섞지 않고 별도 variant로 만든다.
- file bootstrap 후 자동 변환 script는 제공하지 않는다. `scripts/check-harness.sh`는 구조와 미작성 항목을 보고할 뿐 파일을 수정하지 않는다.
- file bootstrap 후 이름 변경은 사람이 checklist를 보고 수행한다. 자동 rename script는 제공하지 않는다.
- 기본 CI는 harness 구조만 검증한다. application CI는 프로젝트가 file bootstrap 후 추가한다.
- 기본 CI는 GitHub Actions로 제공한다.
