# 장애 시나리오

Mini AI Ops Lab에서 재현할 수 있는 장애의 증상, 확인할 로그, 원인과 복구 절차를 기록한다. 명령은 별도 안내가 없으면 프로젝트 root에서 실행한다.

## 문서의 역할과 검증 범위

이 문서는 테스트용 오류 목록과 실제 운영 대응서라는 두 역할을 함께 가진다.

- 개발·검증 역할: 실무에서 발생할 수 있는 장애를 project를 손상시키지 않는 방법으로 재현해 기존 실패 처리와 log 기록이 동작하는지 확인한다.
- 운영 역할: 실제 MLOps 작업 중 같은 유형의 장애가 발생했을 때 먼저 확인할 log, 일부 결과, 원인과 복구 순서를 제공한다.

학습 오류, disk·권한 문제, 잘못된 config, 느리거나 멈춘 Tool과 미허용 요청은 실제 운영에서도 발생할 수 있다. 이 project에서는 실제 disk를 가득 채우거나 권한을 제거하는 대신 `--fail`, 제어된 `OSError`, 즉시 timeout과 검증용 미등록 이름으로 같은 처리 경로를 안전하게 확인한다. 이런 방식은 failure injection 또는 failure testing의 작은 예다.

제어된 재현이 모든 실환경 장애를 보장하지는 않는다. OS가 memory 부족으로 process를 강제 종료하면 Python exception과 failed record가 남지 않을 수 있고, log 파일 자체를 쓸 수 없으면 장애 기록도 실패할 수 있다. 실제 filesystem 쓰기 중단은 빈 디렉터리나 일부 파일을 남길 수 있으며, network storage·동시 실행·log rotation도 현재 검증 범위 밖이다. 따라서 이 문서는 현재 확인된 대응 기준이며 실제 운영환경이 확장되면 시나리오도 함께 보완한다.

## 빠른 판단표

| 장애 | 먼저 확인할 기록 | 대표 상태와 오류 | 추가 확인 대상 |
|---|---|---|---|
| 학습 작업 실패 | `logs/runs.jsonl` | `failed`, `RuntimeError` 또는 학습 exception | traceback, model 생성 여부 |
| Model artifact 저장 실패 | `logs/runs.jsonl` | `failed`, `OSError` 등 저장 exception | Disk, 권한, 불완전한 파일 |
| Agent Tool timeout | `logs/audit.jsonl` | `timeout`, `ToolTimeoutError` | 일부 run·artifact 발생 여부 |
| Config load 실패 | `logs/runs.jsonl` | `failed`, `FileNotFoundError` 또는 `ValueError` | 요청 경로, YAML 형식과 값 |
| 허용되지 않은 Tool 요청 | `logs/audit.jsonl` | `failed`, `ToolNotAllowedError` | `configs/tools.yaml` Allowlist |

## 공통 대응 순서

1. Terminal의 오류 JSON과 exit code를 확인한다.
2. 학습 장애는 run log, Tool 요청 장애는 audit log에서 상태와 오류를 확인한다.
3. Run ID, Tool 이름, 시작 시각을 기준으로 관련 record와 일부 결과를 구분한다.
4. 원인을 해결하기 전에 기존 실패 log를 성공처럼 수정하거나 덮어쓰지 않는다.
5. 쓰기 작업이면 model, 빈 디렉터리와 다른 일부 결과가 남았는지 확인한다.
6. 원인을 해결한 뒤 새 요청으로 정상 동작을 검증하고 이전 failed record와 새 success record를 함께 보존한다.

## 1. 학습 작업 실패

### 목적

설정 검증 후 학습 과정에서 exception이 발생해도 실패 사실과 원인이 run log에 남고 process가 올바른 exit code를 반환하는지 확인한다.

### 안전한 재현 방법

```bash
python src/run_job.py --fail
echo $?
```

