# Harness Evals

이 directory는 Flowverse Conductor agent harness의 작업 성능을 평가하기 위한 repo-local eval suite입니다.

`scripts/check-harness.sh`는 파일 구조와 mirror drift를 확인하는 doctor입니다. 이 eval suite는 agent가 실제 작업을 수행한 결과물을 별도 run artifact로 받아 pass rate, rule violation, verification evidence, review 품질 같은 작업 성능 지표를 계산합니다.

## Layout

- `tasks/*.json`: 공개 seed 평가 task와 deterministic check 선언
- `scoring-contract.json`: release gate metric과 task minimum score 계약
- `fixtures/`: agent에게 제공할 입력 repository 또는 diff fixture
- `graders/harness_eval.py`: task schema 검증과 run artifact 채점기
- `graders/check_golden_runs.py`: generated golden artifact로 grader calibration 검증
- `graders/check_scoring_contract.py`: generated artifact로 scoring contract gate 검증
- `graders/check_weekly_report.py`: generated artifact로 weekly reporting/regression 검증
- `graders/check_eval_dashboard.py`: generated weekly summary로 dashboard history/site 생성 검증
- `../scripts/run-harness-eval.py`: Codex 또는 Claude Code를 호출해 run artifact를 생성하는 runner
- `../scripts/report-harness-eval.py`: manifest와 grader report를 weekly summary/report로 변환
- `../scripts/update-eval-dashboard.py`: weekly summary history와 정적 dashboard site 생성
- `../docs/harness/eval-dashboard/`: dashboard frontend
- `golden-runs/`: golden run self-test 설명

## Public And Private Suites

이 repository에 commit되는 `evals/tasks/*.json`과 `evals/fixtures/`는 public seed suite입니다. 현재 public suite는 20개 task로 fresh bootstrap, existing-codebase migration, skill sync, review quality, verification quality, safety adherence 변형을 포함합니다.

Private suite는 이 repository에 commit하지 않습니다. 동일한 schema를 쓰되 별도 root에 아래처럼 둡니다.

```text
private-evals/
  tasks/
    private-task-id.json
  fixtures/
    private-fixture/
```

채점할 때는 private root의 `tasks` directory를 넘깁니다.

```bash
./scripts/eval-harness.sh --tasks-dir path/to/private-evals/tasks --run-dir path/to/run-dir
```

`fixture` 경로는 tasks directory의 parent를 기준으로 해석되므로 private task에서는 `"fixture": "fixtures/private-fixture"` 형태를 유지합니다. Private fixture에는 실제 secret, production data, customer data를 넣지 않습니다.

## Runner

`scripts/run-harness-eval.py`는 agent 실행과 artifact 생성을 담당합니다. 기본 출력 위치는 `runs/YYYY-MM-DD/<provider>/<suite-name>/`이며 `runs/`는 commit하지 않습니다.

```bash
./scripts/run-harness-eval.py --provider codex --attempts 1
./scripts/run-harness-eval.py --provider codex --attempts 3 --suite-name public-repeat
./scripts/run-harness-eval.py --provider codex --task-id review-quality-basic --run-dir runs/manual/review-smoke
./scripts/run-harness-eval.py --provider claude --tasks-dir path/to/private-evals/tasks --suite-name private
```

Runner는 task에 `fixture`가 있으면 fixture를 `workspace/`로 복사합니다. `fixture`가 없는 skill sync와 verification task는 현재 harness source를 `workspace/`로 복사합니다. Fresh bootstrap과 migration task에서 agent가 설치할 harness source는 prompt에 `source_root`로 명시됩니다. `.git`, `node_modules`, `runs`, cache, log, real `.env` 같은 local-only artifact는 workspace로 복사하지 않습니다.

각 attempt에는 grader가 읽는 `workspace/`, `transcript.md`, `review.md`, `metrics.json` 외에 운영 추적용 `prompt.md`, `final.md`, `agent-stdout.log`, `agent-stderr.log`, `attempt.json`이 저장됩니다. Run root에는 `manifest.json`과, grading을 실행한 경우 `grader-report.json`이 저장됩니다.

Weekly reporting은 같은 run root에 `weekly-summary.json`, `weekly-report.md`, `regressions.json`을 추가합니다.

```bash
python3 scripts/report-harness-eval.py --run-dir runs/YYYY-MM-DD/codex/public
python3 scripts/report-harness-eval.py \
  --run-dir runs/YYYY-MM-DD/codex/public \
  --previous-summary path/to/previous/weekly-summary.json
```

Dashboard site는 weekly summary를 history에 누적한 뒤 생성합니다.

```bash
python3 scripts/update-eval-dashboard.py \
  --summary runs/YYYY-MM-DD/codex/public/weekly-summary.json \
  --history .harness-weekly-history/codex/public/dashboard-history.json \
  --site-out .harness-eval-dashboard-site \
  --provider codex \
  --suite-name public
```

