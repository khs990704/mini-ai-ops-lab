# Runbook

## 목적

이 문서는 Mini AI Ops Lab을 준비하고 실행한 뒤 결과를 확인하고, 재현·장애 복구·정리하는 운영 절차를 설명한다. 운영자는 정상 실행과 장애 상황에서 무엇을 어떤 순서로 확인할지 이 문서를 기준으로 판단한다.

모든 명령은 별도 안내가 없으면 WSL의 project root에서 실행한다.

```bash
cd /home/hskim/project/mini-ai-ops-lab
```

## 실행환경 선택

| 실행환경 | 사용할 때 | 특징 |
|---|---|---|
| Local Python | 빠르게 기능을 확인하거나 source를 수정하며 검증할 때 | 현재 WSL의 Python과 설치된 dependency를 사용함 |
| Docker | 다른 host에서도 같은 Python과 dependency 환경을 반복할 때 | Image build가 필요하며 host 결과를 보존하려면 directory mount가 필요함 |

Local과 Docker는 별도의 학습 구현을 사용하지 않는다. 두 환경 모두 `src/run_job.py`와 `src/tool_runner.py`를 같은 운영 진입점으로 사용한다.

## 환경 준비와 사전 점검

### 1. Python과 Dependency 확인

```bash
python --version
python -c "import sklearn, yaml; print('dependencies: ok')"
```

- 목적: 현재 shell에서 사용할 Python과 필수 library인 scikit-learn, PyYAML을 불러올 수 있는지 확인한다.
- 변경 여부: version과 import 가능 여부만 확인하며 파일을 변경하지 않는다.
- 성공 기준: Python version과 `dependencies: ok`가 출력되고 두 명령 모두 exit code `0`이다.

Import 오류가 발생하면 project dependency를 설치한다.

```bash
python -m pip install -r requirements.txt
```

- 목적: `requirements.txt`에 선언된 실행 dependency를 현재 Python 환경에 설치한다.
- 변경 여부: 현재 Python 환경의 package를 설치하거나 갱신한다. Project log와 artifact는 만들지 않는다.
- 성공 기준: 설치가 오류 없이 끝나고 위 import 확인 명령이 exit code `0`을 반환한다.

### 2. 학습 Config 검증

```bash
python -c "import json; from src.config_loader import load_train_config; print(json.dumps(load_train_config('configs/train.yaml'), ensure_ascii=False, indent=2, sort_keys=True))"
```

- 목적: 학습 전에 YAML 형식, 필수 field, 자료형과 값 범위를 확인한다.
- 변경 여부: `configs/train.yaml`을 읽기만 하며 학습, run log와 model을 만들지 않는다.
- 성공 기준: `experiment_name`, `test_size`, `random_state`, `max_iterations`가 포함된 검증 완료 JSON과 exit code `0`이 반환된다. `config_loader.py`는 import용 module이므로 이 명령이 loader 함수를 명시적으로 호출한다.

실패하면 출력된 오류에 따라 경로, YAML 문법, 누락·추가 field와 값 범위를 수정한다. 검증을 통과하기 전에는 학습을 실행하지 않는다.

### 3. Agent Tool 정책 검증

```bash
python src/tool_config_loader.py --config configs/tools.yaml
```

- 목적: Allowlist의 Tool 이름, 입력 형태, 영향 수준과 접근 resource가 현재 정책에 맞는지 확인한다.
- 변경 여부: `configs/tools.yaml`과 resource 경로를 검사할 뿐 Tool, audit log와 학습을 실행하지 않는다.
- 성공 기준: 네 Tool 정의가 포함된 검증 완료 JSON과 exit code `0`이 반환된다.

설정에 이름을 추가하는 것만으로는 Tool이 실행되지 않는다. 실제 요청에는 `src/tool_runner.py`의 검토된 고정 handler도 필요하다.

### 4. Docker 선택 점검

Docker를 사용할 때만 daemon과 현재 project image를 확인한다.

```bash
docker version
docker image inspect mini-ai-ops-lab:day13
```

