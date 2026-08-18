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
- `src/config_loader.py`
- `src/list_runs.py`
- `src/tool_runner.py`
- `src/audit_logger.py`

### Day 4~5 성공·실패 run log

`src/run_job.py`는 학습 작업이 끝나면 성공과 실패를 같은 schema로 `logs/runs.jsonl`에 한 줄씩 추가한다.

- `run_id`: 실행과 artifact를 연결하는 고유 식별자
- `status`: `success` 또는 `failed`
- `started_at`, `ended_at`: UTC ISO 8601 형식의 실행 시작·종료 시각
- `duration_seconds`: `perf_counter()`로 측정한 경과 시간
- `config_path`, `config`: 지정한 설정 경로와 검증을 통과해 실제 사용한 값
- `experiment_name`, `parameters`: 같은 목적의 run grouping과 비교용 학습값
- `metrics`, `artifact_path`: 성공하면 결과가 있고 실패하면 `null`
- `error_type`, `error_message`, `traceback`: 실패하면 원인이 있고 성공하면 `null`

### Day 13 Agent Tool audit log

`src/audit_logger.py`는 Tool 요청이 끝날 때마다 `logs/audit.jsonl`에 한 줄을 추가한다. 허용된 실행뿐 아니라 미등록 요청, handler 실패와 timeout도 기록한다.

- `tool_name`: 요청한 Tool 이름
- `status`: `success`, `failed` 또는 `timeout`
- `started_at`, `ended_at`: 요청 전체의 UTC 시작·종료 시각
- `duration_seconds`: 설정 검증부터 결과 처리까지 단조 시계로 측정한 시간
- `input_provided`: 원문을 저장하지 않고 입력 제공 여부만 나타냄
- `timeout_seconds`: 요청에 적용한 제한 시간
- `error_type`, `error_message`: 거부·실패·timeout 원인

Run log와 audit log는 목적이 다르다.

| Log | 질문 | 기록 시점 |
|---|---|---|
| `logs/runs.jsonl` | 학습이 어떤 조건과 결과로 끝났는가? | 학습 작업 종료 시 |
| `logs/audit.jsonl` | Agent가 어떤 Tool을 요청했고 어떻게 처리됐는가? | 모든 Tool 요청 종료 시 |

`python src/run_job.py`로 직접 학습하면 run log만 남는다. `tool_runner.py --tool run_train_job`을 사용하면 학습 run log와 Tool audit log가 모두 남는다.

### Day 14 log schema 변화와 일관성 검수

기능이 단계적으로 추가되면서 `logs/runs.jsonl`에는 서로 다른 시점의 schema가 함께 존재한다.

| 도입 시점 | 추가된 정보 | 현재 record 수 |
|---|---|---:|
| Day 4 | run ID, 상태, 시각, duration, metric, artifact | 2 |
| Day 5 | 오류 종류, 메시지와 traceback | 6 |
| Day 8 | config와 config 경로 | 3 |
| Day 9 이후 | experiment 이름과 parameters | 6 |

이 차이는 기존 record가 손상됐다는 뜻이 아니라 기능이 추가되기 전에는 해당 field가 존재하지 않았다는 뜻이다. 과거 기록을 보기 좋게 만들기 위해 임의로 덮어쓰지 않고 원본을 보존하며, `list_runs.py`처럼 조회하는 쪽에서 없는 field를 안전하게 처리한다.

Day 14 검수 시점에는 run log 17건과 audit log 10건이 모두 JSON으로 해석됐다. Success run 12건의 `artifact_path`가 모두 실제 파일과 연결됐고, 현재 Day 9 이후 schema 6건과 audit schema 10건도 필요한 field와 상태 규칙을 통과했다.

실제 `model.pkl`은 16개라 run log가 연결한 12개보다 4개 많았다. 그중 3개는 run logging 도입 전 만들어진 artifact이고, 나머지 1개는 낮은 수준의 학습 진입점을 직접 실행한 결과로 추정된다. 과거 증거일 수 있으므로 자동 삭제하거나 로그를 인위적으로 만들지 않고 보존한다.

Audit log는 Day 13부터 생성됐으므로 그 이전 Tool 요청 기록은 존재하지 않는다. 또한 현재 audit schema에는 내부 학습의 `run_id`가 없어 `run_train_job` audit record와 run record를 직접 결합할 수 없다. 두 흐름을 정확히 추적하려면 이후 공통 `request_id` 또는 `run_id`를 전달해야 한다.

### Day 15 장애 시나리오와 제어된 실패 검증

