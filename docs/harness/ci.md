# Harness CI

이 template은 GitHub에 올라가는 것을 전제로 하며, 최소 GitHub Actions workflow를 포함합니다.

## 범위

검증할 것:

- shell script syntax
- Python helper syntax
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

이 template은 agent-harness-only template이므로 application CI는 file bootstrap 후 각 프로젝트가 GitHub Actions workflow로 추가합니다.

## Warning 정책

`scripts/check-harness.sh`의 warning은 CI를 실패시키지 않습니다. 예를 들어 file bootstrap 직후 `project-profile.md` 미작성이나 starter 이름 잔존은 프로젝트 초기 상태에서 정상적인 warning입니다. 구조 오류, 깨진 JSON, skill mirror drift 같은 문제만 실패로 처리합니다.