- 목적: Docker client가 daemon과 통신할 수 있고 Day 13 기능이 포함된 image가 local에 있는지 확인한다.
- 변경 여부: Docker 상태와 image metadata를 읽기만 한다.
- 성공 기준: Client·Server version과 `mini-ai-ops-lab:day13` image 정보가 출력된다.

Image가 없거나 `requirements.txt`, `src/`, `configs/`, `Dockerfile`이 변경됐다면 project root에서 다시 build한다.

```bash
docker build -t mini-ai-ops-lab:day13 .
```

- 목적: 현재 dependency, source와 config를 포함한 재현 가능한 local image를 생성한다.
- 변경 여부: Docker image와 build cache를 생성하거나 갱신한다. Project의 run log와 artifact는 만들지 않는다.
- 성공 기준: Build가 exit code `0`으로 끝나고 image export와 tag 지정이 완료된다.

Docker를 사용할 수 없어도 Local Python 점검이 모두 통과하면 Local 운영 절차를 진행할 수 있다.

## 실행 전 확인표

- Project root에서 명령을 실행하고 있는가?
- Python dependency import가 성공하는가?
- `configs/train.yaml` 검증이 통과하는가?
- Agent Tool을 사용한다면 `configs/tools.yaml` 검증이 통과하는가?
- Docker를 선택했다면 daemon과 사용할 image가 준비됐는가?
- 새 실행이 run log, audit log 또는 model artifact를 추가한다는 점을 확인했는가?

## 기본 실행과 결과 확인

### 1. 직접 학습 실행

```bash
python src/run_job.py --config configs/train.yaml
echo $?
```

- 목적: 검증된 기본 설정으로 새 학습 run을 실행하고 model을 저장한다.
- 변경 여부: `logs/runs.jsonl`에 success 또는 failed record 한 줄을 추가한다. 성공하면 `artifacts/{run_id}/model.pkl`도 생성한다.
- 성공 기준: terminal에 `status: success`, metric, run ID와 artifact 경로가 출력되고 `echo $?`가 `0`이다.
- 실패 기준: exit code `1`과 failed JSON이 출력된다. 이때 model이 있다고 가정하지 말고 run record의 오류부터 확인한다.

운영 기록이 필요한 학습의 기본 진입점은 `run_job.py`다. `train_job.py`를 직접 실행하면 학습과 artifact 저장은 확인할 수 있지만 run log가 생기지 않으므로 일반 운영에는 사용하지 않는다.

Docker image의 동작만 확인하고 결과를 버리는 smoke test는 다음과 같다.

```bash
docker run --rm mini-ai-ops-lab:day13
```

- 목적: Day 13 image 안에서 기본 학습 진입점이 정상 실행되는지 확인한다.
- 변경 여부: Container 내부에 run log와 model을 만들지만 종료 시 `--rm`으로 container와 함께 제거한다. Host project 결과와 image는 바뀌지 않는다.
- 성공 기준: `status: success`, metric과 container 내부 artifact 경로가 출력되고 exit code가 `0`이다.

Docker 실행 결과를 host project에 보존하려면 directory를 mount한다.

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --mount type=bind,source="$PWD/logs",target=/app/logs \
  --mount type=bind,source="$PWD/artifacts",target=/app/artifacts \
  mini-ai-ops-lab:day13