- `python src/run_job.py --fail`은 실제 외부 장애 대신 검증용 `RuntimeError`를 발생시킨다.
- 이 명령은 `logs/runs.jsonl`에 실패 record 한 줄을 추가하지만 model artifact는 만들지 않는다.
- `echo $?`는 바로 앞 명령의 exit code를 읽기만 하며 파일을 변경하지 않는다.
- 예상 결과는 terminal의 failed JSON과 exit code `1`이다.

### 증상

- process가 exit code `1`로 종료된다.
- terminal의 `stderr`에 `status`가 `failed`인 JSON이 출력된다.
- 해당 run ID의 model artifact가 생성되지 않는다.

### 확인할 로그

```bash
tail -n 1 logs/runs.jsonl
```

이 명령은 마지막 실행 기록을 읽기만 한다. 다음 field를 확인한다.

- `status`: `failed`
- `metrics`, `artifact_path`: `null`
- `error_type`: 발생한 exception 종류
- `error_message`: 사람이 확인할 수 있는 오류 설명
- `traceback`: 오류가 발생한 파일과 호출 경로
- `run_id`, 시각, 실행 시간: 실패 실행을 구분하는 정보

JSONL은 traceback의 줄바꿈을 escape한 상태로 한 물리적 줄에 저장하므로, 실패 record 하나가 여러 JSONL record로 나뉘지 않는다.

### 원인

현재 `--fail` 시나리오에서는 실패 처리 검증을 위해 `run_training_job(force_failure=True)`가 의도적인 `RuntimeError`를 발생시킨다. 실제 운영에서는 data 처리나 `train_model()`의 학습 오류도 같은 `except Exception` 경로에서 기록된다. 저장 단계의 오류는 다음 Model artifact 저장 실패 시나리오에서 별도로 다룬다.

### 복구 및 정상 동작 확인

검증용 실패 원인은 `--fail` option이므로 이를 제거하고 정상 명령을 다시 실행한다.

```bash
python src/run_job.py
echo $?
tail -n 2 logs/runs.jsonl
```

- 정상 명령은 새 model artifact와 success record를 생성한다.
- `echo $?`의 예상 출력은 `0`이다.
- 마지막 두 log에서 이전 `failed`와 새 `success` 상태를 확인한다.
- success record의 `artifact_path`에 실제 model 파일이 있으면 정상 동작이 복구된 것이다.

실제 장애에서는 `error_type`, `error_message`, `traceback`으로 원인을 먼저 확인하고 해당 원인을 제거한 뒤 같은 정상 실행 절차로 복구를 검증한다.

### 예방과 현재 범위

- exception을 숨기지 않고 failed status와 traceback을 같은 run ID로 기록한다.
- 성공과 실패가 같은 field를 사용하도록 하여 상태별 기록을 비교하기 쉽게 한다.
- `KeyboardInterrupt`와 `SystemExit`처럼 일반적인 작업 오류가 아닌 process 제어 신호는 `except Exception`으로 강제로 변환하지 않는다.
- 현재는 단일 process 실행을 기준으로 하며 동시 log 쓰기와 log rotation은 이후 운영 범위에서 검토한다.

## 2. Model Artifact 저장 실패

### 목적

학습은 완료됐지만 경로, 권한, disk 공간 또는 직렬화 문제로 model을 저장하지 못했을 때 성공으로 잘못 기록하지 않고 실패 원인과 run ID를 남기는지 확인한다.

### 안전한 재현 방법

```bash
python -c "import json; from unittest.mock import patch; from src.run_job import run_training_job; patcher=patch('src.run_job.save_model', side_effect=OSError('검증을 위해 발생시킨 artifact 저장 실패입니다.')); patcher.start(); record=run_training_job(); patcher.stop(); print(json.dumps(record, ensure_ascii=False, sort_keys=True)); raise SystemExit(0 if record['status'] == 'failed' and record['error_type'] == 'OSError' else 1)"
```

