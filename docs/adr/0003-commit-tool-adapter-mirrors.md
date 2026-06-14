# Commit Tool Adapter Mirrors

Codex repo skill mirror, Codex plugin skill mirror, Codex custom agent mirror, Claude Code project skill mirror, Claude Code project subagent mirror는 template source repository에 실제 파일로 commit한다.

Adapter 파일을 file bootstrap 후 별도 setup으로 만들 수도 있었지만, 이 template의 가치는 bootstrap 직후 agent harness가 바로 작동하는 데 있다. 따라서 중복을 감수하고 canonical `harness/skills/`와 `harness/agents/`에서 mirror를 재생성하는 구조를 선택했다.

Skill mirror는 단순 복사하고, agent mirror는 도구별 format 차이 때문에 render script로 생성한다.