GitHub Actions weekly workflow는 `.github/workflows/harness-weekly.yml`에 있습니다. Scheduled run은 repository variable `HARNESS_WEEKLY_EVAL_ENABLED=true`일 때만 실행되고, 수동 `workflow_dispatch`는 provider, suite, tasks directory, attempts, dry-run 여부를 입력으로 받습니다.

Provider 호출 없이 runner 구조만 확인할 때는 dry run을 사용합니다.

```bash
./scripts/run-harness-eval.py --provider codex --dry-run --skip-grade --task-id review-quality-basic --run-dir /tmp/harness-runner-smoke --overwrite
```

Codex adapter는 `codex exec`를 사용합니다. GitHub Actions weekly workflow에서는 `openai/codex-action@v1`이 Codex CLI와 API proxy를 준비하므로 repository secret `OPENAI_API_KEY`가 필요합니다. Claude adapter는 `claude -p`를 사용하므로 runner를 돌리는 host에 해당 CLI와 인증이 준비되어 있어야 합니다. CLI가 없거나 인증이 없으면 attempt는 실패 artifact로 남고 runner는 다음 task를 계속 실행합니다. 즉, 한 task 실패가 전체 run artifact 수집을 중단하지 않습니다. 중단이 필요하면 `--fail-fast`를 사용합니다.

## Run Artifact Contract

grader는 agent를 직접 실행하지 않습니다. 실행 harness나 사람이 아래 구조로 결과물을 저장한 뒤 채점합니다.

```text
run-dir/
  fresh-bootstrap-basic/
    run-001/
      workspace/
      transcript.md
      metrics.json
  review-quality-basic/
    run-001/
      review.md
      transcript.md
      metrics.json
```

`workspace/`는 agent 작업 후 repository snapshot입니다. `transcript.md`는 agent가 사용한 주요 명령, 검증 결과, refusal, final report를 포함한 작업 증거입니다. `metrics.json`은 선택 사항이며 `tokens`, `cost_usd`, `duration_seconds` 숫자 값을 넣을 수 있습니다.

`command_succeeds` check는 candidate `workspace/` 안에서 명령을 실행합니다. 신뢰할 수 없는 run artifact를 채점할 때는 disposable checkout, sandbox, 또는 CI job처럼 격리된 환경에서 실행하세요.

## Commands

Suite schema만 검증:

```bash
./scripts/eval-harness.sh --check-suite
```

Run artifact 채점:

```bash
./scripts/eval-harness.sh --run-dir path/to/run-dir
```

JSON 출력:

```bash
./scripts/eval-harness.sh --run-dir path/to/run-dir --json
```

특정 task만 채점:

```bash
./scripts/eval-harness.sh --task-id review-quality-basic --run-dir path/to/run-dir
```

grader calibration self-test:

```bash
python3 evals/graders/check_golden_runs.py
python3 evals/graders/check_eval_dashboard.py
```

weekly reporting self-test:

```bash
python3 evals/graders/check_weekly_report.py
```

## Metric Notes

- `doctor_pass_rate`: `doctor_pass` metric check가 있는 attempt 중 harness doctor command가 성공한 비율
- `pass@1`: 각 task의 첫 시도가 통과한 비율
- `pass^3`, `pass^5`: 동일 task 반복 실행에서 처음 3회 또는 5회가 모두 통과한 비율
- `regression_pass_rate`: deterministic check 단위 통과율
- `rule_violation_count`: destructive command, secret write, preservation failure 같은 rule violation check 실패 수
- `blocking_failure_count`: blocking check 실패 수
- `verification_evidence_rate`: `verification_evidence` metric check가 있는 attempt 중 transcript에 검증 명령과 결과 증거가 남은 비율
- `reviewer_bug_catch_rate`: review task의 seeded expected finding 포착률
- `flaky_task_rate`: 같은 task 반복 시도 중 pass/fail이 섞인 task 비율
- `tokens_per_attempt`, `cost_usd_per_attempt`, `seconds_per_attempt`: `metrics.json`이 제공할 때 계산되는 평균 비용 지표

`evals/scoring-contract.json`은 release gate를 정의합니다. 기본 gate는 blocking failure와 rule violation을 0으로 요구하고, `pass@1`, deterministic regression pass rate, verification evidence, doctor pass, review bug catch rate의 minimum threshold를 강제합니다. 비용/시간과 반복 attempt 안정성 metric은 아직 report-only입니다.

`scripts/eval-harness.sh --run-dir ...`는 scoring contract가 있으면 기본으로 gate를 적용합니다. 순수 task pass/fail만 보고 싶을 때는 `--no-scoring-contract`를 사용하세요.

실제 성능 비교에는 public benchmark가 아니라 repo-local private task suite를 함께 사용합니다. 이 template의 public seed task는 구조 예시이므로, 제품 repository에서는 비공개 task와 fixture를 추가해 agent가 외워서 맞힐 수 없는 평가 표면을 유지합니다.

golden run self-test는 agent benchmark가 아닙니다. 채점기가 known-good artifact를 통과시키고 known-bad artifact를 떨어뜨리는지 확인하는 calibration check입니다.