장애 시나리오는 오류 메시지를 새로 만드는 기능이 아니다. 이미 구현된 실패 처리 경로가 실제로 상태, 오류와 일부 결과를 기록하는지 안전하게 재현하고, 운영자가 확인·복구할 순서를 문서화한 것이다.

| 장애 | 기록 위치 | 대표 상태와 오류 |
|---|---|---|
| 학습 작업 실패 | `logs/runs.jsonl` | `failed`, `RuntimeError` 또는 학습 exception |
| Model artifact 저장 실패 | `logs/runs.jsonl` | `failed`, `OSError` 등 저장 exception |
| Config load 실패 | `logs/runs.jsonl` | `failed`, `FileNotFoundError` 또는 `ValueError` |
| Tool timeout | `logs/audit.jsonl` | `timeout`, `ToolTimeoutError` |
| 미허용 Tool 요청 | `logs/audit.jsonl` | `failed`, `ToolNotAllowedError` |

제어된 실패는 실제 disk 고갈이나 권한 손상을 만들지 않고 같은 exception 처리 경로를 반복 확인하는 방법이다. `--fail`은 `RuntimeError`를 발생시키고, artifact 검증은 현재 Python process 안에서 `save_model()`이 `OSError`를 내도록 임시 교체했다. 후자는 source code와 실제 filesystem 권한을 바꾸지 않는다.

Artifact 검증 명령의 exit code `0`은 학습 성공이 아니라 검사 조건인 `failed`와 `OSError`가 예상대로 기록됐다는 뜻이다. 운영 상태를 판단할 때는 검증 프로그램의 exit code와 내부 run record의 `status`를 구분해야 한다.

복구는 기존 failed record를 success로 고치는 작업이 아니다. 오류와 일부 결과를 확인하고 원인을 제거한 뒤 새 요청을 실행해 새 success record와 artifact를 만든다. 이전 실패 기록은 장애 증거로 보존한다.

이 다섯 유형은 단순한 학습용 가상 상황이 아니라 실제 MLOps 운영에서도 발생할 수 있다. Data·학습 오류, disk 공간·권한 문제, 잘못된 config, 느리거나 멈춘 작업과 정책 밖 Tool 요청을 작은 project 범위에서 다룬 것이다. 안전한 failure injection은 실제 원인을 그대로 만드는 대신 동일한 application exception 처리 경로와 운영 절차를 확인한다.

다만 application이 잡을 수 있는 exception을 검증했다고 모든 실환경 장애가 해결되는 것은 아니다. OS의 강제 종료, log write 실패, network storage, 동시 실행과 부분 파일은 별도의 관찰·정리 대책이 필요하다. 따라서 장애 시나리오는 테스트 증거이면서 현재 운영 대응의 출발점이며, 실행환경이 커질 때 계속 확장해야 한다.

## 알아둘 명령어나 코드

```bash
python src/run_job.py --config configs/train.yaml
python src/run_job.py --config configs/missing.yaml
python src/run_job.py --fail
python src/list_runs.py --limit 5
python src/list_runs.py --experiment iris-baseline --limit 3
python src/tool_runner.py --tool echo --input "hello" --timeout 1
python src/tool_runner.py --tool run_train_job --timeout 0
echo $?
tail -n 3 logs/runs.jsonl
tail -n 5 logs/audit.jsonl
wc -l logs/runs.jsonl
```

첫 번째 실행은 새 artifact와 success log를 만든다. 존재하지 않는 설정 경로는 `FileNotFoundError` failed log를 남기며 artifact를 만들지 않는다. `--fail` 실행은 검증용 exception을 발생시켜 failed log만 만든다. `list_runs.py` 명령은 전체 또는 선택한 실험의 최근 record를 변경 없이 조회한다. Tool Runner 명령은 각각 success와 timeout audit record를 추가한다. `echo $?`는 바로 앞 process의 exit code를 확인한다. `tail`과 `wc`는 원본 로그나 전체 줄 수를 확인한다.

## 흔한 실패 사례

