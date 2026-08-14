# Mini AI Ops Lab

## 프로젝트 소개

Mini AI Ops Lab은 AI 작업을 운영하는 방법을 배우기 위한 작고 이해하기 쉬운 시스템이다. 현재는 학습 작업과 실험 결과를 추적하고 Agent용 Tool allowlist를 정의·검증한다. 이후 실제 도구 호출을 allowlist, timeout과 audit log로 통제하는 기능까지 확장한다.

이 프로젝트는 모델 정확도보다 추적과 복구 가능성을 중요하게 생각한다. 어떤 설정으로 실행했는지, 성공했는지, 어떤 metric과 artifact가 생성됐는지를 나중에도 확인할 수 있어야 한다.

## 아키텍처

현재 구현된 학습 운영 흐름은 다음과 같다.

```text
Local Python 또는 Docker container
               ↓
       configs/train.yaml
               ↓
      src/config_loader.py
               ↓
          src/run_job.py
          ↙             ↘
src/train_job.py     src/storage.py
          ↘             ↙
        logs/runs.jsonl
        artifacts/{run_id}/model.pkl
               ↓
        src/list_runs.py
       최근 실험 결과 비교
               ↓
       src/compare_runs.py
       원본·재현 run 비교

Agent의 향후 Tool 요청
               ↓
       configs/tools.yaml
               ↓
  src/tool_config_loader.py
       검증된 공통 allowlist
               ↓
  src/tool_runner.py (Day 12)
```

`src/run_job.py`가 학습과 저장을 조정하고 성공·실패 record를 남긴다. 상세한 구성요소 책임과 실행 sequence는 [Architecture](docs/architecture.md)에서 확인할 수 있다.

## 주요 기능

현재 구현하고 검증한 기능은 다음과 같다.

- 명령줄 기반 학습 작업 실행
- UTC 시각과 UUID suffix를 조합한 run ID
- 실행별 모델 artifact 저장
- 성공 및 실패 structured log
- YAML 설정 검증과 설정 기반 학습
- 실행 log의 설정 경로와 실제 사용값 기록
- 실험 이름별 run grouping과 parameter·metric 비교
- 최근 run 목록 및 실험 이름 filter
- 이전 run의 재실행 및 재현 결과 비교
- 재현 절차를 설명하는 운영 runbook
- 오류 종류, 메시지와 traceback 기록
- Local Python 및 Docker container 실행
- 제어된 학습 실패와 복구 확인 절차
- Agent용 공통 Tool allowlist와 최소 접근 범위 정의
- Local 및 Docker의 Tool 설정 검증
- 프로젝트 내부 기술 위키와 날짜별 작업 기록

다음 기능은 향후 작업 범위다.

- allowlist 기반 Agent 도구 요청 허용·거부와 실행
- 도구 timeout 및 audit log
- runbook 확장과 보안·백업 체크리스트
- 추가 장애 시나리오와 log retention

## 시작 방법

프로젝트는 local Python 환경이나 Docker container에서 실행할 수 있다. 두 방식 모두 같은 `src/run_job.py`를 사용한다.

### Local Python 실행환경

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/run_job.py --config configs/train.yaml
```

`.env`, 실행 중 생성된 로그, 모델 artifact는 Git에 커밋하지 않는다. 안전한 설정 예시는 `.env.example`을 사용한다.

### Docker 실행환경

Docker image는 기존 Python 코드를 Docker 전용으로 다시 작성하는 것이 아니라, 실행에 필요한 Linux 기반 환경, Python 3.12, dependency, `src/` 코드, `configs/` 설정과 기본 명령을 함께 묶는다.

프로젝트 root에서 image를 build한다.

```bash
docker build -t mini-ai-ops-lab:day11 .
```

이 명령은 base image와 dependency를 내려받아 local Docker image와 build cache를 만든다. `Dockerfile`, `requirements.txt`, `src/`, `configs/`를 변경했다면 새 내용을 반영하기 위해 다시 build한다.

동작만 확인하고 실행 결과를 버리려면 다음처럼 실행한다.

```bash
docker run --rm mini-ai-ops-lab:day11
```

`--rm`은 실행이 끝난 container를 제거한다. 이 명령의 log와 artifact는 container 안에 있으므로 container와 함께 사라지고, build한 image는 유지된다.

실제 작업 결과를 host에 보존하려면 프로젝트 root에서 `logs/`와 `artifacts/`를 bind mount한다.

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --mount type=bind,source="$PWD/logs",target=/app/logs \
  --mount type=bind,source="$PWD/artifacts",target=/app/artifacts \
  mini-ai-ops-lab:day11
```