```

- 목적: Container의 재현 가능한 실행환경을 사용하면서 run log와 model을 host에 보존한다.
- 변경 여부: Host `logs/runs.jsonl`과 `artifacts/{run_id}/model.pkl`을 추가하고 종료된 container는 제거한다.
- 성공 기준: Exit code `0`, success JSON과 host의 새 run record·model이 모두 확인된다.
- 주의: `--user`는 생성 파일 소유자를 현재 WSL 사용자와 맞춘다. Mount 대상은 project root의 정확한 `logs/`, `artifacts/`인지 실행 전에 확인한다.

### 2. Agent Tool 요청

Tool 호출 경로를 가볍게 확인하려면 `echo`를 실행한다.

```bash
python src/tool_runner.py --tool echo --input "runbook-check" --timeout 1
echo $?
```

- 목적: Allowlist, 입력 검증, handler 실행, timeout과 audit 기록의 정상 흐름을 확인한다.
- 변경 여부: 업무 데이터와 model은 만들지 않지만 `logs/audit.jsonl`에 success record 한 줄을 추가한다.
- 성공 기준: `status: success`, `result: runbook-check`와 exit code `0`이다.

최근 학습 상태를 Agent Tool 경로로 조회할 수 있다.

```bash
python src/tool_runner.py --tool read_log_summary --timeout 1
```

- 목적: 최근 run 5건의 상태와 핵심 결과를 읽는다.
- 변경 여부: Run log와 artifact는 읽기만 하지만 Tool 요청 자체는 audit log 한 줄을 추가한다.
- 성공 기준: `status: success`와 최근 run 요약이 출력된다.

Agent 요청으로 새 학습을 시작할 때만 쓰기 Tool을 사용한다.

```bash
python src/tool_runner.py --tool run_train_job --timeout 30
```

- 목적: Tool Runner의 통제 아래 기본 설정 학습을 실행한다.
- 변경 여부: audit log, run log와 model artifact를 모두 추가한다.
- 성공 기준: Tool의 `status`, 내부 `training_status`가 모두 `success`이고 `run_id`와 실제 `artifact_path`가 출력된다.
- 주의: Timeout이나 handler 실패 뒤에는 run log와 artifact에 일부 결과가 남았는지 별도로 확인한다.

### 3. 최근 Run 확인

```bash
python src/list_runs.py --limit 3
```

- 목적: 최근 세 학습의 experiment, 상태, metric, parameter, run ID와 artifact 경로를 비교한다.
- 변경 여부: `logs/runs.jsonl`을 읽기만 한다.
- 성공 기준: 최신순 표가 출력되고 방금 실행한 run의 상태와 결과를 확인할 수 있다.

원본 JSON이 필요하면 다음 명령을 사용한다.

```bash
tail -n 3 logs/runs.jsonl
```

이 명령은 마지막 세 물리적 JSONL record를 읽기만 한다. 실패 분석에서는 `status`, `error_type`, `error_message`, `traceback`을 함께 확인한다.

### 4. Audit Log 확인

```bash
tail -n 3 logs/audit.jsonl
```

- 목적: 최근 세 Tool 요청의 이름, 상태, 시각, duration, timeout과 오류를 확인한다.
- 변경 여부: Audit log를 읽기만 한다.
- 성공 기준: 각 줄이 독립된 JSON 객체이며 방금 요청한 Tool의 상태가 존재한다.

### 5. Model Artifact 확인

```bash
find artifacts -maxdepth 2 -type f -name 'model.pkl' -printf '%p %s bytes\n' | sort
```

- 목적: 저장된 model 경로와 파일 크기를 확인한다.
- 변경 여부: `artifacts/`를 읽기만 한다.
- 성공 기준: Success run의 `artifact_path`와 같은 `artifacts/{run_id}/model.pkl`이 0보다 큰 크기로 표시된다.

Run log의 `run_id`와 `artifact_path`를 기준으로 model을 연결한다. 단순히 가장 최근 수정된 파일이라는 이유만으로 특정 run의 결과라고 판단하지 않는다.

### 실행 경로별 생성 결과

| 실행 경로 | Run log | Audit log | Model artifact |
|---|---|---|---|
| `python src/run_job.py` | 추가 | 없음 | 성공 시 추가 |
| `echo`, `read_log_summary` Tool | 없음 | 추가 | 없음 |
| `run_train_job` Tool | 추가 | 추가 | 내부 학습 성공 시 추가 |

## 재현의 의미와 현재 기준

재현은 과거 run을 수정하거나 덮어쓰는 작업이 아니다. 원본 record와 model을 보존한 상태에서 같은 조건으로 새 run을 만들고 결과를 비교하는 작업이다.

현재 프로젝트는 다음 항목이 모두 참이면 재현 성공으로 판단한다.

- `experiment_name`이 같다.
- `parameters`가 같다.
- `metrics`가 같다.
- 원본과 재현 model artifact가 모두 존재한다.
- 두 run ID와 artifact 경로는 서로 다르다.

실행 시각과 `duration_seconds`는 실행할 때마다 달라질 수 있으므로 비교하지 않는다. 이 기준은 운영 흐름의 반복 가능성을 확인하는 현재 프로젝트 기준이며 model 파일의 byte나 모든 예측값이 동일함을 증명하지는 않는다.

## 이전 Run 재현 사전 조건

- 프로젝트의 `logs/runs.jsonl`과 `artifacts/`가 있어야 한다.
- 원본 run은 `success` 상태이고 `parameters`, `metrics`, `artifact_path`가 있어야 한다.
- 원본 run에 기록된 config와 실제 model artifact가 남아 있어야 한다.
- 원본을 만든 code, dependency와 실행환경을 가능한 범위에서 확인해야 한다.
- Docker로 만든 원본을 같은 image에서 재현하려면 Docker daemon과 해당 image가 local에 남아 있어야 한다.

현재 run record에는 Docker image와 Git commit이 기록되지 않는다. 따라서 어떤 image로 실행했는지는 당시 작업 기록처럼 별도 운영 증거가 있을 때만 확정할 수 있다.

## 이전 Run 재현 절차

일반적인 재현 순서는 다음과 같다.

```text
원본 success run 선택
        ↓
