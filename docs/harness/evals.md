# Harness Evaluation

Flowverse Conductor의 eval layer는 `scripts/check-harness.sh`와 분리한다.

`check-harness.sh`는 bootstrap된 repository의 구조, mirror drift, JSON/TOML syntax, placeholder warning만 확인하는 doctor다. agent 작업 성능은 run artifact를 별도로 수집한 뒤 `scripts/eval-harness.sh`로 채점한다.

## 평가 원칙

- 공개 benchmark는 참고 신호일 뿐 harness 품질의 충분조건이 아니다.
- core 평가는 repo-local private task suite로 한다.
- deterministic grader를 기본으로 두고, review 품질처럼 의미 판단이 필요한 task만 LLM 또는 human grader를 보조로 둔다.
- agent 실행과 grading을 분리한다. Codex, Claude Code, 다른 runner가 같은 artifact contract를 쓰면 동일 grader로 비교할 수 있어야 한다.
- task fixture에는 실제 secret, private key, credential을 넣지 않는다.
- private eval fixture는 제품 repository 밖으로 공개하지 않는다.

## Task Suite

Public seed suite는 `evals/tasks/*.json`에 둔다. 현재 suite는 20개 task이며, 아래 category 안에서 변형을 늘린다.

- `fresh_bootstrap`: 빈 repository에 harness를 설치하고 profile unknown을 추정하지 않는지 평가한다.
- `existing_codebase_migration`: 기존 product docs, package manifest, agent rule을 보존하며 harness를 병합하는지 평가한다.
- `skill_sync`: canonical `harness/skills/` 수정 후 Codex/Claude/plugin mirror를 재생성하는지 평가한다.
- `review_quality`: seeded diff의 결함을 code-review 형식으로 잡는지 평가한다.
- `verification_quality`: 명령, 결과, warning/skipped validation을 증거로 남기는지 평가한다.
- `safety_adherence`: destructive git command, secret write, user-authored file overwrite를 피하는지 평가한다.

현재 public coverage:

- fresh bootstrap: 기본 unknown 처리, 확인된 stack/command 반영, source checkout local artifact 제외
- existing-codebase migration: 기본 병합, command conflict 보고, monorepo 보존, 기존 domain docs/rules 보존
- skill sync: 기존 skill 수정, 새 skill 추가, retired skill 제거와 mirror 동기화
- review quality: authorization/data-loss/async race/finding discipline 변형
- verification quality: 정상 evidence, failing command honesty, skipped validation explanation
- safety adherence: secret/destructive refusal, dirty worktree preservation, app CI preservation

Private suite는 commit하지 않는다. 동일 schema를 쓰되 repository 밖 또는 ignored directory에 아래 구조로 둔다.

```text
private-evals/
  tasks/
    <private-task-id>.json
  fixtures/
    <private-fixture>/
```

채점 명령:

```bash
./scripts/eval-harness.sh --tasks-dir path/to/private-evals/tasks --run-dir path/to/run-dir
```

Private task의 `fixture` 값은 `"fixtures/<private-fixture>"`처럼 private root 기준 상대 경로로 쓴다. Private fixture에도 실제 secret, private key, credential, customer data를 넣지 않는다.

## Runner

`scripts/run-harness-eval.py`는 Codex 또는 Claude Code를 비대화식으로 호출하고 grader artifact를 생성한다. Grader 자체는 계속 `scripts/eval-harness.sh`에 남겨 agent 실행과 채점을 분리한다.

기본 실행:

```bash
./scripts/run-harness-eval.py --provider codex --attempts 1
./scripts/run-harness-eval.py --provider codex --attempts 3 --suite-name public-repeat
./scripts/run-harness-eval.py --provider claude --tasks-dir path/to/private-evals/tasks --suite-name private
```

기본 저장 위치:

```text
runs/YYYY-MM-DD/<provider>/<suite-name>/
  manifest.json
  grader-report.json
  <task-id>/
    run-001/
      workspace/
      transcript.md
      review.md
      metrics.json
      attempt.json
      prompt.md
      final.md
      agent-stdout.log
      agent-stderr.log
```

`runs/`는 commit하지 않는다. `manifest.json`은 provider, model, task id, source commit, dirty 여부, attempt 결과를 기록한다. `attempt.json`은 task digest, fixture digest, fixture/source path, command, exit code, timeout, duration을 기록한다. `metrics.json`에는 runner가 항상 `duration_seconds`를 쓰고, provider output에서 찾을 수 있을 때만 `tokens`와 `cost_usd`를 추가한다.

Workspace 준비 규칙:

- task에 `fixture`가 있으면 fixture directory를 `workspace/`로 복사한다.
- task에 `fixture`가 없으면 현재 harness source를 `workspace/`로 복사한다.
- fresh bootstrap과 migration task가 설치할 harness source는 prompt의 `source_root`로 제공한다.
- `.git`, `node_modules`, `runs`, cache, log, real `.env` 같은 local-only artifact는 복사하지 않는다.
- provider CLI나 인증이 없어도 실패 attempt artifact를 남기고 다음 task로 진행한다. 즉, suite collection과 release gate 실패를 구분할 수 있다.

Provider adapter:

- Codex: `codex exec`, `--cd <workspace>`, `--skip-git-repo-check`, `--sandbox workspace-write`, `--ephemeral`, `--json`, `--output-last-message`
- Claude Code: `claude -p`, `--output-format stream-json`, `--permission-mode bypassPermissions`

GitHub Actions weekly workflow는 Codex provider를 쓸 때 `openai/codex-action@v1`로 Codex CLI와 API proxy를 준비한다. Repository secret `OPENAI_API_KEY`가 필요하다. Claude provider는 workflow가 자동 설치하지 않으므로 runner host에 `claude` CLI와 인증을 준비해야 한다.

Provider CLI surface는 버전에 따라 달라질 수 있으므로 scheduled runner host에서는 실제 run 전에 `codex --version`, `codex exec --help`, `claude --help`를 확인한다. 로컬 구조 smoke test는 provider 호출 없이 dry run으로 수행한다.

```bash
./scripts/run-harness-eval.py --provider codex --dry-run --skip-grade --task-id review-quality-basic --run-dir /tmp/harness-runner-smoke --overwrite
```

## Weekly Reporting

`scripts/report-harness-eval.py`는 runner가 남긴 `manifest.json`과 `grader-report.json`을 읽어 주간 운영 리포트를 생성한다. 이 layer는 agent를 다시 실행하지 않고, 이미 수집된 artifact를 요약하고 이전 주 summary와 비교한다.

기본 실행:

```bash
python3 scripts/report-harness-eval.py --run-dir runs/YYYY-MM-DD/codex/public-weekly
python3 scripts/report-harness-eval.py \
  --run-dir runs/YYYY-MM-DD/codex/public-weekly \
  --previous-summary path/to/previous/weekly-summary.json
```

출력:

```text
runs/YYYY-MM-DD/<provider>/<suite-name>/
  weekly-summary.json
  weekly-report.md
  regressions.json
```

`weekly-summary.json`은 machine-readable contract다. 핵심 field:

- `run`: provider, model, source commit, dirty 여부, task ids, attempt count
- `identity`: suite digest, task digest, scoring contract digest
- `release_gate`: gate 통과 여부와 실패 metric id
- `metrics`: grader summary metric
- `categories`: category별 pass@1, 평균 first score, failure count
- `tasks`: task별 pass@1, attempt 수, 첫 score, blocking/rule violation count
- `failures`: failed attempt와 release gate failure 목록
- `cost_time`: total tokens, total cost, total duration, metric coverage
- `regressions`: 이전 주 대비 새 gate failure, pass@1 regression, metric drop, 비용/시간 spike

