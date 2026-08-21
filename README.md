# Mini AI Ops Lab

## 개요

Mini AI Ops Lab은 **머신러닝 학습 작업과 Agent Tool 요청을 작지만 운영 가능한 형태로 관리하는 학습용 시스템**이다.

이 프로젝트의 중심은 모델 정확도 향상이 아니다. 다음 질문에 실행 결과와 문서로 답할 수 있는 운영 흐름을 만드는 것이 목적이다.

- 어떤 설정으로 학습했는가?
- 실행이 성공하거나 실패한 이유는 무엇인가?
- 어떤 run이 어느 model artifact를 만들었는가?
- 이전 실행을 같은 조건으로 다시 수행하고 비교할 수 있는가?
- Agent가 요청한 Tool은 허용됐으며 제한 시간 안에 끝났는가?
- 장애가 발생하면 어떤 log를 확인하고 어떻게 복구하는가?

이를 위해 config 검증, run별 model 저장, JSONL run·audit log, 실험 비교, Tool allowlist와 timeout, 장애 대응, backup·restore 절차를 하나의 저장소에 연결했다.

## 아키텍처

시스템에는 운영자가 사용하는 **직접 학습 경로**와 Agent가 사용하는 **통제된 Tool 경로**가 있다. `run_train_job` handler는 Tool 요청을 기존 학습 경로에 연결하므로 학습 구현을 중복하지 않는다.

```text
직접 학습
configs/train.yaml
        │
        ▼
config 검증 ──▶ run_job.py ──▶ train_job.py + storage.py
                       │
                       ├─▶ logs/runs.jsonl
                       └─▶ artifacts/{run_id}/model.pkl

Agent Tool 요청
configs/tools.yaml
        │
        ▼
Tool 정책 검증 ──▶ tool_runner.py ──▶ 고정 Python handler
                         │                    │
                         │                    └─▶ run_train_job ──▶ run_job.py
                         └─▶ logs/audit.jsonl
```

### 구성요소 책임

| 구성요소 | 책임 |
|---|---|
| `configs/train.yaml` | 학습의 experiment 이름과 parameter 정의 |
| `src/config_loader.py` | 학습 전에 YAML 구조, 자료형과 값 범위 검증 |
| `src/run_job.py` | 학습 실행을 조정하고 success·failed run record 저장 |
| `src/train_job.py`, `src/storage.py` | Model 학습, metric 계산과 run별 artifact 저장 |
| `configs/tools.yaml` | Agent가 요청할 수 있는 Tool과 접근 수준 정의 |
| `src/tool_runner.py` | Allowlist, 입력, handler와 timeout을 확인한 뒤 Tool 실행 |
| `src/audit_logger.py` | Tool 요청의 success·failed·timeout audit record 저장 |

| 실행 경로 | 목적 | 생성하거나 변경하는 운영 증거 |
|---|---|---|
| `python src/run_job.py` | 학습을 직접 실행 | run log와 model artifact |
| 조회·`echo` Tool | Agent가 상태 조회 또는 응답 기능 사용 | audit log |
| `run_train_job` Tool | Agent 요청으로 학습 실행 | audit log, run log와 model artifact |

현재 audit record에는 내부 학습의 `run_id`가 없어 Tool 요청과 run record를 공통 ID로 직접 연결하지 못한다. 두 record의 요청 시각과 결과를 함께 확인하는 것이 현재 운영 경계다. 상세 sequence와 제약은 [Architecture](docs/architecture.md)에서 확인할 수 있다.

## 주요 기능

### 학습과 실험 관리

- YAML config 검증을 통과한 명령줄 기반 학습
- UTC 시각과 UUID suffix를 조합한 고유 run ID
- `artifacts/{run_id}/model.pkl` 형태의 실행별 model 저장
- Experiment 이름, parameter, metric과 artifact 경로를 연결한 JSONL record
- 최근 run 조회, experiment filter와 두 run의 재현 기준 비교

### 실패와 운영 기록

- Success와 failed run의 공통 schema
- 오류 종류, 메시지와 traceback 기록
- 제어된 실패 재현과 정상 실행 복구 절차
- 장애 시나리오, Runbook과 보안·백업 체크리스트

### Agent Tool 통제

- `echo`, `list_artifacts`, `read_log_summary`, `run_train_job` Allowlist
- Tool 입력 형태와 고정 Python handler 검증
- 미등록 요청의 실행 전 거부
- 별도 process 실행과 Tool별 timeout
- Success·failed·timeout audit log