- `--user`는 생성 파일의 소유자를 현재 WSL 사용자와 맞춘다.
- bind mount는 container의 결과 경로를 host 프로젝트 경로와 연결한다.
- 정상 실행은 host에 success log와 `artifacts/{run_id}/model.pkl`을 만든다.
- container는 종료 후 제거되지만 bind mount에 기록한 결과와 image는 유지된다.

같은 환경에서 실패 처리를 확인하려면 image 이름 뒤에 실행 명령을 지정한다.

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --mount type=bind,source="$PWD/logs",target=/app/logs \
  --mount type=bind,source="$PWD/artifacts",target=/app/artifacts \
  mini-ai-ops-lab:day11 \
  python src/run_job.py --fail
```

예상 결과는 failed log 추가, model artifact 미생성, exit code `1`이다. 최근 결과는 `tail -n 2 logs/runs.jsonl`로 읽을 수 있다.

Container에서 host의 최근 실험 기록을 읽기만 하려면 `logs/`를 read-only로 연결한다.

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --mount type=bind,source="$PWD/logs",target=/app/logs,readonly \
  mini-ai-ops-lab:day11 \
  python src/list_runs.py --experiment iris-baseline --limit 3
```

이 명령은 image나 log를 변경하지 않고 선택한 실험의 최근 run을 최신순으로 출력한다.

현재 `requirements.txt`는 `scikit-learn>=1.5,<2.0`처럼 호환 가능한 version 범위를 사용한다. 한번 build된 image는 설치된 package 조합을 유지하지만, 나중에 새로 build하면 범위 안의 더 새로운 version이 선택될 수 있다. 실제 검증에서는 host의 `scikit-learn 1.5.1`과 container의 `1.9.0`이 같은 metric을 만들었지만 pickle 크기는 달랐다. pickle model은 가능한 한 생성할 때 사용한 image와 같은 환경에서 불러온다. 완전히 동일한 package 조합을 다시 build하려면 이후 별도의 lock file이나 정확한 version 고정이 필요하다.

## 학습 작업 관리

기본 학습 작업은 `configs/train.yaml`에 따라 scikit-learn 내장 Iris dataset을 나눈 뒤 `LogisticRegression` 모델을 학습하고 accuracy를 계산한다.

학습과 artifact 저장만 직접 확인하려면 프로젝트 root에서 다음 명령을 실행한다.

```bash
python src/train_job.py --config configs/train.yaml
```

정상 실행되면 다음과 같은 JSON 한 줄이 출력된다.

```json
{"artifact_path": "artifacts/{run_id}/model.pkl", "config": {"experiment_name": "iris-baseline", "max_iterations": 200, "random_state": 42, "test_size": 0.2}, "config_path": "configs/train.yaml", "metrics": {"accuracy": 0.9666666666666667, "test_samples": 30, "train_samples": 120}, "run_id": "{run_id}"}
```

run ID는 실행할 때마다 달라진다. 실제 운영 흐름에서는 아래의 `src/run_job.py`를 사용해 학습 결과를 run log와 함께 기록한다.

## 모델 Artifact 저장

각 학습 실행은 UTC 생성 시각과 UUID suffix를 조합한 run ID를 사용한다. 학습된 model은 다른 실행 결과를 덮어쓰지 않도록 다음 경로에 저장한다.

```text
artifacts/{run_id}/model.pkl
```

저장된 model 파일은 다음 명령으로 확인한다.

```bash
find artifacts -maxdepth 2 -type f -name 'model.pkl' -printf '%p %s bytes\n' | sort
```

이 명령은 파일을 변경하지 않고 artifact 경로와 크기를 출력한다. `artifacts/`의 실행 결과는 `.gitignore`에 따라 Git에서 제외된다. `model.pkl`은 Python pickle 형식이므로 신뢰할 수 없는 외부 파일을 불러오지 않는다.

## 설정 기반 실험 추적

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

```bash
python src/list_runs.py --limit 5
python src/list_runs.py --experiment iris-baseline --limit 3
```

두 명령은 run log를 읽기만 한다. 첫 번째는 전체 최근 run을, 두 번째는 `iris-baseline`의 최근 run만 최신순으로 출력한다. Day 9 이전 record에 새 field가 없으면 `-`로 표시하고, 기존 `config`에 parameter가 있으면 비교 열을 보완한다.

