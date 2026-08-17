# Architecture

## 목적

Mini AI Ops Lab은 작은 머신러닝 학습 작업을 추적 가능한 운영 job으로 발전시키고 Agent의 Tool 요청을 제한하는 프로젝트다. 현재 architecture는 model 정확도 개선보다 설정 검증, 실행 추적, 재현성과 최소 권한의 실행 경계에 집중한다.

## 현재 구현 범위

Day 13까지 핵심 기능을 구현하고 Day 14에 전체 연결과 운영 증거를 검수한 범위는 다음과 같다.

- Iris 분류 model 학습과 accuracy 계산
- 실행별 고유 run ID 생성
- `artifacts/{run_id}/model.pkl` 저장
- 성공·실패 정보를 `logs/runs.jsonl`에 누적
- 제어된 실패 재현과 traceback 기록
- Local Python 및 Docker container 실행
- `configs/train.yaml` 기반 학습 조건 관리
- 설정 항목과 값의 유효성 검사
- 각 run에 설정 경로와 실제 사용값 기록
- `experiment_name`으로 같은 목적의 run grouping
- parameter, metric과 artifact를 한 record에서 비교
- 최근 run 목록과 실험 이름 filter
- 원본과 재현 success run의 조건·결과·artifact 비교
- 같은 Docker image를 사용하는 이전 run 재현 절차
- `configs/tools.yaml`의 네 Tool과 최소 접근 범위 정의
- 공통 Tool allowlist의 구조, 권한 값과 resource 경로 검증
- Local 및 Docker의 Tool 설정 로드
- 허용된 Tool 이름과 입력 형태 검증
- 고정된 Python handler를 통한 네 Tool 실행
- 미등록 Tool과 잘못된 입력의 실행 전 차단
- 성공·실패 Tool 결과의 공통 JSON 구조
- 별도 process 기반 Tool 실행과 제한 시간 초과 종료
- 성공·거부·실패·timeout의 `logs/audit.jsonl` 누적
- 직접 학습과 Agent 학습 요청의 공통 `run_training_job()` 재사용
- run log·audit log·artifact의 schema와 참조 일관성 검수

Agent 또는 role별 권한, audit log rotation과 중단된 쓰기 작업의 자동 rollback은 이후 작업 범위다.

## 시스템 구성

```text
직접 학습 요청                            Agent Tool 요청
      │                                         │
      ▼                                         ▼
configs/train.yaml                       configs/tools.yaml
      │                                         │
      ▼                                         ▼
src/config_loader.py                src/tool_config_loader.py
      │                                         │
      ▼                                         ▼
src/run_job.py ◀──── run_train_job ───── src/tool_runner.py
      │                                 allowlist·입력·timeout
      │                                         │
      ▼                            ┌────────────┴────────────┐
src/train_job.py + src/storage.py  ▼                         ▼
      │                       조회·echo handler       src/audit_logger.py
      │                                                 │
      ├─ logs/runs.jsonl                                ▼
      └─ artifacts/{run_id}/model.pkl            logs/audit.jsonl
      │
      ▼
src/list_runs.py → src/compare_runs.py
```

Local과 Docker는 별도의 구현을 사용하지 않는다. 두 실행환경 모두 학습에는 `src/run_job.py`, Tool 요청에는 `src/tool_runner.py`를 진입점으로 사용한다.

## 구성요소와 책임