### 실행환경과 프로젝트 기록

- 같은 Python code를 사용하는 Local·Docker 실행
- Git에서 제외된 log·artifact의 수동 backup·restore 검증
- 프로젝트 내부 기술 위키와 날짜별 작업 기록

현재 범위에는 자동 backup schedule, 외부 backup 저장소, Agent별 권한, Git·image·data version을 포함한 완전한 재현과 대규모 orchestration은 포함하지 않는다.

## 빠른 시작

모든 명령은 WSL의 project root에서 실행한다. Local Python이 가장 빠른 확인 경로이며 Docker는 dependency를 image 안에 묶어 실행할 때 사용한다.

```bash
cd /home/hskim/project/mini-ai-ops-lab
```

### Local Python

처음 한 번만 가상환경을 만들고 dependency를 설치한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

이 명령들은 `.venv/`와 그 안의 Python package를 생성한다. 이미 준비된 가상환경이 있다면 `source .venv/bin/activate`만 실행한다.

학습 설정을 읽고 유효성을 먼저 확인한다.

```bash
python -c "from src.config_loader import load_train_config; print(load_train_config('configs/train.yaml'))"
```

이 명령은 config를 읽기만 한다. 검증된 `experiment_name`, `test_size`, `random_state`, `max_iterations`가 출력되면 학습을 실행할 수 있다.

```bash
python src/run_job.py --config configs/train.yaml
python src/list_runs.py --limit 1
```

첫 명령은 새 학습을 실행해 `logs/runs.jsonl`에 record 한 줄을 추가하고, 성공하면 `artifacts/{run_id}/model.pkl`을 생성한다. 두 번째 명령은 log를 변경하지 않고 방금 실행한 run을 조회한다. 두 출력에 같은 `run_id`와 `status: success`가 있고 실제 artifact 경로가 존재하면 정상이다.

### Docker

Docker daemon을 사용할 수 있다면 project code와 dependency를 image로 만든다.

```bash
docker build -t mini-ai-ops-lab:day13 .
docker run --rm mini-ai-ops-lab:day13
```

`docker build`는 local image와 build cache를 생성하거나 갱신한다. `docker run --rm`은 container 안에서 기본 학습을 실행한 뒤 종료된 container를 제거한다. Bind mount가 없으므로 이 smoke test의 log와 model은 host project에 남지 않는다.

Docker 실행 결과를 host에 보존하는 bind mount 명령, 실패 재현과 read-only 조회 방법은 [Runbook](docs/runbook.md)의 기본 실행 절차를 따른다.

> `.env`, 실제 log와 model artifact는 Git에 commit하지 않는다. 환경변수 형식은 `.env.example`, 자세한 제외·복구 기준은 [보안·백업 체크리스트](docs/security-backup-checklist.md)에서 확인한다.

## 학습과 실험 추적

기본 작업은 `configs/train.yaml`에 따라 scikit-learn의 Iris dataset과 `LogisticRegression`을 사용한다. Model 성능 자체보다 config, metric, log와 artifact가 한 run ID로 연결되는 과정을 확인하는 것이 목적이다.

`src/train_job.py`는 학습과 artifact 저장을 담당하는 하위 기능이고, 운영 실행점인 `src/run_job.py`는 성공·실패 결과까지 `logs/runs.jsonl`에 남긴다. 일반 실행에는 `run_job.py`를 사용한다.

### Model Artifact

각 학습 실행은 UTC 생성 시각과 UUID suffix를 조합한 run ID를 사용한다. 학습된 model은 다른 실행 결과를 덮어쓰지 않도록 다음 경로에 저장한다.

```text
artifacts/{run_id}/model.pkl
```

저장된 model 파일은 다음 명령으로 확인한다.

```bash
find artifacts -maxdepth 2 -type f -name 'model.pkl' -printf '%p %s bytes\n' | sort
```

이 명령은 파일을 변경하지 않고 artifact 경로와 크기를 출력한다. `artifacts/`의 실행 결과는 `.gitignore`에 따라 Git에서 제외된다. `model.pkl`은 Python pickle 형식이므로 신뢰할 수 없는 외부 파일을 불러오지 않는다.

### Config와 Run 조회

학습 조건은 다음처럼 `configs/train.yaml`에서 관리한다.

```yaml
experiment_name: iris-baseline
test_size: 0.2
random_state: 42
max_iterations: 200
```