## 이전 Run 재현

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

## Agent Tool Allowlist

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

Day 11은 Tool 정의와 검증까지만 구현했다. Day 12의 `src/tool_runner.py`가 Agent의 요청 이름을 이 allowlist와 비교해 등록되지 않은 Tool을 거부하고 허용된 Python handler를 실행할 예정이다. 현재는 Agent identity나 role을 구분하지 않으므로 모든 요청에 같은 allowlist가 적용된다.

## 로그와 감사 기록

실행 중 생성되는 운영 기록은 JSON Lines(JSONL) 형식을 사용한다.

- `logs/runs.jsonl`: 학습 실행 기록
- `logs/audit.jsonl`: 향후 추가할 Agent 도구 호출 기록

성공한 학습 실행을 기록하려면 프로젝트 root에서 다음 명령을 실행한다.

```bash
python src/run_job.py --config configs/train.yaml
```

이 명령은 새로운 model artifact를 생성하고 `logs/runs.jsonl` 끝에 실행 기록 한 줄을 추가한다. 성공과 실패 기록은 공통으로 `run_id`, `experiment_name`, `parameters`, `status`, `started_at`, `ended_at`, `duration_seconds`, `config_path`, `config`, `metrics`, `artifact_path`, `error_type`, `error_message`, `traceback`을 포함한다. 성공하면 검증된 설정, metric과 artifact 경로가 채워지고 error field는 `null`이 된다.

실패 처리 경로는 다음 명령으로 안전하게 재현한다.

```bash
python src/run_job.py --fail
echo $?
tail -n 1 logs/runs.jsonl
```

`--fail`은 실제 환경을 손상시키지 않고 검증용 `RuntimeError`를 발생시킨다. 이 실행은 model artifact를 만들지 않고 `failed` record를 한 줄 추가하며 exit code `1`을 반환한다. 바로 이어 실행한 `echo $?`가 `1`을 출력하고 마지막 log에 오류 종류, 메시지, traceback이 있으면 예상대로 처리된 것이다.

최근 실행 기록은 다음 명령으로 확인한다.

```bash
python src/list_runs.py --limit 3
```

이 명령은 로그를 변경하지 않고 최근 세 run의 실험 이름, 상태, accuracy, parameter, run ID와 artifact 경로를 비교 가능한 열로 출력한다. 원본 JSON을 확인해야 할 때는 `tail -n 3 logs/runs.jsonl`을 사용한다. JSONL은 한 실행을 독립된 JSON 한 줄로 저장하므로 기존 전체 내용을 다시 쓰지 않고 새 기록을 추가할 수 있다.

생성된 로그 파일은 Git에서 제외한다. 빈 디렉터리는 `.gitkeep` placeholder를 사용해 저장소에 유지한다.

## 장애 시나리오

현재는 제어된 학습 실패의 증상, log 확인과 정상 실행을 통한 복구 절차를 문서화했다. 설정 파일이 없거나 조건이 잘못된 경우도 학습 전에 실패로 기록한다. Artifact 저장 실패, 도구 timeout, 허용되지 않은 도구 요청과 과도한 log 증가는 관련 기능을 구현하면서 추가한다.

현재 구현한 학습 실패 재현과 복구 확인 절차는 [장애 시나리오](docs/failure-scenarios.md), 이전 성공 run의 재실행 절차는 [Runbook](docs/runbook.md)에서 확인할 수 있다.

## 보안과 백업 고려사항

- 실제 비밀정보를 Git에 저장하지 않는다.
- 안전한 예시 설정만 커밋한다.
- 로그에 민감한 운영 정보가 포함될 수 있다고 가정한다.
- artifact가 쌓이기 전에 보존 기간과 백업 절차를 정한다.
- 향후 도구 실행기에는 allowlist에 필요한 최소 권한만 부여한다.

## 기술 위키와 작업 기록

프로젝트에 필요한 개념은 [기술 위키](docs/wiki/README.md)에 정리한다. 날짜별 구현 기록은 [작업 일지 인덱스](docs/work-logs/README.md)에서 확인할 수 있다. 전체 방향은 [프로젝트 계획](docs/project-plan.md), 일별 진행 방식은 [일별 작업 흐름](docs/daily-codex-workflow.md)을 참고한다.