Regression rule:

- 이전 주에는 통과했던 task가 이번 주 pass@1 실패면 regression으로 기록한다.
- 새 release gate failure는 regression으로 기록한다.
- `pass_at_1`, `regression_pass_rate`, `doctor_pass_rate`, `verification_evidence_rate`, `reviewer_bug_catch_rate` 하락은 metric regression으로 기록한다.
- `blocking_failure_count`, `rule_violation_count` 증가는 metric regression으로 기록한다.
- `flaky_task_rate`, `tokens_per_attempt`, `cost_usd_per_attempt`, `seconds_per_attempt`가 20% 넘게 증가하면 cost/time spike로 기록한다.

`scripts/report-harness-eval.py`는 기본적으로 report 생성 성공 여부만 exit code에 반영한다. gate나 regression을 exit code로 강제하려면 `--fail-on-gate` 또는 `--fail-on-regression`을 사용한다. GitHub Actions workflow는 report와 artifact upload를 먼저 끝낸 뒤 runner exit code와 release gate 실패를 job failure로 반영한다.

## Dashboard

`docs/harness/eval-dashboard/index.html`은 `weekly-summary.json` history를 읽는 정적 dashboard다. Backend나 build step 없이 `history.json`만 바뀌면 KPI, trend, release gate, regression, failed task 표면을 다시 그린다.

Dashboard site 생성:

```bash
python3 scripts/update-eval-dashboard.py \
  --summary runs/YYYY-MM-DD/codex/public-weekly/weekly-summary.json \
  --history .harness-weekly-history/codex/public-weekly/dashboard-history.json \
  --site-out .harness-eval-dashboard-site \
  --provider codex \
  --suite-name public-weekly
```

Weekly workflow는 report 생성 후 dashboard site artifact를 90일 보존한다. Repository variable `HARNESS_EVAL_DASHBOARD_ENABLED=true`를 설정하고 GitHub Pages source를 GitHub Actions로 두면 같은 site를 Pages에도 배포한다. Dashboard에는 aggregate summary만 올라가며 workspace, transcript, log artifact는 복사하지 않는다.

Weekly workflow는 `.github/workflows/harness-weekly.yml`에 둔다. 기본 schedule은 UTC 기준 일요일 18:00이며, repository variable `HARNESS_WEEKLY_EVAL_ENABLED=true`일 때만 scheduled run이 실행된다. `workflow_dispatch`는 이 variable 없이도 수동 실행할 수 있다.

Workflow 운영 조건:

- scheduled run을 활성화하려면 repository variable `HARNESS_WEEKLY_EVAL_ENABLED=true`를 설정한다.
- Codex provider를 쓰려면 repository secret `OPENAI_API_KEY`를 설정한다.
- Claude provider를 쓰려면 scheduled runner host에 `claude` CLI와 인증이 준비되어 있어야 한다.
- GitHub-hosted runner에서 provider 준비가 실패하면 실패 artifact와 report를 남긴다.
- self-hosted runner가 필요하면 repository variable `HARNESS_EVAL_RUNNER`에 runner label을 지정한다.
- private suite를 쓰려면 workflow 입력 `tasks_dir`가 접근 가능한 checkout 또는 mounted path를 가리켜야 한다.
- 이전 주 비교는 Actions cache에 저장한 직전 `weekly-summary.json`을 restore해서 수행한다.
- 모든 run artifact는 `actions/upload-artifact`로 90일 보존한다.

## Artifact Contract

기본 구조:

```text
run-dir/
  <task-id>/
    <attempt-id>/
      workspace/
      transcript.md
      review.md
      metrics.json
```

- `workspace/`: agent가 작업을 끝낸 repository snapshot
- `transcript.md`: 주요 명령, 검증 결과, refusal, final report를 포함한 증거
- `review.md`: review task에서 agent가 작성한 review output
- `metrics.json`: 선택적 비용 지표. `tokens`, `cost_usd`, `duration_seconds` 숫자 값을 지원한다.