원본 config와 artifact 확인
        ↓
같은 조건과 실행환경으로 새 run 생성
        ↓
원본 run ID와 새 run ID 비교
```

원본 record를 수정하거나 기존 artifact 경로에 model을 덮어쓰지 않는다. 재현 실행도 별도의 새 run이므로 run log 한 줄과 새 artifact를 생성한다.

### 1. 재현할 성공 Run 선택

최근 `iris-baseline` run을 조회한다.

```bash
python src/list_runs.py --experiment iris-baseline --limit 5
```

- 목적: 재현 기준으로 사용할 성공 run ID, parameter, metric과 artifact 경로를 찾는다.
- 변경 여부: `logs/runs.jsonl`을 읽기만 한다.
- 성공 기준: `status`가 `success`이고 parameter, accuracy와 artifact 경로가 표시된다.

아래부터는 Day 10에서 실제로 검증한 run ID를 사용한 예시다. 다른 run을 재현할 때는 조회 결과에서 선택한 success run ID로 교체한다.

Day 10에서 선택한 원본은 다음과 같다.

```text
run_id: 20260812T004148291974Z-e2bef42e
experiment_name: iris-baseline
accuracy: 0.9666666666666667
artifact_path: artifacts/20260812T004148291974Z-e2bef42e/model.pkl
```

### 2. 원본 Run의 기록과 Artifact 확인

원본 JSONL record를 보기 쉽게 출력한다. `run_id` 값은 재현하려는 원본으로 바꾼다.

```bash
python -c "import json; from pathlib import Path; run_id='20260812T004148291974Z-e2bef42e'; records=[json.loads(line) for line in Path('logs/runs.jsonl').read_text(encoding='utf-8').splitlines()]; print(json.dumps(next(record for record in records if record.get('run_id') == run_id), ensure_ascii=False, indent=2, sort_keys=True))"
```

- 목적: 원본의 `config`, `parameters`, `metrics`와 `artifact_path`를 확인한다.
- 변경 여부: run log를 읽기만 한다.
- 성공 기준: 선택한 run ID의 `status`가 `success`이고 필요한 비교 field가 출력된다.

원본 model이 실제로 존재하는지 확인한다.

```bash
test -f artifacts/20260812T004148291974Z-e2bef42e/model.pkl
echo $?
```

- 목적: log가 가리키는 원본 artifact의 존재 여부를 확인한다.
- 변경 여부: 파일을 읽거나 변경하지 않는다.
- 성공 기준: `echo $?`가 `0`을 출력한다.

원본에 기록된 설정은 다음과 같다.

```yaml
experiment_name: iris-baseline
test_size: 0.2
random_state: 42
max_iterations: 200
```

재현 전에 `configs/train.yaml`이 이 값과 같은지 확인한다. 값이 다르면 원본 record의 값으로 별도 YAML을 준비하고 `--config`로 지정해야 한다. 원본 JSONL record 자체를 수정해서는 안 된다.

### 3. 같은 실행환경에서 새 Run 생성

원본이 현재 Local Python과 같은 code·dependency에서 만들어졌고 기록된 config와 `configs/train.yaml`이 같다면 다음 명령으로 새 run을 만든다.

```bash
python src/run_job.py --config configs/train.yaml
```

- 목적: 원본에 기록된 학습 조건으로 새로운 비교 대상 run을 생성한다.
- 변경 여부: run log 한 줄과 성공 시 새 model artifact를 추가한다.
- 성공 기준: exit code `0`, 원본과 다른 새 run ID, `status: success`와 실제 artifact 경로가 출력된다.

원본이 Docker image에서 만들어졌고 당시 image를 알고 있다면 같은 image를 사용한다. Day 10 검증에서는 원본을 만들 때 사용한 Day 9 image로 다시 학습했다.

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --mount type=bind,source="$PWD/logs",target=/app/logs \
  --mount type=bind,source="$PWD/artifacts",target=/app/artifacts \
  mini-ai-ops-lab:day9
```