- `unittest.mock.patch`는 이 Python process 안에서만 `save_model()` 대신 제어된 `OSError`를 발생시킨다.
- Source file, 디렉터리 권한과 실제 disk 상태는 변경하지 않는다.
- 학습 후 저장 단계에서 실패하므로 `logs/runs.jsonl`에 failed record 한 줄을 추가하지만 model artifact는 만들지 않는다.
- 이 검증 명령 자체의 exit code `0`은 예상한 실패 record가 만들어졌다는 뜻이다. 학습 작업의 상태는 출력 JSON의 `failed`다.

### 증상

- 학습 계산이 끝났어도 최종 상태가 `failed`다.
- `metrics`와 `artifact_path`는 `null`이며 해당 run은 배포하거나 재현 비교에 사용할 정상 model이 없다.
- `error_type`과 `error_message`에 저장 단계에서 발생한 오류가 남는다.
- 실제 파일 쓰기 중 발생한 장애라면 빈 run 디렉터리나 불완전한 파일이 남을 수 있다.

### 확인할 로그와 결과

```bash
tail -n 1 logs/runs.jsonl
find artifacts -maxdepth 2 -type f -name 'model.pkl'
df -h .
ls -ld artifacts
```

- `tail`은 마지막 run의 `status`, `run_id`, `error_type`, `error_message`와 `artifact_path`를 읽는다.
- `find`는 저장이 완료된 model 파일 목록을 읽는다.
- `df`는 project가 있는 filesystem의 전체·사용·여유 공간을 읽는다.
- `ls`는 `artifacts/`의 소유자와 권한을 읽는다.
- 네 명령 모두 파일을 변경하지 않는다.

Failed record에서 다음 값을 확인한다.

- `status`: `failed`
- `error_type`: 검증에서는 `OSError`
- `error_message`: 검증용 저장 실패 설명 또는 실제 filesystem 오류
- `metrics`, `artifact_path`: 완료된 결과물이 없으므로 `null`
- `run_id`: 남은 임시 디렉터리나 파일을 조사할 때 사용할 식별자

### 원인

- `artifacts/` 또는 하위 경로에 쓸 권한이 없다.
- Disk 공간이나 inode가 부족하다.
- 같은 run ID 디렉터리가 이미 존재한다.
- 저장 중 process가 종료되거나 filesystem I/O 오류가 발생했다.
- `pickle.dump()`가 model 객체를 직렬화하지 못했다.

현재 `save_model()`은 run 디렉터리를 만든 뒤 `model.pkl`을 바로 기록한다. 따라서 실제 쓰기 도중 실패하면 run log는 failed여도 빈 디렉터리 또는 일부 파일이 남을 가능성이 있다.

### 복구 및 정상 동작 확인

1. Failed record의 `run_id`, `error_type`, `error_message`를 확인한다.
2. `df -h .`와 `ls -ld artifacts`로 공간, 소유자와 쓰기 권한을 확인한다.
3. 해당 run ID 경로에 일부 결과가 남았는지 확인하고, 다른 정상 run의 model을 삭제하지 않도록 대상을 구분한다.
4. 공간·권한·filesystem 원인을 해결한 뒤 새 run ID로 정상 학습을 다시 실행한다.

```bash
python src/run_job.py --config configs/train.yaml
echo $?
tail -n 2 logs/runs.jsonl
```

- 정상 재실행은 새 success record와 `artifacts/{새-run-id}/model.pkl`을 생성한다.
- 예상 exit code는 `0`이다.
- 이전 failed record는 장애 증거로 보존하고, 새 success record의 `artifact_path`가 실제 파일이면 복구가 완료된 것이다.

### 예방과 현재 범위

- 실행 전에 artifact filesystem의 여유 공간, mount와 쓰기 권한을 확인한다.
- Run ID별 디렉터리를 사용하고 기존 디렉터리를 덮어쓰지 않는다.
- 저장 실패도 학습 실패와 같은 run schema로 기록한다.
- 현재는 임시 파일에 완전히 쓴 뒤 rename하는 원자적 저장과 실패 시 임시 파일 자동 정리를 구현하지 않았다.
- 불완전한 결과를 지울 때는 failed run ID와 경로를 먼저 확인하고 정상 model을 함께 삭제하지 않는다.