| 구성요소 | 책임 | 하지 않는 일 |
|---|---|---|
| `configs/train.yaml` | experiment 이름, data 분리와 model 학습 조건 정의 | 설정 검증, 실행 결과 기록 |
| `src/config_loader.py` | YAML 읽기, 필수·추가 항목과 자료형·값 범위 검증 | 학습 실행, log 기록 |
| `src/run_job.py` | run ID 생성, 설정 로드, 비교 field 구성, 학습·저장 조정, 성공·실패 log와 exit code 반환 | 학습 알고리즘 구현, model 직렬화 세부 처리 |
| `src/list_runs.py` | 최근 run을 최신순으로 조회하고 experiment 이름으로 filter | 학습 실행, log 수정 |
| `src/compare_runs.py` | 두 success run의 experiment, parameter, metric과 artifact 존재 여부 비교 | 학습 실행, record나 model 수정 |
| `configs/tools.yaml` | 허용할 Tool, 입력 형태, 영향 수준과 접근 resource 정의 | 실제 요청 검증, Tool 실행 |
| `src/tool_config_loader.py` | Tool allowlist의 schema, 값과 상대 resource 경로 검증 | Agent 식별, Tool 요청 허용·실행 |
| `src/tool_runner.py` | Tool 이름·입력 검증, 별도 process의 고정 handler 실행·timeout, audit 연결과 구조화된 결과 반환 | shell 명령 실행, timeout rollback |
| `src/audit_logger.py` | Tool 요청 시각, duration, 상태와 오류를 JSONL에 append | Tool 허용 판단, handler 실행 |
| `src/train_job.py` | 검증된 설정에 따른 Iris data 분리, `LogisticRegression` 학습, accuracy와 sample 수 계산 | 운영 상태와 traceback 기록 |
| `src/storage.py` | 고유 run ID 생성, run별 디렉터리 생성, pickle model 저장 | 학습 실행과 log schema 관리 |
| `logs/runs.jsonl` | 모든 run의 상태, 시각, metric, artifact 경로와 오류 정보 누적 | model 객체 보관 |
| `logs/audit.jsonl` | 모든 Tool 요청의 성공·거부·실패·timeout 이력 누적 | 학습 parameter와 model 보관 |
| `artifacts/{run_id}/model.pkl` | 실행별 학습 model 보관 | 실행 원인과 상태 설명 |
| `Dockerfile` | Python 3.12, dependency, source, 기본 설정과 실행 명령을 image로 정의 | 실행 결과를 영구 보존 |
| `.dockerignore` | 불필요한 개발 파일, 기존 결과와 secret 가능 파일을 build context에서 제외 | Git ignore 규칙 대체 |

`python src/train_job.py`는 학습과 artifact 저장만 직접 확인하는 하위 수준 진입점이므로 run log를 만들지 않는다. 운영 기록까지 필요한 기본 사용 경로는 `python src/run_job.py`다.

## 통합 운영 흐름

| 진입점 | 실행 통제 | 학습 결과 | Tool 감사 기록 |
|---|---|---|---|
| `python src/run_job.py` | 학습 config 검증과 exception 처리 | run log와 model 생성 | 없음 |
| 조회·`echo` Tool | allowlist, 입력 검증과 timeout | 조회 또는 문자열 결과 | audit log 생성 |
| `run_train_job` Tool | allowlist, 입력 검증과 timeout 후 `run_training_job()` 호출 | run log와 model 생성 | audit log 생성 |

`run_train_job`은 별도의 학습 구현이 아니라 `src/run_job.py`의 `run_training_job()`을 handler로 호출한다. 따라서 Agent 경로에도 같은 학습 config 검증, model 저장과 run log schema가 적용된다. Tool Runner를 거치지 않는 직접 학습에는 audit record가 없고, 모든 Tool 요청에는 주요 기능의 읽기·쓰기 여부와 별개로 audit record가 추가된다.

## 성공 실행 흐름

```text
1. run ID와 시작 시각 생성
2. 지정된 YAML을 읽고 필수 항목, 자료형과 값 범위 검증
3. 검증된 설정에 따라 Iris data 분리
4. 설정된 최대 반복 횟수로 LogisticRegression 학습과 accuracy 계산
5. artifacts/{run_id}/model.pkl 저장
6. 종료 시각과 duration 계산
7. 실험 이름, parameter, metric과 artifact 경로를 포함한 status=success record를 logs/runs.jsonl에 append
8. 같은 record를 stdout에 출력하고 exit code 0 반환
```

Success record는 `experiment_name`, `parameters`, `config_path`, `config`, `metrics`와 `artifact_path`를 포함하며 `error_type`, `error_message`, `traceback`은 `null`이다.

## 실패 실행 흐름

```text
1. run ID와 시작 시각 생성
2. 설정 읽기·검증, 학습 또는 artifact 저장 중 Exception 발생
3. exception 종류, 메시지와 traceback 수집
4. status=failed record를 logs/runs.jsonl에 append
5. record를 stderr에 출력하고 exit code 1 반환
```