- 실패: 로그가 구조화되지 않았거나 필요한 필드가 없음
- 증상: 장애가 발생했지만 원인을 추적할 수 없음
- 확인할 것: 로그 schema, 예외 처리, run ID의 일관성
- 복구 방법: 상태, 시각, 실행 시간, 오류, artifact 경로를 일관된 필드로 기록함
- 실패: 의도한 프로젝트 로그가 보이지 않음
- 증상: 실행은 성공했지만 `logs/runs.jsonl`을 찾을 수 없음
- 확인할 것: 명령을 실행한 현재 작업 디렉터리와 상대 경로
- 복구 방법: 프로젝트 root에서 `python src/run_job.py`를 실행함
- 실패: exception이 terminal에만 표시되고 운영 기록이 남지 않음
- 증상: process는 실패했지만 해당 run ID와 오류 원인을 나중에 찾을 수 없음
- 확인할 것: 학습과 artifact 저장 코드가 `try/except` 안에 있는지, failed record가 append되는지 확인
- 복구 방법: 일반적인 `Exception`을 포착하여 상태, 오류 종류·메시지, traceback과 exit code를 함께 기록함
- 실패: 설정 파일을 읽기 전에 작업이 중단됨
- 증상: failed record의 `config_path`는 있지만 `config`는 `null`임
- 확인할 것: `error_type`, `error_message`와 지정한 설정 파일의 존재 여부
- 복구 방법: 설정 경로와 파일 내용을 수정한 뒤 같은 운영 명령을 다시 실행함
- 실패: JSONL 일부가 손상돼 최근 run 조회가 중단됨
- 증상: 특정 line에서 JSON decode 오류가 발생함
- 확인할 것: `list_runs.py`가 출력한 경고의 line 번호와 원본 `logs/runs.jsonl`
- 복구 방법: 조회 도구는 손상 line을 경고 후 건너뛰고 나머지를 표시한다. 원본 수정 전에는 별도 backup과 손상 원인 확인이 필요함
- 실패: Tool은 실행됐지만 audit log를 쓸 수 없음
- 증상: Tool 결과가 발생했을 수 있지만 CLI는 audit 파일 접근 오류와 exit code `1`을 반환함
- 확인할 것: `logs/` 경로, 파일 소유자·권한, disk 공간과 Container mount
- 복구 방법: audit 경로 쓰기 문제를 해결하고 이미 발생한 업무 상태를 별도로 확인함
- 실패: audit log에 원문 입력이나 결과 전체를 저장함
- 증상: credential이나 민감한 요청 내용이 운영 로그에 남을 수 있음
- 확인할 것: audit schema와 기록되는 field
- 복구 방법: 이 프로젝트처럼 `input_provided`와 최소 오류 정보만 남기고 민감정보를 제외함
- 실패: 모든 과거 run에 현재 schema를 강제로 요구함
- 증상: 기능 추가 전의 정상 record를 손상된 로그로 잘못 판단함
- 확인할 것: record 생성 시점과 당시 지원하던 field, 현재 schema field의 존재 여부
- 복구 방법: 원본을 임의 수정하지 않고 schema 세대를 구분하며 조회 도구에서 누락 field를 호환 처리함

## 실용적인 이해

로그는 운영 장애를 이해할 때 가장 먼저 확인하는 자료다. 이 프로젝트는 학습 작업과 도구 호출을 한 건씩 추적할 수 있도록 run log와 audit log를 JSONL 형식으로 기록한다.

`logs/`는 실행 과정에 관한 기록을 보관한다. 반면 `artifacts/`는 실행이 만든 모델과 같은 실제 결과물을 보관한다.

현재 모든 학습 실행 기록은 하나의 `logs/runs.jsonl`에 누적되고, model은 `artifacts/{run_id}/model.pkl`에 실행별로 분리된다. 로그의 `run_id`와 `artifact_path`를 사용하면 어떤 실행이 어느 model을 만들었는지 찾을 수 있다. `open("a")`의 append mode는 파일이 없으면 만들고, 있으면 기존 내용 끝에 새 JSON 한 줄을 추가한다.

exception을 잡는 목적은 실패를 성공처럼 숨기는 것이 아니라 원인을 기록 가능한 데이터로 바꾸는 것이다. 실패 record를 저장한 뒤에도 CLI는 exit code `1`을 반환해 shell이나 상위 시스템이 실패를 인식하게 한다. 성공은 `stdout`과 exit code `0`, 실패는 `stderr`와 exit code `1`로 구분한다.

설정 로드도 run의 일부이므로 학습 전에 실패하더라도 실행 기록을 남긴다. 파일을 읽지 못한 경우 `config_path`는 사용자가 요청한 경로를 보존하고, 검증된 값이 없다는 사실은 `config: null`로 구분한다.

`src/list_runs.py`는 JSONL을 앞에서부터 한 줄씩 읽되 filter를 통과한 최근 N개만 `deque`에 유지하고 최신순으로 출력한다. Day 9 이전 record는 새 field가 없어도 오류로 처리하지 않고 없는 값은 `-`로 표시한다. 기존 `config`에 학습값이 있으면 `parameters` 열을 보완하되 원본 record는 수정하지 않는다.