## 3. Agent Tool Timeout

### 목적

Tool이 끝나지 않거나 너무 오래 자원을 점유할 때 제한 시간 이후 별도 process를 종료하고 그 사실을 audit log에서 추적할 수 있는지 확인한다.

### 안전한 재현 방법

```bash
python src/tool_runner.py --tool run_train_job --timeout 0
echo $?
```

- `--timeout 0`은 결과를 기다리지 않고 즉시 timeout 경로를 재현한다.
- Tool 요청은 `logs/audit.jsonl`에 기록된다.
- 쓰기 Tool을 중단하는 검증이므로 일반적으로 일부 결과가 남을 가능성을 고려해야 한다.
- Day 13 검증에서는 run log와 model artifact 개수가 변하지 않았지만 이를 항상 보장하지는 않는다.
- 예상 결과는 terminal의 timeout JSON과 exit code `1`이다.

### 증상

- process가 exit code `1`로 종료된다.
- terminal의 `stderr`에 `status: timeout`과 `ToolTimeoutError`가 출력된다.
- Agent가 정상 Tool 결과를 받지 못한다.
- 작업 진행 시점에 따라 일부 log, artifact 또는 외부 상태가 남을 수 있다.

### 확인할 로그와 결과

```bash
tail -n 1 logs/audit.jsonl
tail -n 1 logs/runs.jsonl
find artifacts -maxdepth 2 -type f -name 'model.pkl'
```

- 첫 명령은 마지막 Tool 요청의 `status`, `duration_seconds`, `timeout_seconds`와 오류를 확인한다.
- 두 번째 명령은 timeout Tool이 학습 run record를 남겼는지 읽기만 한다.
- 세 번째 명령은 일부 model artifact가 생성됐는지 목록을 읽기만 한다.
- Audit record의 성공 기준은 `status: timeout`, `error_type: ToolTimeoutError`와 요청한 제한 시간이다.

### 원인

검증에서는 `--timeout 0`을 사용해 의도적으로 결과 대기 시간을 없앴다. 실제 운영에서는 무한 반복, 느린 학습, 응답하지 않는 외부 서비스, 잠금 대기 또는 부족한 CPU·memory 때문에 제한 시간을 넘길 수 있다.

### 복구 및 정상 동작 확인

1. `logs/audit.jsonl`에서 어떤 Tool이 얼마 후 timeout 됐는지 확인한다.
2. 쓰기 Tool이면 관련 run log, artifact와 외부 상태에 일부 결과가 남았는지 확인한다.
3. 원인을 해결하거나 정상 소요 시간보다 긴 제한 시간을 정한다.
4. 정상 제한 시간으로 다시 실행한다.

```bash
python src/tool_runner.py --tool run_train_job --timeout 30
echo $?
tail -n 2 logs/audit.jsonl
```

- 정상 재실행은 run log와 model artifact를 생성하므로 project 상태를 변경한다.
- 예상 결과는 exit code `0`, Tool과 학습의 `success`, 새 model 경로다.
- 마지막 audit 두 줄에서 이전 `timeout`과 새 `success`를 확인하면 복구 검증이 끝난다.

### 예방과 현재 범위

- Tool별 정상 소요 시간과 자원 특성에 맞는 timeout을 사용한다.
- Handler는 별도 process에서 실행해 timeout 후 남은 실행을 종료한다.
- Timeout은 transaction rollback이 아니므로 쓰기 작업은 임시 경로와 완료 후 rename 같은 원자적 저장 방식을 추가로 고려한다.
- 현재 기본값은 모든 Tool에 공통 30초이며 Tool별 설정과 재시도 정책은 아직 없다.
- Audit log 쓰기 실패, 동시 실행과 log rotation은 별도 운영 과제로 남아 있다.

## 4. Config Load 실패

### 목적

