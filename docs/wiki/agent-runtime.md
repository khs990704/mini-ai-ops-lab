# Agent 실행환경

## 짧은 정의

Agent 실행환경은 tool call 요청을 받고, 요청을 검증하며, 허용된 도구만 실행하고, 그 결과를 기록하는 환경이다.

## 이 프로젝트에서 중요한 이유

Agent가 제한 없이 도구를 실행하면 안정성과 보안 문제가 생길 수 있다. 이 프로젝트는 작은 allowlist 기반 도구 실행기를 통해 실행 통제, timeout, 감사 가능성을 구현한다.

## 저장소에서 사용되는 위치

- `configs/tools.yaml`
- `src/tool_runner.py`
- `src/audit_logger.py`
- `logs/audit.jsonl`

## 알아둘 명령어나 코드

```bash
python src/tool_runner.py --tool echo --input "hello"
python src/tool_runner.py --tool unknown
tail -n 5 logs/audit.jsonl
```

## 흔한 실패 사례

- 실패: 허용되지 않은 도구 요청
- 증상: 등록되지 않았거나 위험한 도구 이름이 요청됨
- 확인할 것: `configs/tools.yaml`, `logs/audit.jsonl`
- 복구 방법: 기본적으로 요청을 거부하고 시도 자체를 audit log에 기록함

## 실용적인 이해

Agent 도구 실행은 일반 함수 호출처럼 보이더라도 외부 상태를 바꿀 수 있다. 이 프로젝트에서는 allowlist, 입력 처리, timeout, audit log를 사용해 실행 범위를 제한하고 호출 이력을 추적한다.

## Codex Q&A 기록

아직 기록된 질문이 없다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
