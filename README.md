# Flowverse Conductor Agent Harness

이 저장소는 새 프로젝트를 시작할 때 파일을 다운로드하거나 복사해서 쓰는 회사 공통 agent harness starter입니다. 목표는 Codex와 Claude Code가 같은 프로젝트 규칙, 같은 작업 절차, 같은 재사용 skill을 읽도록 만드는 것입니다.

## 처음 적용하는 법

Flowverse Conductor를 새 repository나 기존 application repository에 처음 적용할 때는 `MIGRATE_EXISTING_CODEBASE.md`를 Codex나 Claude Code에 먼저 제공합니다. 이 파일은 repo-local skill이 설치되기 전에도 동작하는 수동 bootstrap runbook입니다.

대상 repository에서 Codex나 Claude Code를 열고 `MIGRATE_EXISTING_CODEBASE.md`의 전체 내용과 아래 지시를 함께 전달합니다.

```text
Install the Flowverse Conductor agent harness into the current repository using this runbook.
Use https://github.com/Dudaeeee/flowverse-conductor.git as the source harness.
If this repository is empty or brand new, install the harness directly.
If this repository already has source code or project docs, preserve existing files and migrate safely.
```

agent는 먼저 대상 repository를 점검한 뒤 두 가지 mode 중 하나로 진행합니다.

- Fresh target mode: 비어 있거나 아직 의미 있는 application source가 없는 repository입니다. source harness를 직접 설치하되 source `.git` history와 local-only artifact는 가져오지 않습니다.
- Existing-codebase mode: 이미 source code, package manifest, docs, CI, deployment config, database file, agent instruction이 있는 repository입니다. 기존 파일을 덮어쓰지 않고 충돌 파일을 merge 대상으로 분류한 뒤, 기존 코드 분석 결과를 harness 문서에 반영합니다.

설치가 끝나면 agent는 `starter` skill을 사용해 `docs/harness/project-profile.md`, `CONTEXT.md`, `AGENTS.md`를 프로젝트에 맞게 채웁니다. 아직 확정되지 않은 제품 의도, stack, command, deployment 정책은 추정하지 않고 사용자에게 질문하거나 "not chosen yet"으로 기록합니다.

Codex는 `.agents/skills/`를 repo-scoped skills로 읽습니다. Claude Code에서는 `CLAUDE.md`가 `AGENTS.md`를 import하고, `.claude/skills/` 아래 skill이 `/skill-name`으로 노출됩니다.

수동으로 적용해야 한다면 아래 순서로 진행합니다.

1. `./scripts/check-harness.sh`를 실행해 구조와 미작성 항목을 확인합니다.
2. `docs/harness/rename-checklist.md`를 보고 starter 이름과 placeholder를 프로젝트 이름으로 바꿉니다.
3. `docs/harness/project-profile.md`를 실제 제품, stack, command, 환경, 제약에 맞게 채웁니다.
4. `CONTEXT.md`를 프로젝트 domain glossary로 갱신합니다.
5. `AGENTS.md`를 실제 repository 규칙과 검증 명령에 맞게 조정합니다.
6. skill이나 agent를 수정했으면 `./scripts/sync-agent-skills.sh`를 실행합니다.
7. `./scripts/check-harness.sh`를 다시 실행합니다.

마지막으로 agent가 가능한 검증을 실행하게 합니다.

```bash
./scripts/check-harness.sh
```

대상 프로젝트의 install, lint, typecheck, test, build command가 확인되었고 실행해도 안전하다면 함께 검증합니다. 실행하지 못한 검증은 이유를 보고해야 합니다.

## 구성