- 목적: 확인된 원본과 같은 image 및 image 안의 `configs/train.yaml`로 새 학습 run을 만든다.
- 변경 여부: host의 `logs/runs.jsonl`에 success record를 추가하고 `artifacts/{새-run-id}/model.pkl`을 생성한다. 실행이 끝난 container는 `--rm`으로 제거되지만 image와 host 결과는 유지된다.
- 성공 기준: exit code `0`, 새 run ID, `status: success`, metric과 artifact 경로가 출력된다.

Day 10에서 생성한 재현 run은 다음과 같다.

```text
run_id: 20260813T050336148461Z-c104baf9
accuracy: 0.9666666666666667
artifact_path: artifacts/20260813T050336148461Z-c104baf9/model.pkl
```

### 4. 원본과 재현 Run 비교

새 실행이 출력한 run ID를 candidate로 지정한다.

```text
python src/compare_runs.py --source-run <원본-run-id> --candidate-run <새-run-id>
```

Angle bracket로 표시한 값은 설명용 placeholder이므로 실제 run ID로 바꿔 실행한다. Day 10의 검증된 두 run은 다음 명령으로 다시 비교할 수 있다.

```bash
python src/compare_runs.py \
  --source-run 20260812T004148291974Z-e2bef42e \
  --candidate-run 20260813T050336148461Z-c104baf9
```

- 목적: 재현돼야 할 조건과 결과, 두 artifact의 존재 여부를 자동으로 확인한다.
- 변경 여부: run log와 artifact 경로를 읽기만 한다.
- 성공 기준: 모든 `checks`가 `true`, `reproduced`가 `true`, exit code가 `0`이다.
- 실패 기준: 비교값 불일치, artifact 누락, 존재하지 않는 run 또는 failed run은 exit code `1`을 반환한다.

Day 10 검증에서는 experiment 이름, parameter와 metric이 같았고 원본·재현 model이 모두 존재했다. 두 run ID와 artifact 경로는 서로 달랐으므로 별개의 실행 결과로 보존됐다.

비교 명령은 새 학습을 실행하지 않고 기존 log와 artifact 존재 여부만 읽는다. 따라서 같은 두 run을 반복 비교해도 project 상태는 바뀌지 않는다.

## 재현이 실패했을 때 확인할 항목

| 확인 결과 | 의미 | 다음 조치 |
|---|---|---|
| `parameters_match: false` | 원본과 다른 학습 조건을 사용함 | 원본 record의 `parameters`와 실행 YAML을 비교함 |
| `metrics_match: false` | 결과가 달라짐 | data, code, dependency, 난수와 실행환경 차이를 확인함 |
| `source_artifact_exists: false` | 원본 model을 찾을 수 없음 | artifact 보존·삭제·mount 경로를 확인함 |
| `candidate_artifact_exists: false` | 재현 model 저장이 완료되지 않음 | 새 run의 status와 error field를 확인함 |
| run을 찾을 수 없음 | 지정한 ID가 JSONL에 없음 | `list_runs.py`로 정확한 run ID를 다시 확인함 |
| run이 `failed` 상태 | 비교할 정상 결과가 없음 | 실패 원인을 해결하고 새 success run을 생성함 |

