# Context And Decisions

이 template은 `CONTEXT.md`와 `docs/adr/`를 기본 포함합니다.

## CONTEXT.md

`CONTEXT.md`는 project domain glossary입니다. 사람과 agent가 같은 단어를 같은 뜻으로 쓰도록 만드는 문서입니다.

포함할 것:

- domain term
- 선택한 canonical name
- 피해야 할 동의어
- 짧은 정의

넣지 않을 것:

- 구현 세부
- API spec
- 작업 계획
- backlog
- 회의록

## docs/adr/

`docs/adr/`는 durable decision record를 위한 위치입니다. 모든 결정을 기록하지 않습니다.

ADR이 필요한 경우:

- 나중에 바꾸기 어렵다.
- 맥락 없이 보면 놀라운 선택이다.
- 실제 대안이 있었고 trade-off를 거쳐 선택했다.

ADR은 짧게 씁니다. 미래의 reader가 "왜 이렇게 했는가"를 이해할 수 있으면 충분합니다.