- `AGENTS.md`: Codex와 다른 agent가 읽는 canonical 프로젝트 지침입니다.
- `CLAUDE.md`: Claude Code adapter입니다. `@AGENTS.md`를 import해서 지침을 중복하지 않습니다.
- `CONTEXT.md`: 프로젝트의 domain glossary입니다. 구현 세부가 아니라 용어 정의만 둡니다.
- `docs/adr/`: 중요한 decision record를 짧게 남기는 위치입니다.
- `harness/skills/`: 회사가 관리하는 skill 원본입니다.
- `harness/agents/`: 회사가 관리하는 reusable subagent/custom agent 원본입니다.
- `.agents/skills/`: Codex repo-scoped skill mirror입니다. plugin 설치 없이 Codex가 읽을 수 있습니다.
- `.claude/skills/`: Claude Code용 project-local skill mirror입니다.
- `.claude/agents/`: Claude Code용 project-local subagent mirror입니다.
- `.codex/agents/`: Codex용 project-scoped custom agent mirror입니다.
- `plugins/company-agent-harness/`: Codex plugin adapter입니다.
- `.agents/plugins/marketplace.json`: Codex repo marketplace entry입니다.
- `docs/harness/`: 운영 방식, adapter 전략, 프로젝트별 agent 운영 계약입니다.
- `docs/harness/rename-checklist.md`: file bootstrap 후 starter 이름과 placeholder를 바꾸는 checklist입니다.
- `scripts/sync-agent-skills.sh`: skill과 agent 원본을 Codex와 Claude 위치로 동기화합니다.
- `scripts/render-agent-mirrors.py`: `harness/agents/`를 Codex TOML과 Claude Markdown mirror로 변환합니다.
- `scripts/check-harness.sh`: file bootstrap 후 harness 구조와 미작성 항목을 점검하는 doctor script입니다.
- `evals/`: agent 작업 성능을 평가하는 repo-local task suite, fixture, deterministic grader입니다.
- `scripts/eval-harness.sh`: eval task schema와 agent run artifact를 채점하는 wrapper입니다.
- `scripts/run-harness-eval.py`: Codex 또는 Claude Code를 호출해 eval run artifact를 생성하는 runner입니다.
- `scripts/report-harness-eval.py`: eval run artifact를 weekly summary/report/regression으로 변환하는 reporter입니다.
- `scripts/update-eval-dashboard.py`: weekly summary history를 누적하고 정적 eval dashboard site를 생성합니다.
- `docs/harness/eval-dashboard/`: weekly eval dashboard의 정적 frontend입니다.
- `.github/workflows/harness.yml`: harness 구조만 검증하는 최소 CI입니다.
- `.github/workflows/harness-weekly.yml`: provider를 실제 호출하는 scheduled/manual weekly eval workflow입니다.

이 template은 agent harness만 담는 빈 프로젝트 기반입니다. application framework, product code, runtime-specific starter app은 포함하지 않습니다.
Codex repo skill mirror, Codex plugin adapter, Codex custom agent mirror, Claude Code skill mirror, Claude Code agent mirror는 실제 파일로 포함합니다. 그래서 file bootstrap 직후 각 도구가 harness를 바로 읽을 수 있습니다.
First-class adapter는 Codex와 Claude Code만 지원합니다. 다른 도구는 공통 문서와 `AGENTS.md`를 통한 best-effort 사용 범위에 둡니다.
이 template source repository는 GitHub에 올라가는 것을 전제로 합니다. 기본 CI는 GitHub Actions로 제공합니다.

## 설계 원칙