Failed record는 성공과 같은 field를 사용하지만 `metrics`와 `artifact_path`가 `null`이고 오류 field가 채워진다. 설정 검증 후 실패했다면 실험 이름과 parameter는 유지된다. 설정을 읽지 못했다면 `config`, `experiment_name`, `parameters`도 `null`이다. `--fail` option은 외부 환경을 손상시키지 않고 이 경로를 반복 검증하기 위해 설정 검증 후 제어된 `RuntimeError`를 발생시킨다.

## Run ID와 데이터 연결

```text
logs/runs.jsonl
└── experiment_name: iris-baseline
    ├── run_id: 20260812T003313853388Z-076af5dc
    │   ├── parameters와 metrics
    │   └── artifacts/{run_id}/model.pkl
    └── run_id: 20260812T004148291974Z-e2bef42e
        ├── parameters와 metrics
        └── artifacts/{run_id}/model.pkl
```

Experiment name은 같은 목적의 여러 실행을 묶고, run ID는 하나의 실행 record와 그 실행이 만든 model을 연결한다. Log는 실행 조건과 결과를 설명하고 artifact는 학습된 model을 보존한다.

## 최근 run 조회 흐름

```text
logs/runs.jsonl
       ↓ 한 줄씩 읽기
experiment_name filter
       ↓ 조건에 맞는 최근 N개만 유지
최신순 비교 표 출력
```

`src/list_runs.py`는 원본 JSONL을 수정하지 않는다. Day 9 field가 없는 과거 record는 없는 값을 `-`로 표시하고, 기존 `config`에 parameter가 있으면 비교 열을 보완한다. 손상된 JSON line은 경고 후 건너뛰어 나머지 운영 기록을 계속 조회한다.

## 이전 run 재현 흐름

```text
원본 success run
  ├── 기록된 config, parameters, metrics
  └── 기존 model artifact
              ↓
같은 Docker image와 설정으로 학습
              ↓
새 run ID와 새 model artifact
              ↓
src/compare_runs.py
  ├── 같아야 함: experiment, parameters, metrics
  ├── 존재해야 함: 원본·재현 artifact
  └── 달라야 함: run ID와 artifact 경로
```

`compare_runs.py`는 두 success record와 artifact 경로를 읽기만 한다. 모든 현재 기준을 만족하면 `reproduced: true`와 exit code `0`, 값 불일치나 artifact 누락은 exit code `1`을 반환한다. Failed run이나 존재하지 않는 run은 결과를 비교할 수 없으므로 명확한 오류로 거부한다.

이번 재현은 원본 `20260812T004148291974Z-e2bef42e`와 같은 `mini-ai-ops-lab:day9` image 및 설정으로 새 run `20260813T050336148461Z-c104baf9`를 생성해 검증했다. Parameter와 metric은 같았으며 두 model은 서로 다른 run별 경로에 보존됐다.

## Agent Tool Allowlist 경계

```text
Agent: 필요한 Tool을 판단하고 이름으로 요청
                 ↓
Tool Runner: tools.yaml 등록 여부와 입력 확인
                 ↓
별도 process: 고정 handler 실행과 timeout 대기
                 ↓
성공 결과 반환 또는 process 종료
                 ↓
audit_logger: duration과 success/failed/timeout 기록
```

Day 11의 `configs/tools.yaml`은 `echo`, `list_artifacts`, `read_log_summary`, `run_train_job` 네 이름만 실행 후보로 정의한다. `none`, `read`, `write`는 Tool이 미칠 수 있는 가장 높은 영향 수준을 나타내며 `resources`는 의도한 접근 범위를 설명한다.

`tool_config_loader.py`는 필수·추가 field, Tool 이름, 입력 형태, 접근 수준과 resource가 project 내부 상대 경로인지 검증한다. `tool_runner.py`는 검증된 목록에 없는 이름을 기본 거부하고 요청 입력을 확인한 뒤 `TOOL_HANDLERS`에 미리 연결된 Python 함수만 호출한다. 따라서 설정에 이름만 추가하거나 shell 명령 같은 문자열을 전달해도 임의 기능은 실행되지 않는다.

현재 handler의 동작은 다음과 같다.

