# 장애 시나리오

Mini AI Ops Lab에서 재현할 수 있는 장애의 증상, 확인할 로그, 원인과 복구 절차를 기록한다. 명령은 별도 안내가 없으면 프로젝트 root에서 실행한다.

## 1. 학습 작업 실패

### 목적

학습 또는 artifact 저장 과정에서 exception이 발생해도 실패 사실과 원인이 run log에 남고 process가 올바른 exit code를 반환하는지 확인한다.

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

현재 `--fail` 시나리오에서는 실패 처리 검증을 위해 `run_training_job(force_failure=True)`가 의도적인 `RuntimeError`를 발생시킨다. 실제 운영에서는 `train_model()`의 학습 오류나 `save_model()`의 경로·권한·disk 오류도 같은 `except Exception` 경로에서 기록된다.

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

## 2. Agent Tool Timeout

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

## 향후 추가할 시나리오

- model artifact 저장 실패
- config load 실패
- 허용되지 않은 tool 요청
- 과도한 log 증가
