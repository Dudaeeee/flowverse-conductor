# Rename Checklist

이 template은 자동 rename script를 제공하지 않습니다. 이 repo의 파일을 다운로드하거나 복사해서 새 repository를 시작한 뒤 프로젝트 소유자나 `starter` 스킬을 실행하는 agent가 아래 항목을 확인하고 프로젝트 이름에 맞게 바꿉니다.

## 바꿀 항목

- `README.md` 제목과 설명
- `AGENTS.md`의 프로젝트 이름과 목적
- `CONTEXT.md`의 context 이름과 glossary
- `docs/harness/project-profile.md`의 product section
- `.agents/plugins/marketplace.json`의 marketplace `name`과 `interface.displayName`
- `plugins/company-agent-harness/.codex-plugin/plugin.json`의 `description`, `developerName`
- 기본적으로 `plugins/company-agent-harness/.codex-plugin/plugin.json`의 `name`은 유지한다.
- 명확한 이유가 있으면 `plugins/company-agent-harness/` directory name과 plugin `name`을 바꿀 수 있다.
- plugin directory name을 바꿨다면 `scripts/sync-agent-skills.sh`, `scripts/check-harness.sh`, `docs/harness/adapters.md`, `README.md`의 경로 참조를 함께 바꾼다.

## 권장 순서

1. 제품 이름과 repository slug를 정한다.
2. `docs/harness/project-profile.md`를 채운다.
3. `CONTEXT.md`를 프로젝트 domain glossary로 바꾼다.
4. README와 AGENTS의 프로젝트 이름을 바꾼다.
5. Codex plugin package name은 기본적으로 `company-agent-harness`로 유지한다.
6. 경로를 바꿨다면 `./scripts/sync-agent-skills.sh`를 실행한다.
7. `./scripts/check-harness.sh`를 실행해 남은 placeholder warning을 확인한다.

## Placeholder 검색

```bash
rg -n --hidden "Flowverse|flowverse-conductor|Your Company" \
  --glob '!**/.git/**' \
  --glob '!**/docs/harness/rename-checklist.md' \
  --glob '!**/scripts/check-harness.sh' \
  .
```
