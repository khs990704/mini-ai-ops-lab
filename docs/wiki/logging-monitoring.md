# 로깅과 모니터링

## 짧은 정의

로깅은 발생한 사건을 기록하는 일이다. 모니터링은 시스템이나 애플리케이션 상태를 시간에 따라 관찰하여 문제를 발견하는 일이다.

structured log는 상태와 시각 같은 정보를 정해진 field로 기록한 로그다. JSONL은 한 줄에 JSON 객체 하나를 저장하는 형식으로, 기존 파일 전체를 다시 쓰지 않고 새 실행 기록을 추가하기 좋다.

## 이 프로젝트에서 중요한 이유

이 프로젝트는 가장 단순한 운영 증거인 structured log부터 시작한다. 로그를 통해 어떤 작업이 실행됐는지, 성공했는지, 얼마나 걸렸는지, 어떤 metric이 생성됐는지, 무엇이 실패했는지 확인할 수 있다.

## 저장소에서 사용되는 위치

- `logs/runs.jsonl`
- `logs/audit.jsonl`
- `logs/errors.jsonl`
- `src/run_job.py`
- `src/tool_runner.py`

### Day 4 성공 run log

`src/run_job.py`는 학습과 model 저장이 성공하면 다음 field를 `logs/runs.jsonl`에 한 줄로 추가한다.

- `run_id`: 실행과 artifact를 연결하는 고유 식별자
- `status`: 현재는 성공을 의미하는 `success`
- `started_at`, `ended_at`: UTC ISO 8601 형식의 실행 시작·종료 시각
- `duration_seconds`: `perf_counter()`로 측정한 경과 시간
- `metrics`: accuracy와 학습·검증 sample 수
- `artifact_path`: 해당 실행에서 생성한 model 위치

## 알아둘 명령어나 코드

```bash
python src/run_job.py
tail -n 3 logs/runs.jsonl
tail -n 5 logs/audit.jsonl
wc -l logs/runs.jsonl
```

`python src/run_job.py`는 새 artifact를 만들고 run log 한 줄을 추가한다. `tail`과 `wc`는 로그를 변경하지 않고 최근 기록이나 전체 줄 수를 확인한다.

## 흔한 실패 사례

- 실패: 로그가 구조화되지 않았거나 필요한 필드가 없음
- 증상: 장애가 발생했지만 원인을 추적할 수 없음
- 확인할 것: 로그 schema, 예외 처리, run ID의 일관성
- 복구 방법: 상태, 시각, 실행 시간, 오류, artifact 경로를 일관된 필드로 기록함
- 실패: 의도한 프로젝트 로그가 보이지 않음
- 증상: 실행은 성공했지만 `logs/runs.jsonl`을 찾을 수 없음
- 확인할 것: 명령을 실행한 현재 작업 디렉터리와 상대 경로
- 복구 방법: 프로젝트 root에서 `python src/run_job.py`를 실행함

## 실용적인 이해

로그는 운영 장애를 이해할 때 가장 먼저 확인하는 자료다. 이 프로젝트는 학습 작업과 도구 호출을 한 건씩 추적할 수 있도록 run log와 audit log를 JSONL 형식으로 기록한다.

`logs/`는 실행 과정에 관한 기록을 보관한다. 반면 `artifacts/`는 실행이 만든 모델과 같은 실제 결과물을 보관한다.

현재 모든 학습 실행 기록은 하나의 `logs/runs.jsonl`에 누적되고, model은 `artifacts/{run_id}/model.pkl`에 실행별로 분리된다. 로그의 `run_id`와 `artifact_path`를 사용하면 어떤 실행이 어느 model을 만들었는지 찾을 수 있다. `open("a")`의 append mode는 파일이 없으면 만들고, 있으면 기존 내용 끝에 새 JSON 한 줄을 추가한다.

## Codex Q&A 기록

- 질문: Day 3까지는 학습한 model을 저장하고 Day 4에는 그 학습의 로그까지 기록하는 것인가?
  답변: 맞다. `model.pkl`은 학습 결과물이고 `runs.jsonl`은 실행 시각, 상태, metric, 결과물 경로를 설명하는 운영 이력이다. 두 데이터는 같은 `run_id`로 연결된다.
- 질문: 현재는 실행 로그 파일 하나를 지정하고 학습 후 로그를 추가하는 방식인가?
  답변: 맞다. 모든 성공 run은 `logs/runs.jsonl`에 JSON 한 줄씩 누적되고, model artifact만 run ID별 디렉터리로 분리된다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [MLOps](mlops.md)
