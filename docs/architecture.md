# Architecture

## 목적

Mini AI Ops Lab은 작은 머신러닝 학습 작업을 실행 가능한 script에서 추적 가능한 운영 job으로 발전시키는 프로젝트다. 현재 architecture는 model 정확도 개선보다 설정 검증, 실행 식별, 결과 보존, 성공·실패 기록과 재현 가능한 실행환경에 집중한다.

## 현재 구현 범위

Day 8에 구현된 범위는 다음과 같다.

- Iris 분류 model 학습과 accuracy 계산
- 실행별 고유 run ID 생성
- `artifacts/{run_id}/model.pkl` 저장
- 성공·실패 정보를 `logs/runs.jsonl`에 누적
- 제어된 실패 재현과 traceback 기록
- Local Python 및 Docker container 실행
- `configs/train.yaml` 기반 학습 조건 관리
- 설정 항목과 값의 유효성 검사
- 각 run에 설정 경로와 실제 사용값 기록

Agent tool runner, audit log와 timeout은 이후 작업 범위이며 현재 실행 흐름에는 포함되지 않는다.

## 시스템 구성

```text
Local Python 또는 Docker container
               │
               ▼
       configs/train.yaml
          학습 조건 정의
               │
               ▼
     src/config_loader.py
       설정 읽기와 검증
               │
               ▼
       src/run_job.py
       실행 조정과 상태 기록
          │          │
          │          └──────────────┐
          ▼                         ▼
 src/train_job.py             src/storage.py
 데이터·학습·평가          run ID·model 저장
          │                         │
          └──────────┬──────────────┘
                     ▼
              실행 결과 분리
          ┌──────────┴──────────┐
          ▼                     ▼
 logs/runs.jsonl      artifacts/{run_id}/model.pkl
 실행 상태와 원인          학습된 실제 결과물
```

Local과 Docker는 별도의 학습 구현을 사용하지 않는다. 두 실행환경 모두 같은 `src/run_job.py`를 진입점으로 사용한다.

## 구성요소와 책임

| 구성요소 | 책임 | 하지 않는 일 |
|---|---|---|
| `configs/train.yaml` | data 분리와 model 학습에 사용할 조건 정의 | 설정 검증, 실행 결과 기록 |
| `src/config_loader.py` | YAML 읽기, 필수·추가 항목과 자료형·값 범위 검증 | 학습 실행, log 기록 |
| `src/run_job.py` | run ID 생성, 설정 로드, 실행 시간 측정, 학습·저장 조정, 성공·실패 log와 exit code 반환 | 학습 알고리즘 구현, model 직렬화 세부 처리 |
| `src/train_job.py` | 검증된 설정에 따른 Iris data 분리, `LogisticRegression` 학습, accuracy와 sample 수 계산 | 운영 상태와 traceback 기록 |
| `src/storage.py` | 고유 run ID 생성, run별 디렉터리 생성, pickle model 저장 | 학습 실행과 log schema 관리 |
| `logs/runs.jsonl` | 모든 run의 상태, 시각, metric, artifact 경로와 오류 정보 누적 | model 객체 보관 |
| `artifacts/{run_id}/model.pkl` | 실행별 학습 model 보관 | 실행 원인과 상태 설명 |
| `Dockerfile` | Python 3.12, dependency, source, 기본 설정과 실행 명령을 image로 정의 | 실행 결과를 영구 보존 |
| `.dockerignore` | 불필요한 개발 파일, 기존 결과와 secret 가능 파일을 build context에서 제외 | Git ignore 규칙 대체 |

`python src/train_job.py`는 학습과 artifact 저장을 직접 확인하는 하위 수준 진입점이다. 운영 기록까지 필요한 기본 사용 경로는 `python src/run_job.py`다.

## 성공 실행 흐름

```text
1. run ID와 시작 시각 생성
2. 지정된 YAML을 읽고 필수 항목, 자료형과 값 범위 검증
3. 검증된 설정에 따라 Iris data 분리
4. 설정된 최대 반복 횟수로 LogisticRegression 학습과 accuracy 계산
5. artifacts/{run_id}/model.pkl 저장
6. 종료 시각과 duration 계산
7. 설정 경로와 실제 설정값을 포함한 status=success record를 logs/runs.jsonl에 append
8. 같은 record를 stdout에 출력하고 exit code 0 반환
```