## 완전한 재현에 대한 현재 제약

같은 config는 재현의 필수 조건이지만 일반적인 머신러닝에서 충분조건은 아니다. 다음 정보도 결과에 영향을 줄 수 있다.

- 학습 code와 Git commit
- 입력 data와 data version
- Python 및 dependency version
- Docker image digest
- CPU·GPU와 비결정적 연산
- 모든 random seed

현재 run record는 config, parameter, metric과 artifact 경로를 저장하지만 Git commit, Docker image digest와 data version은 저장하지 않는다. 또한 `mini-ai-ops-lab:day9` 같은 tag는 같은 이름으로 다시 build할 수 있으므로 장기적으로 동일 image를 보장하는 불변 식별자가 아니다.

따라서 이번 결과는 남아 있던 같은 Day 9 image와 같은 설정에서 현재 metric이 반복됐다는 증거다. 장기적인 재현성을 강화하려면 이후 run record에 code commit, image digest와 dependency 또는 data version을 추가해야 한다.

## 장애 확인과 복구

장애가 발생하면 즉시 같은 명령을 반복하기보다 어떤 실행이 실패했고 일부 결과가 남았는지 먼저 확인한다.

### 1. 최근 운영 기록 확인

```bash
python src/list_runs.py --limit 5
tail -n 5 logs/runs.jsonl
tail -n 5 logs/audit.jsonl
```

- 목적: 최근 학습과 Tool 요청의 상태, 오류와 결과를 확인한다.
- 변경 여부: 세 명령 모두 log를 읽기만 한다.
- 성공 기준: 학습은 `run_id`, Tool 요청은 `tool_name`과 시작 시각을 기준으로 문제가 된 record를 식별할 수 있다.

동시 요청이 있는 환경에서는 마지막 줄이 반드시 방금 실행한 요청이라고 가정하지 않는다. Terminal에 출력된 run ID, Tool 이름과 시각을 log record와 비교한다.

### 2. 오류 종류에 따른 첫 조치

| 증상 또는 오류 | 먼저 확인할 것 | 첫 조치 |
|---|---|---|
| 학습 `RuntimeError` 또는 다른 exception | Run record의 `error_type`, `error_message`, `traceback` | Data, parameter와 학습 code 원인을 해결함 |
| Config `FileNotFoundError`, `ValueError` | `config_path`, `config`, YAML 형식과 값 | 올바른 config를 준비하고 loader 검증을 다시 실행함 |
| Artifact `OSError` 등 | Run ID, disk 공간, directory 권한과 일부 파일 | 저장환경 원인을 해결하고 새 run으로 다시 저장함 |
| `ToolTimeoutError` | Tool 이름, 제한 시간, 일부 run·artifact | 느린 원인을 해결하거나 적정 timeout으로 새 요청함 |
| `ToolNotAllowedError` | 요청 이름, `configs/tools.yaml`, 고정 handler | 오타면 허용된 이름으로 고치고 정책 밖 요청은 거부함 |

각 장애의 안전한 재현, 상세 원인과 예방 방법은 [장애 시나리오](failure-scenarios.md)를 따른다.

### 3. Config 오류 복구

```bash
python -c "import json; from src.config_loader import load_train_config; print(json.dumps(load_train_config('configs/train.yaml'), ensure_ascii=False, indent=2, sort_keys=True))"
```

1. Failed record의 `config_path`와 오류를 확인한다.
2. 경로, YAML 문법, 필수·추가 field와 값 범위를 수정한다.
3. 위 명령이 exit code `0`으로 검증된 JSON을 출력하는지 확인한다.
4. `python src/run_job.py --config configs/train.yaml`로 새 run을 실행한다.