지정한 학습 설정 파일이 없거나 YAML 형식과 값이 잘못됐을 때 학습을 시작하지 않고, 요청한 설정 경로와 실패 원인을 run log에 남기는지 확인한다.

### 안전한 재현 방법

```bash
python src/run_job.py --config configs/missing.yaml
echo $?
```

- 존재하지 않는 경로를 지정해 설정 파일을 열 수 없는 상황을 재현한다.
- 이 명령은 `logs/runs.jsonl`에 실패 record 한 줄을 추가하지만 학습과 model artifact 저장은 실행하지 않는다.
- `echo $?`는 바로 앞 명령의 exit code를 읽기만 한다.
- 예상 결과는 terminal의 failed JSON, `FileNotFoundError`와 exit code `1`이다.

### 증상

- process가 exit code `1`로 종료된다.
- terminal의 `stderr`에 `status: failed`와 설정 파일 경로 오류가 출력된다.
- `config`, `experiment_name`, `parameters`, `metrics`, `artifact_path`가 `null`이다.
- 해당 run ID의 model artifact가 생성되지 않는다.

### 확인할 로그

```bash
tail -n 1 logs/runs.jsonl
```

이 명령은 마지막 run record를 읽기만 한다. 다음 field를 확인한다.

- `status`: `failed`
- `config_path`: 사용자가 요청한 `configs/missing.yaml`
- `config`: 검증을 마친 설정이 없으므로 `null`
- `error_type`: 파일이 없으면 `FileNotFoundError`; YAML이나 설정값 문제면 `ValueError`
- `error_message`, `traceback`: 실패한 경로와 호출 위치
- `metrics`, `artifact_path`: 학습 전 실패했으므로 `null`

### 원인

- `--config`에 존재하지 않는 경로를 지정했다.
- YAML 문법이 올바르지 않다.
- 필수 설정이 없거나 지원하지 않는 설정 이름이 있다.
- `test_size`, `random_state`, `max_iterations`의 자료형 또는 값 범위가 유효하지 않다.
- 설정 파일을 읽을 권한이 없다.

`src/config_loader.py`는 YAML을 읽은 뒤 필수·추가 항목, 자료형과 값 범위를 검사한다. 검증을 통과하기 전에는 학습 함수에 설정을 전달하지 않는다.

### 복구 및 정상 동작 확인

1. Run record의 `config_path`, `error_type`과 `error_message`를 확인한다.
2. 존재하는 설정 경로를 지정하거나 YAML의 형식과 값을 수정한다.
3. 정상 설정으로 새 run을 실행한다.

```bash
python src/run_job.py --config configs/train.yaml
echo $?
tail -n 2 logs/runs.jsonl
```

- 정상 재실행은 새 success run과 model artifact를 생성하므로 project 상태를 변경한다.
- 예상 exit code는 `0`이다.
- 마지막 두 record에서 이전 `failed`와 새 `success`를 확인하고, success record의 `artifact_path`가 실제 파일이면 복구가 완료된 것이다.

### 예방과 현재 범위

- 실행 전에 설정 파일 경로가 올바른지 확인한다.
- 설정은 `config_loader.py`의 검증을 통과한 뒤에만 학습에 사용한다.
- 실패 record에는 요청한 `config_path`를 보존해 어떤 파일을 읽으려 했는지 추적한다.
- 원본 설정에 secret을 넣지 않고 저장소에 올릴 수 있는 값만 YAML로 관리한다.
- 현재는 설정 파일의 내용과 검증 오류를 기록하지만 별도의 config schema version은 없다.

## 5. 허용되지 않은 Tool 요청

### 목적

Agent가 `configs/tools.yaml`의 Allowlist에 없는 Tool을 요청했을 때 임의 기능을 실행하지 않고, 거부된 요청의 이름과 원인을 audit log에 남기는지 확인한다.

### 안전한 재현 방법

```bash
python src/tool_runner.py --tool forbidden_command
echo $?
```