- `experiment_name`: 같은 목적의 여러 run을 묶는 이름이며 비어 있지 않은 100자 이하 문자열이어야 한다.
- `test_size`: 전체 data 중 검증에 사용할 비율이며 `0`보다 크고 `1`보다 작아야 한다.
- `random_state`: 같은 방식으로 data를 나누기 위한 난수값이며 허용 범위의 정수여야 한다.
- `max_iterations`: model 학습의 최대 반복 횟수이며 양의 정수여야 한다.

`experiment_name`은 같은 목적의 실행을 묶고, `run_id`는 그 안의 개별 실행 한 번을 구분한다. `src/config_loader.py`는 학습 전에 필수 항목, 추가 항목, 자료형과 값의 범위를 검사한다. 조건이 잘못되었거나 파일이 없으면 학습을 시작하지 않고 failed record를 남긴다.

`logs/runs.jsonl`에는 설정 전체와 함께 비교용 `experiment_name`, `parameters`, `metrics`, `artifact_path`를 기록한다. 따라서 같은 실험의 parameter와 결과를 비교하고 어느 run이 어떤 model을 만들었는지 찾을 수 있다.

다음은 2026-08-21에 검증한 success record의 주요 field를 보기 좋게 펼친 예시다. 실제 JSONL에서는 한 record가 한 줄에 저장된다.

```json
{
  "run_id": "20260821T024802876493Z-dbffecf6",
  "experiment_name": "iris-baseline",
  "status": "success",
  "parameters": {
    "test_size": 0.2,
    "random_state": 42,
    "max_iterations": 200
  },
  "metrics": {
    "accuracy": 0.9666666666666667,
    "train_samples": 120,
    "test_samples": 30
  },
  "artifact_path": "artifacts/20260821T024802876493Z-dbffecf6/model.pkl",
  "error_type": null
}
```

```bash
python src/list_runs.py --limit 5
python src/list_runs.py --experiment iris-baseline --limit 3
```

두 명령은 run log를 읽기만 한다. 첫 번째는 전체 최근 run을, 두 번째는 `iris-baseline`의 최근 run만 최신순으로 출력한다. Day 9 이전 record에 새 field가 없으면 `-`로 표시하고, 기존 `config`에 parameter가 있으면 비교 열을 보완한다.

### 이전 Run 재현

재현은 기존 run을 수정하는 작업이 아니다. 성공한 원본 run의 설정과 실행환경을 확인하고 같은 조건으로 새 run을 만든 뒤 결과를 비교한다.

```text
원본 success run 선택
        ↓
기록된 config와 artifact 확인
        ↓
같은 Docker image와 설정으로 새 run 생성
        ↓
experiment, parameters, metrics와 artifact 비교
```

Day 10에서는 다음 명령으로 원본과 재현 run을 비교했다.

```bash
python src/compare_runs.py \
  --source-run 20260812T004148291974Z-e2bef42e \
  --candidate-run 20260813T050336148461Z-c104baf9
```

이 명령은 log와 artifact 경로를 읽기만 한다. Experiment 이름, parameter와 metric이 같고 두 model이 존재하며, run ID와 artifact 경로가 서로 다르면 `reproduced: true`와 exit code `0`을 반환한다.

같은 config만으로 일반적인 머신러닝의 완전한 재현이 보장되지는 않는다. 현재 run record에는 Git commit, Docker image digest와 data version이 없으며 model byte나 모든 예측 결과도 비교하지 않는다. 실제 선택·재실행·비교 절차와 실패 항목별 대응은 [Runbook](docs/runbook.md)에서 확인한다.

## Agent Tool Runner

Agent는 무엇을 할지 판단하고 Tool 사용을 요청하는 주체이며, Tool은 실제 기능이다. `configs/tools.yaml`은 현재 단일 Agent 실행환경에 공통으로 적용할 다음 allowlist를 정의한다.

| Tool | 입력 | 접근 수준 | 허용 resource |
|---|---|---|---|
| `echo` | text | `none` | 없음 |
| `list_artifacts` | 없음 | `read` | `artifacts/` |
| `read_log_summary` | 없음 | `read` | `logs/runs.jsonl` |
| `run_train_job` | 없음 | `write` | `logs/runs.jsonl`, `artifacts/` |

다음 명령은 allowlist의 구조, 입력 형태, 접근 수준과 project 내부 상대 resource를 검증한다.