원본 failed record를 success로 수정하지 않는다. 새 success record와 model이 복구 증거다.

### 4. Artifact 저장 오류 복구

```bash
df -h .
ls -ld artifacts
find artifacts -maxdepth 2 -type f -name 'model.pkl' -printf '%p %s bytes\n' | sort
```

1. Failed run의 `run_id`, `error_type`과 `error_message`를 확인한다.
2. Disk 공간, directory 소유자·권한과 해당 run ID의 일부 결과를 확인한다.
3. 공간, mount, 권한 또는 직렬화 원인을 해결한다.
4. 새 run ID로 정상 학습을 실행하고 새 `artifact_path`의 파일을 확인한다.

현재 저장은 임시 파일 작성 후 rename하는 원자적 방식이 아니므로 실제 쓰기 중 실패하면 빈 디렉터리나 불완전한 파일이 남을 수 있다.

### 5. 복구 완료 판단

복구는 오류 메시지가 사라진 것만으로 끝나지 않는다.

- 새 process의 exit code가 `0`인가?
- 새 run 또는 Tool 상태가 `success`인가?
- 쓰기 작업이면 기대한 run log, audit log와 model이 실제로 존재하는가?
- 이전 failed·timeout record와 새 success record가 모두 보존됐는가?
- 같은 원인으로 다시 실패하지 않도록 예방 조치를 반영했는가?

## Agent Tool 요청 확인

### Tool 실행과 Audit Record

Tool Runner의 기본 제한 시간은 30초다. 다음 명령은 `echo` 결과를 반환하고 audit log 한 줄을 추가한다.

```bash
python src/tool_runner.py --tool echo --input "hello" --timeout 1
```

- 목적: 허용된 Tool의 정상 실행과 감사 기록을 확인한다.
- 변경 여부: Tool 자체는 project 업무 데이터를 바꾸지 않지만 `logs/audit.jsonl`에 한 줄을 추가한다.
- 성공 기준: exit code `0`, `status: success`, `result: "hello"`가 출력된다.

최근 요청을 확인한다.

```bash
tail -n 5 logs/audit.jsonl
```

- 목적: 최근 Tool 이름, 상태, 실행 시간, 제한 시간과 오류를 확인한다.
- 변경 여부: audit log를 읽기만 한다.
- 성공 기준: 각 물리적 줄이 독립된 JSON 객체이며 필수 field를 포함한다.

| `status` | 의미 | 다음 확인 |
|---|---|---|
| `success` | 제한 시간 안에 handler가 결과를 반환함 | 쓰기 Tool이면 생성된 업무 결과 확인 |
| `failed` | 미등록·입력 오류 또는 handler 실패 | `error_type`, `error_message`와 설정 확인 |
| `timeout` | 제한 시간 안에 결과를 받지 못해 process를 종료함 | 일부 결과 여부와 자원 상태 확인 |

Audit record는 `tool_name`, `status`, `started_at`, `ended_at`, `duration_seconds`, `input_provided`, `timeout_seconds`, `error_type`, `error_message`를 포함한다. 민감정보 노출을 줄이기 위해 원문 입력과 handler 결과 전체는 저장하지 않는다.

`python src/run_job.py`처럼 Tool Runner를 거치지 않은 직접 학습은 `logs/runs.jsonl`만 기록한다. Agent Tool 이력을 남겨야 한다면 `python src/tool_runner.py --tool run_train_job`을 사용해야 한다.

### Timeout 대응

마지막 요청이 timeout이면 다음 순서로 확인한다.

1. Audit record의 Tool 이름, 제한 시간과 실제 duration을 확인한다.
2. 쓰기 Tool이면 `logs/runs.jsonl`, `artifacts/`와 외부 상태에 일부 결과가 남았는지 확인한다.
3. CPU·memory 부족, 느린 dependency, 잠금이나 무한 반복 원인을 해결한다.
4. 정상 소요 시간을 고려한 timeout으로 새 요청을 실행한다.

```bash
python src/tool_runner.py --tool run_train_job --timeout 30
```

