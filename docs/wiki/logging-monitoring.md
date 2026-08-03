# 로깅과 모니터링

## 짧은 정의

로깅은 발생한 사건을 기록하는 일이다. 모니터링은 시스템이나 애플리케이션 상태를 시간에 따라 관찰하여 문제를 발견하는 일이다.

## 이 프로젝트에서 중요한 이유

이 프로젝트는 가장 단순한 운영 증거인 structured log부터 시작한다. 로그를 통해 어떤 작업이 실행됐는지, 성공했는지, 얼마나 걸렸는지, 어떤 metric이 생성됐는지, 무엇이 실패했는지 확인할 수 있다.

## 저장소에서 사용되는 위치

- `logs/runs.jsonl`
- `logs/audit.jsonl`
- `logs/errors.jsonl`
- `src/run_job.py`
- `src/tool_runner.py`

## 알아둘 명령어나 코드

```bash
tail -n 5 logs/runs.jsonl
tail -n 5 logs/audit.jsonl
wc -l logs/runs.jsonl
```

## 흔한 실패 사례

- 실패: 로그가 구조화되지 않았거나 필요한 필드가 없음
- 증상: 장애가 발생했지만 원인을 추적할 수 없음
- 확인할 것: 로그 schema, 예외 처리, run ID의 일관성
- 복구 방법: 상태, 시각, 실행 시간, 오류, artifact 경로를 일관된 필드로 기록함

## 실용적인 이해

로그는 운영 장애를 이해할 때 가장 먼저 확인하는 자료다. 이 프로젝트는 학습 작업과 도구 호출을 한 건씩 추적할 수 있도록 run log와 audit log를 JSONL 형식으로 기록한다.

`logs/`는 실행 과정에 관한 기록을 보관한다. 반면 `artifacts/`는 실행이 만든 모델과 같은 실제 결과물을 보관한다.

## Codex Q&A 기록

아직 이 카테고리에 기록할 별도의 질문은 없다. 프로젝트 디렉터리 전체 역할에 관한 질문은 [MLOps](mlops.md)에 정리되어 있다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [MLOps](mlops.md)