```bash
python src/tool_config_loader.py --config configs/tools.yaml
```

이 명령은 설정을 읽기만 하며 Tool을 실행하지 않는다. `access`는 각 Tool이 미칠 수 있는 영향의 분류이며, 설정 파일만으로 OS 파일 권한이 적용되지는 않는다.

`src/tool_runner.py`는 요청 이름이 allowlist에 있는지, 입력이 `input_type`과 일치하는지, 해당 이름에 미리 구현된 Python handler가 있는지를 차례로 확인한다. Tool 이름을 shell 명령으로 실행하지 않으므로 YAML에 이름만 추가해도 임의 기능이 실행되지 않는다. 현재는 Agent identity나 role을 구분하지 않으므로 모든 요청에 같은 allowlist가 적용된다.

허용된 Tool은 project root에서 다음과 같이 실행한다.

```bash
python src/tool_runner.py --tool echo --input "hello" --timeout 1
python src/tool_runner.py --tool list_artifacts --timeout 1
python src/tool_runner.py --tool read_log_summary --timeout 1
python src/tool_runner.py --tool run_train_job --timeout 30
```

- `echo`는 입력 문자열을 그대로 반환한다.
- `list_artifacts`는 저장된 model 경로와 run ID를 조회한다.
- `read_log_summary`는 최근 학습 run 5개의 상태와 핵심 결과를 조회한다.
- `run_train_job`은 새 학습을 실행해 `logs/runs.jsonl` 한 줄과 model artifact를 생성한다.

모든 명령은 Tool의 주요 기능과 별개로 `logs/audit.jsonl`에 요청 이력 한 줄을 추가한다. 기본 제한 시간은 30초이며 `--timeout`으로 0 이상의 유한한 초 단위 값을 지정할 수 있다.

모든 요청은 `tool_name`, `status`, `result`, `error_type`, `error_message`를 가진 JSON으로 반환된다. 예를 들어 `echo`의 success 결과는 다음과 같다.

```json
{
  "tool_name": "echo",
  "status": "success",
  "result": "readme-check",
  "error_type": null,
  "error_message": null
}
```

허용되지 않은 이름은 기능을 실행하지 않고 exit code `1`로 거부한다.

```bash
python src/tool_runner.py --tool unknown
```

Runner는 handler를 별도 process에서 실행한다. 제한 시간 안에 결과가 없으면 해당 process를 종료하고 `status: timeout`, `ToolTimeoutError`와 exit code `1`을 반환한다. Timeout은 이미 생성된 파일을 되돌리지 않으므로 쓰기 Tool이 중단됐다면 log와 artifact에 일부 결과가 남았는지도 확인해야 한다. Docker Tool 실행과 장애 복구 명령은 [Runbook](docs/runbook.md)에서 확인한다.

## 로그와 감사 기록

실행 중 생성되는 운영 기록은 JSON Lines(JSONL) 형식을 사용한다.

- `logs/runs.jsonl`: 학습 실행 기록
- `logs/audit.jsonl`: 모든 Agent Tool 요청의 감사 기록

최근 Tool 요청은 다음 명령으로 확인한다.

```bash
tail -n 5 logs/audit.jsonl
```

이 명령은 audit log를 읽기만 한다. 각 record에는 `tool_name`, `status`, 시작·종료 시각, `duration_seconds`, 입력 제공 여부, `timeout_seconds`와 오류 field가 있다. 원문 입력은 민감정보 기록을 줄이기 위해 저장하지 않는다. `success`는 정상 완료, `failed`는 거부나 실행 오류, `timeout`은 제한 시간 초과를 의미한다.

다음은 앞의 `echo` 요청으로 생성된 audit record다. Handler 결과와 입력 원문 대신 입력 제공 여부만 기록한다.

```json
{
  "tool_name": "echo",
  "status": "success",
  "started_at": "2026-08-21T02:49:49.474558+00:00",
  "duration_seconds": 0.010489,
  "input_provided": true,
  "timeout_seconds": 1.0,
  "error_type": null,
  "error_message": null
}
```

Run record는 성공과 실패에 공통 field를 사용한다. Success에는 metric과 artifact 경로가 채워지고 error field는 `null`이며, failed record에는 오류 종류, 메시지와 traceback이 채워진다. 제어된 실패 실행과 복구 방법은 [장애 시나리오](docs/failure-scenarios.md)를 따른다.