Success record는 `config_path`, `config`, `metrics`와 `artifact_path`를 포함하며 `error_type`, `error_message`, `traceback`은 `null`이다.

## 실패 실행 흐름

```text
1. run ID와 시작 시각 생성
2. 설정 읽기·검증, 학습 또는 artifact 저장 중 Exception 발생
3. exception 종류, 메시지와 traceback 수집
4. status=failed record를 logs/runs.jsonl에 append
5. record를 stderr에 출력하고 exit code 1 반환
```

Failed record는 성공과 같은 field를 사용하지만 `metrics`와 `artifact_path`가 `null`이고 오류 field가 채워진다. 설정을 읽지 못했다면 `config`도 `null`이다. `--fail` option은 외부 환경을 손상시키지 않고 이 경로를 반복 검증하기 위해 설정 검증 후 제어된 `RuntimeError`를 발생시킨다.

## Run ID와 데이터 연결

```text
logs/runs.jsonl
└── run_id: 20260810T021535927393Z-24a12c3f
    ├── status, started_at, ended_at, duration_seconds
    ├── config_path와 실제 config
    ├── metrics 또는 error 정보
    └── artifact_path
          ↓
artifacts/20260810T021535927393Z-24a12c3f/model.pkl
```

Run ID는 하나의 실행 record와 그 실행이 만든 model을 연결하는 기준이다. Log는 실행을 설명하고 artifact는 실행 결과물을 보존한다.

## 실행환경 경계

### Local Python

Local virtual environment에 `requirements.txt` dependency를 설치하고 프로젝트 root에서 실행한다.

```bash
python src/run_job.py --config configs/train.yaml
```

### Docker

Docker image는 Python 3.12, dependency, `src/`, `configs/`와 기본 명령을 포함한다. Container는 batch job마다 새로 만들고 `--rm`으로 제거하며, 보존할 `logs/`와 `artifacts/`만 bind mount로 host에 연결한다.

```text
재사용: Docker image
일회성: 학습 container
보존:   host의 logs/와 artifacts/
```

## 현재 제약과 운영 경계

- 실행 경로는 프로젝트 root를 기준으로 한 상대 경로다.
- 학습 설정은 현재 `test_size`, `random_state`, `max_iterations` 세 항목만 지원하며 알 수 없는 항목은 오타 가능성을 막기 위해 거부한다.
- Run log는 설정 파일의 원문이나 hash 대신 검증된 설정값과 지정 경로를 기록한다.
- `logs/runs.jsonl` append는 현재 단일 process 실행을 전제로 하며 동시 쓰기 제어가 없다.
- `running` 중간 상태는 기록하지 않고 실행 종료 후 `success` 또는 `failed` 한 줄만 기록한다.
- Log 파일 쓰기 자체가 실패하면 같은 파일에 그 오류를 기록할 수 없다.
- Artifact 저장 중간에 오류가 나면 일부 run 디렉터리가 남을 수 있다.
- `requirements.txt`는 호환 version 범위이므로 미래 image rebuild의 package 조합까지 완전히 고정하지 않는다.
- Pickle은 신뢰하는 프로젝트 artifact만 사용하며 가능한 한 생성한 실행환경에서 불러온다.
- 현재 log와 artifact는 Git에서 제외되며 별도의 backup·retention 정책은 아직 없다.

이 제약은 현재 학습용 단일 job 범위를 명확히 하기 위한 것이다. 동시성, 장기 보존을 위한 설정 원본 관리, backup과 Agent 실행 통제는 이후 작업에서 단계적으로 추가한다.

## 다음 확장 방향

```text
configs/train.yaml
       ↓
여러 실험 설정과 run 결과 비교
       ↓
이전 run의 재현 절차 강화

configs/tools.yaml
       ↓
allowlist 기반 Agent tool runner
       ↓
timeout과 logs/audit.jsonl
```

## 관련 문서

- [프로젝트 README](../README.md)
- [프로젝트 계획](project-plan.md)
- [일별 작업 흐름](daily-codex-workflow.md)
- [장애 시나리오](failure-scenarios.md)
- [기술 위키](wiki/README.md)
- [작업 일지](work-logs/README.md)
