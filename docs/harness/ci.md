# Harness CI

이 template은 GitHub에 올라가는 것을 전제로 하며, 최소 GitHub Actions workflow를 포함합니다.

## 범위

검증할 것:

- shell script syntax
- Python helper syntax
- eval grader syntax
- eval runner syntax
- eval weekly reporting syntax
- eval dashboard history generator syntax
- eval task schema self-check
- eval golden run calibration self-test
- eval scoring contract self-test
- eval weekly reporting self-test
- eval dashboard self-test
- harness doctor script 실행
- Codex marketplace JSON
- Codex plugin JSON
- Codex custom agent TOML
- skill mirror drift across `.agents/skills/`, `.claude/skills/`, and plugin skills
- agent mirror drift across `.codex/agents/` and `.claude/agents/`
- 필수 harness 파일과 directory 존재 여부

검증하지 않을 것:

- application build
- application test
- deployment
- runtime-specific lint
- framework-specific typecheck
- agent multi-run performance eval
- Codex/Claude provider 호출
- LLM 또는 human grader를 사용하는 subjective eval

이 template은 agent-harness-only template이므로 application CI는 file bootstrap 후 각 프로젝트가 GitHub Actions workflow로 추가합니다.

`scripts/eval-harness.sh --check-suite`, `python3 evals/graders/check_golden_runs.py`, `python3 evals/graders/check_scoring_contract.py`, `python3 evals/graders/check_weekly_report.py`, `python3 evals/graders/check_eval_dashboard.py`는 CI에서 실행해도 agent를 호출하지 않습니다. CI는 `scripts/run-harness-eval.py`도 syntax까지만 확인합니다. 실제 agent를 여러 번 실행하는 비용 큰 eval은 별도 scheduled job, release gate, 또는 수동 benchmark run에서 수행합니다.

## Weekly Eval Workflow

`.github/workflows/harness-weekly.yml`은 실제 provider runner를 호출하는 운영 workflow입니다. 기본 schedule은 UTC 기준 일요일 18:00이지만, scheduled run은 repository variable `HARNESS_WEEKLY_EVAL_ENABLED=true`일 때만 실행합니다. 수동 `workflow_dispatch`는 이 variable 없이도 실행할 수 있습니다.

Workflow가 하는 일:

- `scripts/run-harness-eval.py`로 Codex 또는 Claude suite를 실행한다.
- runner exit code를 저장하되 즉시 job을 중단하지 않는다.
- `scripts/report-harness-eval.py`로 `weekly-summary.json`, `weekly-report.md`, `regressions.json`을 생성한다.
- `scripts/update-eval-dashboard.py`로 누적 `history.json`과 정적 dashboard site를 생성한다.
- Actions cache에서 직전 `weekly-summary.json`을 복원해 regression을 계산한다.
- run artifact와 dashboard site artifact를 90일 보존한다.
- repository variable `HARNESS_EVAL_DASHBOARD_ENABLED=true`이면 GitHub Pages에도 dashboard를 배포한다.
- artifact upload 이후 runner 실패나 release gate 실패를 job failure로 반영한다.

운영 조건:

- scheduled run을 활성화하려면 repository variable `HARNESS_WEEKLY_EVAL_ENABLED=true`를 설정한다.
- Codex provider를 GitHub-hosted runner에서 실행하려면 repository secret `OPENAI_API_KEY`를 설정한다. Workflow는 `openai/codex-action@v1`로 Codex CLI와 API proxy를 준비한 뒤 `scripts/run-harness-eval.py`를 실행한다.
- Claude provider를 실행하려면 runner host에 `claude` CLI와 인증이 준비되어 있어야 한다.
- self-hosted runner를 쓰려면 repository variable `HARNESS_EVAL_RUNNER`에 runner label을 지정한다.
- dashboard를 Pages로 보려면 repository Pages source를 GitHub Actions로 설정하고 `HARNESS_EVAL_DASHBOARD_ENABLED=true`를 둔다.
- private suite는 workflow 입력 `tasks_dir`가 접근 가능한 checkout 또는 mounted path를 가리켜야 한다.
- provider CLI나 인증이 없으면 실패 artifact와 report를 남기는 것이 정상 동작이며, job은 마지막 결과 확인 단계에서 실패한다. Provider 없이 reporting pipeline만 확인하려면 수동 실행에서 `dry_run=true`를 사용한다.

## Warning 정책

`scripts/check-harness.sh`의 warning은 CI를 실패시키지 않습니다. 예를 들어 file bootstrap 직후 `project-profile.md` 미작성이나 starter 이름 잔존은 프로젝트 초기 상태에서 정상적인 warning입니다. 구조 오류, 깨진 JSON, skill mirror drift 같은 문제만 실패로 처리합니다.