이 명령은 새 학습 run, model artifact와 audit record를 생성한다. `status: success`, `result.training_status: success`와 실제 model 경로가 모두 존재하면 정상 복구다.

CLI가 음수, 무한대 또는 `NaN` timeout을 거부하면 Tool 요청이 시작되기 전이므로 audit record도 생성되지 않는다. Timeout process 종료는 이미 발생한 상태 변경을 자동으로 되돌리지 않는다.

### 미허용 Tool 요청 대응

```bash
python src/tool_config_loader.py --config configs/tools.yaml
```

1. Audit record의 `tool_name`과 `ToolNotAllowedError`를 확인한다.
2. 위 명령으로 현재 Allowlist와 입력 형태를 검증한다.
3. 오타면 허용된 이름으로 요청을 고친다.
4. 새 Tool이 실제로 필요하면 영향과 resource를 검토한 뒤 config 정의와 고정 Python handler를 함께 구현한다.

YAML에 이름만 추가하거나 광범위한 shell 실행을 허용하는 방식으로 장애를 우회하지 않는다. 거부된 요청도 보안·운영 증거이므로 audit record를 보존한다.

## 안전한 정리 절차

정리는 장애 증거와 정상 model을 무조건 삭제하는 작업이 아니다. 먼저 사용량과 대상을 읽기 전용으로 확인한다.

```bash
du -sh logs artifacts
wc -l logs/runs.jsonl logs/audit.jsonl
find artifacts -mindepth 1 -maxdepth 1 -type d -print | sort
docker ps -a
```

- `du`는 log와 artifact의 전체 disk 사용량을 확인한다.
- `wc`는 두 JSONL의 record 수를 확인한다.
- `find`는 run별 artifact directory 후보를 나열한다.
- `docker ps -a`는 실행 중이거나 종료된 container를 확인한다.
- 네 명령 모두 project 파일과 Docker 상태를 변경하지 않는다.

### 정리 대상별 판단

| 대상 | 삭제 전 확인 | 현재 원칙 |
|---|---|---|
| Failed run log | 장애 원인 분석과 감사에 필요한지 | 기존 record를 수정하거나 개별 줄만 임의 삭제하지 않음 |
| Success run log | Model과 재현 기준을 연결하는지 | 연결된 artifact와 함께 보존함 |
| Artifact directory | Success record가 참조하는지, 일부 파일인지 | 참조가 없다는 이유만으로 자동 삭제하지 않음 |
| 종료된 container | 결과가 host mount에 보존됐는지 | 일회성 실행은 처음부터 `docker run --rm`을 사용함 |
| Docker image | 과거 run 재현에 필요한지 | 재현 근거를 확인하기 전에는 삭제하지 않음 |

특정 종료 container가 불필요하다고 확인한 경우에만 다음처럼 정확한 ID를 지정한다.

```text
docker rm <확인한-container-id>
```

Angle bracket 부분을 실제 ID로 교체해야 하며 이 명령은 해당 container를 삭제한다. 실행 중 container, 이름이 비슷한 다른 container와 image는 삭제하지 않는다.

`docker ps -a`에는 다른 project나 개발환경의 container도 함께 표시된다. 종료 상태이거나 오래됐다는 이유만으로 일괄 삭제하지 않고, 이 project에서 만든 container인지와 보존할 volume·결과가 없는지를 먼저 확인한다. Day 16 점검에서는 Mini AI Ops Lab의 종료 container가 남아 있지 않았으므로 삭제를 수행하지 않았다.

Log rotation, artifact backup, 복원 검증과 Secret 노출 대응 기준은 [보안·백업 체크리스트](security-backup-checklist.md)를 따른다. 현재 backup은 수동 절차이므로 원본을 정리하기 전에 별도 경로 복원과 검증을 먼저 완료한다.

## 관련 문서

- [프로젝트 README](../README.md)
- [Architecture](architecture.md)
- [장애 시나리오](failure-scenarios.md)
- [보안·백업 체크리스트](security-backup-checklist.md)
- [MLOps 위키](wiki/mlops.md)
- [작업 일지](work-logs/README.md)