| Tool | Handler 동작 | Project 상태 변경 |
|---|---|---|
| `echo` | 입력 문자열 반환 | audit log 추가 |
| `list_artifacts` | `artifacts/*/model.pkl` 목록 조회 | audit log 추가 |
| `read_log_summary` | 최근 run 5개의 상태와 결과 요약 | audit log 추가 |
| `run_train_job` | 기본 설정으로 `run_training_job()` 호출 | audit log, run log와 model 생성 |

성공, 실패와 timeout은 공통으로 `tool_name`, `status`, `result`, `error_type`, `error_message`를 반환한다. `run_train_job`의 `result.training_status`는 Tool handler 실행 결과와 내부 학습 결과를 구분한다.

`tool_runner.py`는 Linux/WSL의 `fork` context로 handler process를 만들고 pipe를 통해 결과를 받는다. `--timeout` 안에 결과가 없으면 먼저 `terminate()`, 필요하면 `kill()`로 process를 정리한다. 요청 전체의 시작·종료 UTC 시각과 단조 시계 기반 duration은 `audit_logger.py`가 JSONL record로 만든다. 원문 입력 대신 `input_provided`만 기록한다.

현재는 Agent identity가 없는 단일 실행환경이므로 모든 요청이 같은 공통 allowlist를 사용한다. 여러 Agent의 역할이 실제로 나뉘면 Agent 또는 role별 최소 권한 목록으로 확장할 수 있다.

## Day 14 로그 일관성 검수

Day 14 시작 시점의 실제 운영 증거를 읽기 전용으로 검사했다.

| 검수 대상 | 결과 |
|---|---|
| `logs/runs.jsonl` | 17건 모두 JSON 파싱 성공, success 12건·failed 5건 |
| Success run → artifact | 12건 모두 실제 model 파일 존재 |
| `logs/audit.jsonl` | 10건 모두 동일 field, success 6건·failed 2건·timeout 2건 |
| 시각과 duration | 종료 시각이 시작보다 빠르거나 duration이 음수인 record 없음 |
| 현재 run schema | `experiment_name`이 있는 6건 모두 field와 상태 규칙 일치 |

Run log는 기존 record를 수정하지 않고 기능이 추가된 시점의 schema를 보존해 네 세대가 함께 존재한다.

| Schema 세대 | Record 수 | 추가된 주요 정보 |
|---|---:|---|
| 초기 run | 2 | 상태, 시각, duration, metric, artifact |
| 실패 추적 | 6 | 오류 종류, 메시지와 traceback |
| Config 추적 | 3 | config 경로와 실제 값 |
| Experiment 추적 | 6 | experiment 이름과 비교용 parameters |

초기 record에 최신 field가 없는 것은 손상이 아니라 schema evolution의 결과다. `list_runs.py`가 없는 값을 호환 표시하고 원본은 그대로 보존한다.

실제 model 16개 중 4개는 run log가 참조하지 않는다. 세 개는 run log 도입 전 생성됐고 나머지 한 개는 기록상 하위 수준 실행 결과로 추정된다. 반대로 success run이 가리키는 artifact 누락은 없었다. 참조가 없는 artifact도 생성 배경을 확인하기 전에는 자동 삭제하지 않는다.

Audit log는 Day 13 이후 Tool 요청만 포함한다. 현재 audit schema에는 `run_id`나 공통 `request_id`가 없어 성공한 `run_train_job` audit record와 내부 run record를 key로 직접 연결하지 못하며, 요청 시각으로만 관련 실행을 추정한다.

## 실행환경 경계

### Local Python

Local virtual environment에 `requirements.txt` dependency를 설치하고 프로젝트 root에서 실행한다.

