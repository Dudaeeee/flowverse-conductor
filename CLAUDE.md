@AGENTS.md

## Claude Code

- 이 파일은 Claude Code adapter입니다. 공통 지침은 `AGENTS.md`가 canonical입니다.
- Claude Code project skills는 `.claude/skills/`에 있습니다.
- Claude Code project subagents는 `.claude/agents/`에 있습니다.
- skill이나 agent 원본을 수정한 뒤에는 `./scripts/sync-agent-skills.sh`를 실행해 Claude mirror를 갱신하세요.
- 큰 변경, risky migration, shared architecture 변경은 편집 전에 plan을 먼저 제시하세요.
- 개인 설정은 `CLAUDE.local.md`에 두고 repository에는 commit하지 마세요.