- 지침의 원천은 하나입니다. `AGENTS.md`가 canonical이고 `CLAUDE.md`는 adapter입니다.
- `AGENTS.md`는 항상 읽히는 lean guide입니다. 세부 workflow는 skills와 `docs/harness/`에 둡니다.
- skill 원천도 하나입니다. `harness/skills/`를 수정하고 mirror는 script로 재생성합니다.
- agent 원천도 하나입니다. `harness/agents/`를 수정하고 `.codex/agents/`, `.claude/agents/` mirror는 script로 재생성합니다.
- 기본 skill과 agent는 범용 engineering workflow만 포함합니다. 제품, 도메인, stack별 skill/agent는 file bootstrap 후 각 프로젝트에서 추가합니다.
- `CONTEXT.md`와 `docs/adr/`는 기본 포함합니다. 프로젝트 용어와 durable decision은 처음부터 기록 가능한 상태로 둡니다.
- upstream skill pack은 직접 starter로 복제하지 않습니다. 회사 정책, 프로젝트 profile, tool adapter를 이 repo가 소유합니다.
- Superpowers methodology는 baseline workflow로 흡수하되 원문을 vendor하지 않고, 회사 harness 문체와 Codex/Claude adapter 정책에 맞게 재작성합니다.
- 모든 자동화는 검증 가능해야 합니다. agent가 파일을 수정하면 관련 lint, test, build, manual check 중 가능한 것을 실행해야 합니다.
- 새 프로젝트가 `Download ZIP` 또는 release archive로 bootstrap된 뒤에는 프로젝트가 전체 repo의 소유권을 갖습니다. 모든 파일은 프로젝트 맥락에 맞게 수정할 수 있습니다.
- file bootstrap 이후 프로젝트는 이 template repo의 업데이트를 자동 또는 정기적으로 받지 않습니다. 필요한 개선사항은 각 프로젝트가 판단해서 수동으로 반영합니다.
- 이 template은 특정 application stack을 선택하지 않습니다. stack별 starter가 필요하면 별도 template variant로 분리합니다.
- tool adapter mirror는 repo에 commit합니다. 권장 수정 위치는 `harness/skills/`와 `harness/agents/`이고, mirror는 `./scripts/sync-agent-skills.sh`로 재생성합니다.
- file bootstrap 후 점검은 doctor script로만 제공합니다. 자동 변환이나 대량 rewrite를 수행하는 init script는 제공하지 않습니다.
- file bootstrap 후 starter 이름 변경은 checklist로 제공합니다. 자동 rename script는 제공하지 않습니다.
- CI는 harness 검증만 포함합니다. application build/test/deploy CI는 file bootstrap 후 각 프로젝트가 추가합니다.
- GitHub hosting을 전제로 합니다. GitHub Actions workflow는 harness template의 기본 검증 표면입니다.
- Codex plugin package name `company-agent-harness`는 기본적으로 유지합니다. 이 이름은 프로젝트 제품명이 아니라 사내 harness adapter를 가리킵니다.
- 지원 adapter 범위는 Codex와 Claude Code로 제한합니다. 다른 agent tool 전용 파일은 실제 필요가 생길 때 별도 결정으로 추가합니다.

## Agent Harness Eval

`./scripts/check-harness.sh`는 구조 doctor이고, agent 작업 성능 평가는 별도 eval layer에서 다룹니다. `evals/tasks/*.json`은 fresh bootstrap, existing-codebase migration, skill sync, review quality, verification quality, safety adherence seed task를 선언합니다. 실제 agent 실행 결과는 run artifact로 저장한 뒤 아래처럼 채점합니다.

```bash
./scripts/eval-harness.sh --check-suite
./scripts/run-harness-eval.py --provider codex --attempts 1
./scripts/eval-harness.sh --run-dir path/to/run-dir
python3 scripts/report-harness-eval.py --run-dir path/to/run-dir
python3 scripts/update-eval-dashboard.py \
  --summary path/to/run-dir/weekly-summary.json \
  --history .harness-weekly-history/codex/public-weekly/dashboard-history.json \
  --site-out .harness-eval-dashboard-site \
  --provider codex \
  --suite-name public-weekly
python3 evals/graders/check_golden_runs.py
python3 evals/graders/check_scoring_contract.py
python3 evals/graders/check_weekly_report.py
python3 evals/graders/check_eval_dashboard.py
```

`scripts/run-harness-eval.py`는 Codex 또는 Claude Code를 호출해 `runs/YYYY-MM-DD/<provider>/<suite>/` 아래 artifact를 생성합니다. 자세한 runner 설계와 artifact contract는 `docs/harness/evals.md`와 `evals/README.md`를 보세요.

Weekly workflow는 매 run마다 dashboard site artifact도 생성합니다. GitHub Pages로 바로 배포하려면 repository variable `HARNESS_EVAL_DASHBOARD_ENABLED=true`를 설정하고 Pages source를 GitHub Actions로 둡니다.

주간 자동 실행을 켜려면 repository variable `HARNESS_WEEKLY_EVAL_ENABLED=true`가 필요합니다. Codex provider를 GitHub-hosted runner에서 실행할 때는 repository secret `OPENAI_API_KEY`도 설정합니다. Workflow는 `openai/codex-action@v1`로 Codex CLI와 API proxy를 준비한 뒤 runner를 호출합니다.

## 참고

상세한 adapter 전략은 `docs/harness/adapters.md`, 외부 reference와 adaptation 기준은 `docs/harness/source-map.md`를 보세요.
