# Runbook

## 목적

이 문서는 Mini AI Ops Lab의 운영 절차를 설명한다. 현재 초안은 이전 학습 run의 조건을 확인하고 같은 환경에서 다시 실행한 뒤 결과를 비교하는 재현 절차를 다룬다. 모든 명령은 WSL의 프로젝트 root에서 실행한다.

```bash
cd /home/hskim/project/mini-ai-ops-lab
```

## 재현의 의미와 현재 기준

재현은 과거 run을 수정하거나 덮어쓰는 작업이 아니다. 원본 record와 model을 보존한 상태에서 같은 조건으로 새 run을 만들고 결과를 비교하는 작업이다.

현재 프로젝트는 다음 항목이 모두 참이면 재현 성공으로 판단한다.

- `experiment_name`이 같다.
- `parameters`가 같다.
- `metrics`가 같다.
- 원본과 재현 model artifact가 모두 존재한다.
- 두 run ID와 artifact 경로는 서로 다르다.

실행 시각과 `duration_seconds`는 실행할 때마다 달라질 수 있으므로 비교하지 않는다. 이 기준은 운영 흐름의 반복 가능성을 확인하는 현재 프로젝트 기준이며 model 파일의 byte나 모든 예측값이 동일함을 증명하지는 않는다.

## 사전 조건

- Docker가 실행 중이어야 한다.
- 프로젝트의 `logs/runs.jsonl`과 `artifacts/`가 있어야 한다.
- 재현에 사용할 Docker image가 local에 남아 있어야 한다.
- 원본 run은 `success` 상태이고 `parameters`, `metrics`, `artifact_path`가 있어야 한다.

## 이전 Run 재현 절차

### 1. 재현할 성공 Run 선택

최근 `iris-baseline` run을 조회한다.

```bash
python src/list_runs.py --experiment iris-baseline --limit 5
```

- 목적: 재현 기준으로 사용할 성공 run ID, parameter, metric과 artifact 경로를 찾는다.
- 변경 여부: `logs/runs.jsonl`을 읽기만 한다.
- 성공 기준: `status`가 `success`이고 parameter, accuracy와 artifact 경로가 표시된다.

Day 10에서 선택한 원본은 다음과 같다.

```text
run_id: 20260812T004148291974Z-e2bef42e
experiment_name: iris-baseline
accuracy: 0.9666666666666667
artifact_path: artifacts/20260812T004148291974Z-e2bef42e/model.pkl
```

### 2. 원본 Run의 기록과 Artifact 확인

원본 JSONL record를 보기 쉽게 출력한다.

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

원본을 만들 때 사용한 Day 9 Docker image로 다시 학습한다.

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --mount type=bind,source="$PWD/logs",target=/app/logs \
  --mount type=bind,source="$PWD/artifacts",target=/app/artifacts \
  mini-ai-ops-lab:day9
```

- 목적: 원본과 같은 image 및 image 안의 `configs/train.yaml`로 새 학습 run을 만든다.
- 변경 여부: host의 `logs/runs.jsonl`에 success record를 추가하고 `artifacts/{새-run-id}/model.pkl`을 생성한다. 실행이 끝난 container는 `--rm`으로 제거되지만 image와 host 결과는 유지된다.
- 성공 기준: exit code `0`, 새 run ID, `status: success`, metric과 artifact 경로가 출력된다.

Day 10에서 생성한 재현 run은 다음과 같다.

```text
run_id: 20260813T050336148461Z-c104baf9
accuracy: 0.9666666666666667
artifact_path: artifacts/20260813T050336148461Z-c104baf9/model.pkl
```

### 4. 원본과 재현 Run 비교

```bash
python src/compare_runs.py \
  --source-run 20260812T004148291974Z-e2bef42e \
  --candidate-run 20260813T050336148461Z-c104baf9
```

- 목적: 재현돼야 할 조건과 결과, 두 artifact의 존재 여부를 자동으로 확인한다.
- 변경 여부: run log와 artifact 경로를 읽기만 한다.
- 성공 기준: 모든 `checks`가 `true`, `reproduced`가 `true`, exit code가 `0`이다.
- 실패 기준: 비교값 불일치, artifact 누락, 존재하지 않는 run 또는 failed run은 exit code `1`을 반환한다.

이번 검증에서는 experiment 이름, parameter와 metric이 같았고 원본·재현 model이 모두 존재했다. 두 run ID와 artifact 경로는 서로 달랐으므로 별개의 실행 결과로 보존됐다.

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

## 관련 문서

- [프로젝트 README](../README.md)
- [Architecture](architecture.md)
- [장애 시나리오](failure-scenarios.md)
- [MLOps 위키](wiki/mlops.md)
- [작업 일지](work-logs/README.md)