- `forbidden_command`는 Allowlist와 `TOOL_HANDLERS`에 등록되지 않은 검증용 이름이다.
- Tool Runner는 handler를 찾거나 별도 process를 시작하기 전에 요청을 거부한다.
- 임의 shell 명령, 학습과 artifact 저장은 실행되지 않는다.
- 거부 시도는 `logs/audit.jsonl`에 failed record 한 줄로 추가된다.
- 예상 결과는 terminal의 failed JSON, `ToolNotAllowedError`와 exit code `1`이다.

### 증상

- Agent가 요청한 Tool 결과를 받지 못한다.
- Process가 exit code `1`로 종료된다.
- Terminal의 `stderr`에 `status: failed`, `result: null`과 `ToolNotAllowedError`가 출력된다.
- Run log와 model artifact는 생성되지 않는다.

### 확인할 설정과 Audit Log

```bash
sed -n '1,200p' configs/tools.yaml
tail -n 1 logs/audit.jsonl
```

- `sed`는 현재 허용된 Tool 이름, 입력 형태, 영향 수준과 resource를 읽기만 한다.
- `tail`은 마지막 Tool 요청 기록을 읽기만 한다.
- 두 명령 모두 project 상태를 변경하지 않는다.

Audit record에서 다음 값을 확인한다.

- `tool_name`: 요청한 `forbidden_command`
- `status`: `failed`
- `error_type`: `ToolNotAllowedError`
- `error_message`: Allowlist에 등록되지 않았다는 설명
- `input_provided`: 입력 원문 대신 입력 제공 여부
- `timeout_seconds`: 요청에 적용하려던 제한 시간

### 원인

- Agent 또는 사용자가 Tool 이름을 잘못 입력했다.
- 필요한 Tool이 정책상 허용되지 않았다.
- `configs/tools.yaml`과 실제 요청 이름의 대소문자 또는 표기가 다르다.
- 설정에는 등록됐지만 `TOOL_HANDLERS`에 안전한 Python handler가 없는 경우에는 별도의 `ToolHandlerNotImplementedError`로 거부된다.

### 복구 및 정상 동작 확인

1. Audit record에서 실제 요청한 `tool_name`과 오류 종류를 확인한다.
2. `configs/tools.yaml`에서 사용할 수 있는 기존 Tool 이름과 필요한 입력 형태를 확인한다.
3. 단순 오타라면 허용된 이름으로 요청을 고쳐 다시 실행한다.
4. 새 기능이 정말 필요하다면 정책 검토 후 Tool 설정과 고정 handler를 함께 구현하고 별도로 검증한다. YAML에 이름만 추가해서 임의 명령을 실행하지 않는다.

```bash
python src/tool_runner.py --tool echo --input "hello"
echo $?
tail -n 2 logs/audit.jsonl
```

- 정상 재실행은 업무 데이터나 artifact를 만들지 않지만 success audit record 한 줄을 추가한다.
- 예상 exit code는 `0`, `status`는 `success`, 결과는 `hello`다.
- 마지막 두 audit record에서 이전 `failed`와 새 `success`를 확인하면 요청 수정이 검증된다.

### 예방과 현재 범위

- Tool 이름은 config의 Allowlist와 실제 Python handler 양쪽에서 확인한다.
- YAML 문자열을 shell 명령으로 해석하지 않고 검토된 handler 함수에만 연결한다.
- 미등록 요청도 보안·운영 사건이므로 audit log에 남긴다.
- 단순히 편리하다는 이유로 광범위한 shell 실행 Tool을 허용하지 않는다.
- 현재는 Agent identity와 role 구분이 없어 모든 요청이 하나의 공통 Allowlist를 사용한다.

## 향후 추가할 시나리오

- 과도한 log 증가

## 관련 문서

- [프로젝트 README](../README.md)
- [Architecture](architecture.md)
- [Runbook](runbook.md)
- [로깅과 모니터링 위키](wiki/logging-monitoring.md)
- [Agent 실행환경 위키](wiki/agent-runtime.md)