traceback은 오류가 어느 호출 경로에서 발생했는지 보여준다. JSONL에서는 줄바꿈이 escape되므로 긴 traceback도 하나의 실행 record가 한 물리적 줄을 유지한다. `except Exception`은 일반적인 작업 오류를 처리하되 `KeyboardInterrupt`나 `SystemExit` 같은 process 제어 신호까지 강제로 변환하지 않는다.

Audit log의 `duration_seconds`는 Tool handler 시간만이 아니라 설정 로드, allowlist·입력 검증, child process 시작과 결과 전달을 포함한 요청 전체 시간이다. 그래서 `run_train_job` audit duration은 내부 run log의 학습 duration보다 조금 길 수 있다.

잘못된 Tool 이름은 실행되지 않아도 요청 시도 자체가 운영 사건이므로 `failed` audit record가 남는다. 반면 음수 timeout처럼 CLI argument parsing에서 거부된 값은 Tool 요청이 시작되기 전이므로 audit record가 생기지 않는다.

## Codex Q&A 기록

- 질문: Day 3까지는 학습한 model을 저장하고 Day 4에는 그 학습의 로그까지 기록하는 것인가?
  답변: 맞다. `model.pkl`은 학습 결과물이고 `runs.jsonl`은 실행 시각, 상태, metric, 결과물 경로를 설명하는 운영 이력이다. 두 데이터는 같은 `run_id`로 연결된다.
- 질문: 현재는 실행 로그 파일 하나를 지정하고 학습 후 로그를 추가하는 방식인가?
  답변: 맞다. 모든 성공 run은 `logs/runs.jsonl`에 JSON 한 줄씩 누적되고, model artifact만 run ID별 디렉터리로 분리된다.
- 질문: `run_training_job(force_failure=True)`를 호출하면 임시 실패 환경을 테스트하는 것인가?
  답변: 실제 환경 장애를 만들지는 않는다. 학습 전에 제어된 `RuntimeError`를 발생시켜 같은 실패 처리 경로를 안전하게 반복 검증한다. CLI의 `--fail`이 이 값을 전달한다.
- 질문: 실패 시 failed log가 남는지 테스트하기 위해 수정하고 검증한 것인가?
  답변: 맞다. `--fail`은 검증용 발생 장치이고 `try/except`와 failed record 작성은 실제 학습 또는 artifact 저장 exception에도 적용되는 운영 기능이다.
- 질문: 기존 Tool들에 대한 기록을 남기는 것인가?
  답변: 맞다. `logs/audit.jsonl`은 정상 실행, 미등록 요청, handler 실패와 timeout을 모두 같은 schema로 기록해 Agent의 Tool 사용 이력을 추적한다.
- 질문: 기능이 추가되면서 기존 로그와 새 로그 사이에 차이가 생긴 것인가?
  답변: 맞다. 오류, config, experiment 추적 기능이 순서대로 추가되면서 과거 record에는 새 field가 없다. 이는 손상이 아니라 schema evolution이며, 원본을 수정하는 대신 조회 코드가 누락 field를 안전하게 처리한다.
- 질문: 실패 시나리오를 만들어 실제 실패의 오류 메시지를 확인할 수 있게 하는 작업인가?
  답변: 맞다. 다만 오류 처리 기능을 새로 만드는 것이 아니라 이미 구현된 실패 경로를 안전하게 재현해 terminal, run log 또는 audit log에서 무엇을 확인하고 어떻게 복구할지를 운영 문서로 만드는 작업이다.
- 질문: 이 장애들은 실무에서도 발생하기 때문에 추가한 것인가?
  답변: 맞다. 학습 오류, artifact 저장 실패, config 오류, timeout과 정책 밖 Tool 요청은 실제 운영에서도 발생한다. Project에서는 실제 환경을 손상시키지 않도록 원인만 제어된 방식으로 재현했다.
- 질문: 테스트용 시나리오일 뿐인가, 실제 MLOps 작업의 장애에 대비한 것인가?
  답변: 둘 다다. 개발 중에는 실패 처리와 log를 검증하는 테스트이고, 운영 중에는 확인할 증거와 복구 순서를 제공하는 대응서다. 다만 제어된 exception 검증만으로 OS 강제 종료, log write 실패와 부분 파일까지 완전히 보장하지는 않는다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [MLOps](mlops.md)
- [장애 시나리오](../failure-scenarios.md)