최근 실행 기록은 다음 명령으로 확인한다.

```bash
python src/list_runs.py --limit 3
```

이 명령은 로그를 변경하지 않고 최근 세 run의 실험 이름, 상태, accuracy, parameter, run ID와 artifact 경로를 비교 가능한 열로 출력한다. 원본 JSON을 확인해야 할 때는 `tail -n 3 logs/runs.jsonl`을 사용한다. JSONL은 한 실행을 독립된 JSON 한 줄로 저장하므로 기존 전체 내용을 다시 쓰지 않고 새 기록을 추가할 수 있다.

프로젝트가 단계적으로 발전해 과거 run에는 현재 field 일부가 없을 수 있다. `list_runs.py`는 없는 값을 `-`로 표시하거나 기존 config에서 비교값을 보완하지만 원본 record는 수정하지 않는다. Run log 도입 전이나 하위 수준 실행으로 만들어져 연결 record가 없는 artifact도 있으므로 참조가 없다는 이유만으로 자동 삭제하지 않는다.

생성된 로그 파일은 Git에서 제외한다. 빈 디렉터리는 `.gitkeep` placeholder를 사용해 저장소에 유지한다.

## 장애 대응

[장애 시나리오](docs/failure-scenarios.md)는 다음 다섯 경우를 증상, 확인할 log, 원인, 복구와 예방 순서로 설명한다.

- 학습 작업 실패
- Model artifact 저장 실패
- Agent Tool timeout
- Config load 실패
- 허용되지 않은 Tool 요청

운영 중에는 먼저 최근 run·audit record와 artifact 상태를 읽고, 기존 증거를 수정하거나 삭제하지 않은 채 원인을 해결한다. 그다음 새 success 실행과 예상 결과물로 복구 완료를 판단한다. 환경 준비부터 실행, 재현, 장애 복구와 안전한 정리까지의 명령 순서는 [Runbook](docs/runbook.md)을 따른다.

과도한 log 증가에 대한 자동 rotation은 아직 구현하지 않았다. 현재 보존·정리 기준은 보안·백업 체크리스트에 정의되어 있다.

## 보안과 백업

- 실제 Secret은 source, config, 문서와 Git history에 기록하지 않는다.
- `.env.example`에는 공유 가능한 변수 형식과 비밀이 아닌 값만 둔다.
- 실제 log와 model은 Git·Docker build context에서 제외한다.
- Tool은 Allowlist와 고정 handler로 제한하고 audit log에는 입력 원문을 저장하지 않는다.
- 출처를 신뢰할 수 없는 pickle model은 load하지 않는다.
- Source와 문서는 Git, config·log·artifact는 별도 archive, Secret은 보호된 저장소에서 복구한다.

현재 RPO 24시간과 RTO 2시간은 고객 SLA가 아니라 backup·restore 연습을 위한 내부 기준이다. `configs/`, `logs/`, `artifacts/`의 수동 archive 생성, 별도 경로 restore와 원본 비교를 검증했다. 자동 schedule과 외부 backup 저장소는 아직 구현하지 않았다.

자세한 제외 정책, 접근 권한, 보존 기간, 복구와 Secret 노출 대응은 [보안·백업 체크리스트](docs/security-backup-checklist.md)에서 확인한다.

## 문서 안내

README는 프로젝트 소개와 첫 실행 경로를 제공하고, 상세 운영·학습 내용은 목적별 문서로 분리한다.

| 문서 | 용도 |
|---|---|
| [Architecture](docs/architecture.md) | 구성요소 책임, 실행 sequence와 현재 제약 |
| [Runbook](docs/runbook.md) | 환경 준비, 실행, 조회, 재현, 복구와 안전한 정리 |
| [장애 시나리오](docs/failure-scenarios.md) | 장애별 증상, 확인 근거, 원인과 복구 |
| [보안·백업 체크리스트](docs/security-backup-checklist.md) | Secret, 권한, 보존, backup·restore와 사고 대응 |
| [기술 위키](docs/wiki/README.md) | 구현 과정에서 사용한 기술 개념과 Q&A |
| [작업 일지](docs/work-logs/README.md) | 날짜별 작업, 명령, 검증과 학습 기록 |
| [프로젝트 계획](docs/project-plan.md) | 범위, 결과물과 전체 구현 방향 |
| [일별 작업 흐름](docs/daily-codex-workflow.md) | Day별 목표와 단계별 검수 방식 |