```bash
python src/run_job.py --config configs/train.yaml
python src/list_runs.py --experiment iris-baseline --limit 3
python src/compare_runs.py --source-run 20260812T004148291974Z-e2bef42e --candidate-run 20260813T050336148461Z-c104baf9
python src/tool_config_loader.py --config configs/tools.yaml
python src/tool_runner.py --tool echo --input "hello" --timeout 1
python src/tool_runner.py --tool list_artifacts --timeout 1
python src/tool_runner.py --tool read_log_summary --timeout 1
python src/tool_runner.py --tool run_train_job --timeout 30
tail -n 5 logs/audit.jsonl
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
- 학습 설정은 현재 `experiment_name`, `test_size`, `random_state`, `max_iterations` 네 항목만 지원하며 알 수 없는 항목은 오타 가능성을 막기 위해 거부한다.
- Experiment name은 grouping label이며 같은 이름의 여러 run을 허용한다. 이름 자체가 개별 model version은 아니다.
- Day 9 이전 log에는 `experiment_name`과 `parameters`가 없을 수 있으며 조회 시 호환 표시만 제공하고 원본 record를 변경하지 않는다.
- Run log는 설정 파일의 원문이나 hash 대신 검증된 설정값과 지정 경로를 기록한다.
- Run record는 Git commit, Docker image digest와 data version을 기록하지 않아 config만으로 장기적인 완전 재현을 보장하지 못한다.
- Docker tag는 같은 이름으로 다시 build할 수 있으므로 불변 image 식별자가 아니다.
- 현재 재현 비교는 metric의 정확한 일치와 artifact 존재 여부를 확인하며 model byte나 전체 예측 결과는 비교하지 않는다.
- `logs/runs.jsonl` append는 현재 단일 process 실행을 전제로 하며 동시 쓰기 제어가 없다.
- `running` 중간 상태는 기록하지 않고 실행 종료 후 `success` 또는 `failed` 한 줄만 기록한다.
- Log 파일 쓰기 자체가 실패하면 같은 파일에 그 오류를 기록할 수 없다.
- Artifact 저장 중간에 오류가 나면 일부 run 디렉터리가 남을 수 있다.
- `requirements.txt`는 호환 version 범위이므로 미래 image rebuild의 package 조합까지 완전히 고정하지 않는다.
- Pickle은 신뢰하는 프로젝트 artifact만 사용하며 가능한 한 생성한 실행환경에서 불러온다.
- 현재 log와 artifact는 Git에서 제외되며 별도의 backup·retention 정책은 아직 없다.
- Tool allowlist는 현재 모든 요청에 공통이며 Agent별 role과 identity를 구분하지 않는다.
- Tool runner는 allowlist, 입력과 고정 handler 연결을 강제하지만 `access`와 `resources`를 OS 파일 권한으로 직접 적용하지는 않는다.
- Timeout은 child process를 종료하지만 이미 생성된 log, artifact나 외부 상태를 자동으로 rollback하지 않는다.
- 별도 process 실행은 현재 WSL/Linux와 Docker의 `fork` 실행환경을 기준으로 한다.
- Audit log는 원문 입력과 handler 결과 전체를 저장하지 않으며, 별도 rotation이나 동시 쓰기 제어가 없다.
- Tool 기능이 완료된 뒤 audit log 쓰기가 실패하면 기능의 상태 변경은 이미 발생했을 수 있다.
- Run log에는 네 schema 세대가 공존하며 과거 record를 현재 schema로 migration하지 않았다.
- 일부 초기·하위 수준 artifact는 연결된 run log가 없다.
- Audit record에는 내부 학습의 `run_id`가 없어 Agent 요청과 run을 공통 ID로 직접 연결하지 못한다.

이 제약은 현재 학습용 단일 job 범위를 명확히 하기 위한 것이다. 동시성, 장기 보존을 위한 설정 원본 관리, backup, 공통 request ID와 Agent별 실행 통제는 이후 작업에서 단계적으로 추가한다.

## 다음 확장 방향

```text
configs/train.yaml
       ↓
experiment 이름과 run 결과 비교
       ↓
이전 run의 재현 명령과 runbook
       ↓
code·image·data version 추적 강화

configs/tools.yaml
       ↓
allowlist 기반 Agent tool runner
       ↓
timeout과 logs/audit.jsonl
       ↓
통합 architecture와 log 일관성 검수
       ↓
운영 문서, 보안과 backup 점검
```

## 관련 문서

- [프로젝트 README](../README.md)
- [프로젝트 계획](project-plan.md)
- [일별 작업 흐름](daily-codex-workflow.md)
- [장애 시나리오](failure-scenarios.md)
- [Runbook](runbook.md)
- [기술 위키](wiki/README.md)
- [작업 일지](work-logs/README.md)