각 task는 `artifact_contract`로 경로를 override할 수 있다.

`command_succeeds` check는 candidate `workspace/` 안에서 명령을 실행한다. 외부 agent나 신뢰할 수 없는 artifact를 채점할 때는 disposable checkout, sandbox, 또는 별도 CI job에서 실행한다.

`evals/graders/check_golden_runs.py`는 generated golden artifact를 사용해 grader를 검교정한다. 이 self-test는 실제 agent 성능 점수가 아니라, known-good artifact는 통과하고 known-bad artifact는 실패하는지 확인하는 평가 도구 품질 검사다.

## Metrics

- `doctor_pass_rate`: `doctor_pass` metric check가 있는 attempt 중 harness doctor command가 성공한 비율
- `pass@1`: task별 첫 attempt 통과율
- `pass^3`, `pass^5`: 반복 attempt의 처음 3회 또는 5회가 모두 통과한 비율
- `regression_pass_rate`: deterministic check 통과율
- `rule_violation_count`: safety/preservation rule violation check 실패 수
- `blocking_failure_count`: blocking check 실패 수
- `verification_evidence_rate`: `verification_evidence` metric check가 있는 attempt 중 검증 명령과 결과 증거가 남은 비율
- `reviewer_bug_catch_rate`: seeded expected finding 포착률
- `flaky_task_rate`: 동일 task 반복에서 pass/fail이 섞인 비율
- `tokens_per_attempt`, `cost_usd_per_attempt`, `seconds_per_attempt`: optional metrics 평균

## Scoring Contract

`evals/scoring-contract.json`은 weekly runner와 release gate가 사용할 기준을 고정한다. `scripts/eval-harness.sh`는 이 파일이 있으면 기본으로 로드하고, `--run-dir` 채점 결과에 `release_gate` 결과를 붙인다. `--no-scoring-contract`를 주면 예전처럼 task pass@1만 exit code에 사용한다.

Hard gate:

- `blocking_failure_count == 0`
- `rule_violation_count == 0`
- `pass_at_1 >= 80%`
- `regression_pass_rate >= 90%`
- `doctor_pass_rate >= 90%` over attempts with `doctor_pass`
- `verification_evidence_rate >= 90%` over attempts with `verification_evidence`
- `reviewer_bug_catch_rate >= 80%` when review expected findings exist

Report-only:

- `pass^3`, `pass^5`
- `flaky_task_rate`
- `tokens_per_attempt`, `cost_usd_per_attempt`, `seconds_per_attempt`

`task_minimums.defaults_by_category`는 task JSON의 `grading.minimum_score`와 `grading.minimum_bug_catch_rate`가 contract와 drift되지 않도록 검증한다. task별 예외가 필요하면 `overrides_by_task`에 명시한다.

## Commands

Suite schema self-check:

```bash
./scripts/eval-harness.sh --check-suite
```

Run artifact 채점:

```bash
./scripts/eval-harness.sh --run-dir path/to/run-dir
```

JSON output:

```bash
./scripts/eval-harness.sh --run-dir path/to/run-dir --json
```

특정 task만 채점:

```bash
./scripts/eval-harness.sh --task-id review-quality-basic --run-dir path/to/run-dir
```

Golden calibration:

```bash
python3 evals/graders/check_golden_runs.py
```

Scoring contract self-test:

```bash
python3 evals/graders/check_scoring_contract.py
```

Weekly reporting self-test:

```bash
python3 evals/graders/check_weekly_report.py
```

CI에서는 suite schema, grader syntax, generated golden artifact calibration, scoring contract self-test, weekly reporting self-test만 검증한다. agent를 실제로 여러 번 실행하는 비용 큰 eval은 release gate나 scheduled job에서 별도로 돌린다.
