# MLOps

## 짧은 정의

MLOps는 머신러닝 실험, 학습 실행, 모델, 로그, 배포 관련 artifact를 추적하고 재현할 수 있도록 운영하는 방식이다.

## 이 프로젝트에서 중요한 이유

Mini AI Ops Lab은 단순한 학습 스크립트를 운영 가능한 작업으로 발전시킨다. 모델 정확도만 보는 것이 아니라 어떤 config가 어떤 metric과 artifact를 만들었는지 나중에도 확인할 수 있어야 한다.

## 저장소에서 사용되는 위치

- `src/train_job.py`
- `src/run_job.py`
- `src/config_loader.py`
- `src/list_runs.py`
- `src/compare_runs.py`
- `src/tool_config_loader.py`
- `src/tool_runner.py`
- `src/audit_logger.py`
- `src/storage.py`
- `configs/train.yaml`
- `configs/tools.yaml`
- `logs/runs.jsonl`
- `logs/audit.jsonl`
- `artifacts/`
- `docs/architecture.md`
- `docs/runbook.md`

### 프로젝트 디렉터리 역할

| 디렉터리 | 역할 | 현재 또는 예정 내용 |
|---|---|---|
| `configs/` | 코드 수정 없이 실행 방식을 바꾸는 설정 보관 | 학습용 `train.yaml`, Tool 허용 정책용 `tools.yaml` |
| `src/` | 프로젝트의 실제 동작을 구현하는 소스 코드 보관 | 학습·저장·조회와 Tool 실행·감사 기록 script |
| `logs/` | 실행 과정, 성공·실패 상태, Agent Tool 요청 기록 | 현재 `runs.jsonl`, `audit.jsonl`; 향후 `errors.jsonl` |
| `artifacts/` | 학습 실행이 만든 결과물 보관 | 현재 실행별 `model.pkl`; 향후 설정 사본과 추가 결과 파일 |

현재 흐름은 다음과 같이 이해할 수 있다.

```text
configs/train.yaml
    ↓
src/config_loader.py에서 읽기와 검증
    ↓
src/run_job.py
    ├── src/train_job.py로 학습과 평가
    ├── src/storage.py로 model 저장
    ├── logs/에 실행 기록
    └── artifacts/에 실행 결과물
             ↓
src/list_runs.py로 최근 실험 비교
             ↓
src/compare_runs.py로 재현 run 비교
```

### Day 2 기본 학습 작업

`src/train_job.py`는 다음 순서로 동작한다.

```text
Iris dataset 로딩
       ↓
학습용 120개와 검증용 30개로 분리
       ↓
LogisticRegression 모델 학습
       ↓
검증 데이터 예측
       ↓
accuracy와 sample 수를 JSON으로 출력
```

- training job: 데이터 준비, 모델 학습, 평가를 하나의 실행 단위로 묶은 작업
- 학습 데이터: 모델이 분류 기준을 배우는 데 사용하는 데이터
- 검증 데이터: 학습에 사용하지 않고 학습된 모델을 평가하는 데이터
- metric: 모델 결과를 숫자로 나타낸 값이며, 현재는 정답을 맞힌 비율인 accuracy를 사용함
- `random_state=42`: 실행할 때마다 같은 방식으로 데이터가 나뉘게 하여 결과를 재현할 수 있게 함
- `stratify`: 세 Iris 품종의 비율이 학습·검증 데이터에서 비슷하게 유지되게 함

### Day 3 run ID와 model artifact

Day 3에서는 학습 결과를 memory에서만 사용하지 않고 실행별 파일로 저장한다.

```text
run ID 생성
    ↓
model 학습과 metric 계산
    ↓
artifacts/{run_id}/ 디렉터리 생성
    ↓
model.pkl 저장
    ↓
run ID, metrics, artifact 경로를 JSON으로 출력
```

- run ID: 하나의 학습 실행을 다른 실행과 구분하는 고유 식별자
- model artifact: 학습 작업이 만든 model 파일처럼 실행 후 보존해야 하는 결과물
- 실행별 경로: 각 model을 별도 디렉터리에 저장하여 이전 실행 결과를 덮어쓰지 않는 구조
- 현재 run ID: UTC 생성 시각과 짧은 UUID suffix를 조합하여 실행 시점 확인과 충돌 방지를 함께 고려함
- 현재 model 형식: Python pickle 형식의 `model.pkl`

### Day 4 run log 연결

Day 4에서는 같은 run ID를 성공 run log에도 기록하여 실행 정보와 model 결과물을 연결한다.

```text
logs/runs.jsonl의 run_id와 artifact_path
                  ↓
artifacts/{run_id}/model.pkl
```

`model.pkl`은 학습된 실제 결과물이고, `runs.jsonl`은 그 결과물이 언제 생성됐고 metric과 실행 시간이 어땠는지를 설명하는 운영 기록이다.

### Day 7 component boundary

첫 주 기능은 다음 책임으로 분리된다.

- `run_job.py`: 실행 전체를 조정하고 성공·실패 상태와 exit code를 결정함
- `train_job.py`: data 분리, model 학습과 metric 계산을 담당함
- `storage.py`: run ID와 model artifact 저장을 담당함
- `runs.jsonl`: 실행 상태와 원인을 설명함
- `artifacts/`: 학습된 실제 결과물을 보관함

Architecture 문서는 날짜별 작업을 반복해서 나열하는 문서가 아니라, 현재 구성요소의 책임과 데이터 흐름 및 운영 경계를 설명한다. 날짜별 진행 과정과 검증 이력은 `docs/work-logs/`가 담당한다.

### Day 8 설정 기반 학습과 재현성

Day 8에서는 코드에 고정되어 있던 학습 조건을 `configs/train.yaml`로 옮겼다.

```yaml
test_size: 0.2
random_state: 42
max_iterations: 200
```

`src/config_loader.py`는 YAML을 읽는 데서 끝나지 않고 다음 조건을 학습 전에 검사한다.

- 세 필수 항목이 모두 있는지 확인한다.
- 오타 가능성이 있는 지원하지 않는 항목을 거부한다.
- `test_size`가 `0`보다 크고 `1`보다 작은 숫자인지 확인한다.
- `random_state`가 허용 범위의 정수인지 확인한다.
- `max_iterations`가 양의 정수인지 확인한다.
- Python에서 `bool`이 `int`의 하위 형식인 점을 고려해 `true`, `false`를 정수 설정으로 허용하지 않는다.

검증을 통과한 설정만 `train_job.py`에 전달한다. `run_job.py`는 지정 경로와 실제 사용값을 `config_path`, `config`로 run log에 함께 저장한다. 설정 파일이 나중에 바뀌어도 해당 run에 사용된 값은 로그에서 확인할 수 있다.

### Day 9 experiment tracking과 model traceability

Day 9에서는 `experiment_name`을 추가해 같은 목적의 여러 run을 묶는다.

```text
experiment_name: iris-baseline
├── run_id A → parameters, metrics, artifact A
├── run_id B → parameters, metrics, artifact B
└── run_id C → parameters, metrics, artifact C
```

- `experiment_name`: 같은 목적의 실행을 묶는 label이며 중복될 수 있음
- `run_id`: 개별 학습 실행 한 번을 구분하는 고유 식별자
- `parameters`: model 학습 전에 정한 `test_size`, `random_state`, `max_iterations`
- `metrics`: 학습 후 계산된 accuracy와 sample 수
- `artifact_path`: 해당 run이 만든 model 위치

`config`는 검증된 설정 전체를 보존하고, `experiment_name`과 `parameters`는 비교 도구가 중첩 구조를 매번 해석하지 않도록 최상위 field에도 기록한다. 성공과 실패가 같은 experiment에 속하면 실패 record에도 검증 완료 parameter가 남는다. 설정 검증 자체가 실패했다면 실험과 parameter를 확정할 수 없어 `null`이다.

### Day 10 이전 run 재현

재현은 과거 record를 새 schema로 수정하는 작업이 아니다. 성공한 원본 run을 그대로 보존하고 같은 조건의 새 run을 만든 뒤 결과를 비교한다.

```text
원본 success run
       ↓ 기록된 config와 artifact 확인
같은 Docker image와 설정으로 새 run 생성
       ↓
experiment, parameters, metrics와 artifact 비교
```

현재 프로젝트의 `src/compare_runs.py`는 다음을 재현 성공 기준으로 사용한다.

- Experiment 이름, parameter와 metric이 같다.
- 원본과 재현 model artifact가 모두 존재한다.
- 새 실행이므로 run ID와 artifact 경로는 서로 다르다.

실행 시각과 duration은 비교하지 않는다. Model byte와 모든 예측 결과도 아직 비교하지 않는다. Day 10에서는 원본 `20260812T004148291974Z-e2bef42e`와 재현 run `20260813T050336148461Z-c104baf9`가 현재 기준을 모두 통과했다.

같은 config는 재현에 필요하지만 항상 충분하지는 않다. Data, code commit, dependency, Docker image digest, hardware와 비결정적 연산도 결과에 영향을 줄 수 있다. 현재 run record는 이 환경 정보를 모두 저장하지 않으므로 이번 검증은 남아 있던 같은 Day 9 image와 같은 설정에서 metric이 반복됐다는 증거다.

### Day 14 MLOps와 Agent 실행 흐름 통합

Day 14에서는 학습 흐름과 Agent Tool 흐름이 별개의 프로그램이 아니라 같은 학습 기능을 서로 다른 진입점에서 사용하는 구조임을 정리했다.

```text
사용자 직접 실행 ── run_job.py ─────────────┐
                                            ├── 학습 → run log → model artifact
Agent Tool 요청 ── tool_runner.py           │
                       └── run_train_job ───┘
                       └── 모든 요청 → audit log
```

| 실행 방법 | 남는 운영 증거 |
|---|---|
| `python src/run_job.py --config configs/train.yaml` | run log와 model artifact |
| `python src/tool_runner.py --tool echo --input "hello"` | Tool audit log |
| `python src/tool_runner.py --tool run_train_job` | Tool audit log, run log와 model artifact |

`run_train_job`은 별도의 학습 구현을 복제하지 않고 `run_job.py`의 운영 함수를 호출한다. 따라서 직접 실행과 Agent 요청이 같은 설정 검증, 실패 처리, run log와 artifact 저장 규칙을 공유한다.

현재 두 log에는 공통 `request_id` 또는 audit record의 `run_id`가 없다. `run_train_job`이 두 log를 모두 남긴다는 기능 연결은 확인할 수 있지만, 특정 audit record와 특정 run record의 관계는 가까운 실행 시각으로 추정해야 한다. 운영 추적성을 높이려면 이후 공통 상관관계 ID가 필요하다.

## 알아둘 명령어나 코드

```bash
python src/train_job.py --config configs/train.yaml
python src/run_job.py --config configs/train.yaml
python src/list_runs.py --limit 5
python src/list_runs.py --experiment iris-baseline --limit 3
python src/compare_runs.py --source-run 20260812T004148291974Z-e2bef42e --candidate-run 20260813T050336148461Z-c104baf9
find artifacts -maxdepth 2 -type f -name 'model.pkl' -printf '%p %s bytes\n' | sort
```

첫 번째 명령은 학습과 artifact 저장을 직접 실행한다. 두 번째 명령은 같은 작업을 실행하고 성공 결과를 `logs/runs.jsonl`에도 추가하는 운영 진입점이다. 다음 두 명령은 전체 또는 지정한 experiment의 최근 run을 읽기만 한다. `compare_runs.py`는 두 success run의 현재 재현 기준을 읽기 전용으로 검사한다. 마지막 명령은 저장된 model 경로와 크기를 읽기만 한다.

## 흔한 실패 사례

- 실패: 이전 실행을 재현할 수 없음
- 증상: 과거 metric은 있지만 사용한 config 또는 artifact 경로가 없음
- 확인할 것: `logs/runs.jsonl`, `configs/train.yaml`, `artifacts/`
- 복구 방법: 각 실행의 config, metric, artifact 경로를 함께 저장함
- 실패: 설정 파일을 찾을 수 없거나 설정값이 허용 범위를 벗어남
- 증상: 학습이 시작되지 않고 `FileNotFoundError` 또는 `ValueError`가 기록됨
- 확인할 것: `config_path`, YAML의 필수 항목, 자료형과 값 범위
- 복구 방법: 존재하는 YAML 경로를 지정하고 `config_loader.py`가 요구하는 조건에 맞게 값을 수정한 뒤 다시 실행함
- 실패: `python src/train_job.py`를 실행했지만 아무 출력이 없음
- 증상: 오류 없이 바로 종료되지만 terminal에 metrics가 나타나지 않음
- 확인할 것: `main()`과 `if __name__ == "__main__":` 진입점이 있는지 확인
- 복구 방법: 직접 실행할 때 `main()`이 호출되도록 진입점을 연결함
- 실패: 기존 model artifact가 덮어써짐
- 증상: 이전 실행의 model 파일이 사라지고 최신 결과만 남음
- 확인할 것: run ID가 매번 새로 생성되는지, `artifacts/{run_id}/` 구조인지 확인
- 복구 방법: 실행별 고유 run ID 디렉터리를 만들고 기존 디렉터리가 있으면 저장을 거부함
- 실패: experiment 이름을 개별 model version처럼 사용함
- 증상: 같은 이름의 여러 model 중 어느 결과를 뜻하는지 구분할 수 없음
- 확인할 것: `experiment_name`뿐 아니라 각 record의 `run_id`와 `artifact_path`
- 복구 방법: experiment 이름은 grouping에 사용하고 개별 실행과 model은 run ID로 식별함
- 실패: config는 같지만 metric이 다름
- 증상: `metrics_match: false`와 exit code `1`이 반환됨
- 확인할 것: data, code commit, dependency, Docker image, random seed와 hardware 차이
- 복구 방법: 원본 run의 config뿐 아니라 실행환경 version을 확인하고 차이를 제거한 뒤 새 run으로 다시 검증함

## 실용적인 이해

팀이 모델 결과의 생성 과정을 추적할 수 없다면 그 결과는 운영에 사용하기 어렵다. 이 프로젝트에서는 학습마다 파라미터, metric, 상태, artifact 경로를 연결하여 결과를 비교하고 재현한다.

Python 파일에 함수를 정의하는 것만으로는 함수가 실행되지 않는다. `python src/train_job.py`처럼 파일을 직접 실행했을 때 학습을 시작하려면 `if __name__ == "__main__":` 진입점에서 `main()`을 호출해야 한다. Day 2에서는 이 진입점이 `train_model()`을 실행하고 metrics를 JSON 한 줄로 출력한다.

run ID는 model 파일 이름만으로 알 수 없는 실행 단위를 표현한다. 현재 같은 run ID가 run log의 설정·metric·상태·artifact 경로를 연결하므로 어떤 조건이 해당 model을 만들었는지 추적할 수 있다.

Experiment tracking은 단순히 실행 횟수를 세는 기능이 아니다. 어떤 조건으로 실행했고 어떤 metric이 나왔으며 어느 model 파일을 만들었는지를 같은 record로 연결해야 비교와 추적이 가능하다. `iris-baseline`이라는 이름이 같아도 run ID가 다르면 별도의 실행과 model이다.

실제 MLOps에서도 run 비교 기능은 필요하지만 파일 이름이 `compare_runs.py`일 필요는 없다. MLflow나 다른 experiment tracking platform이 parameter, metric과 artifact 비교를 대신할 수 있다. 이 프로젝트는 외부 platform 없이 그 핵심 동작을 이해하기 위해 작은 Python script로 직접 구현했다.

설정을 코드 밖으로 옮기면 Python source를 수정하지 않고 실험 조건을 바꿀 수 있다. 다만 YAML이라는 형식만 사용한다고 안전해지는 것은 아니다. 잘못된 비율이나 오타 난 항목으로 비싼 학습을 시작하지 않도록 실행 경계에서 값을 검증해야 한다.

저장소는 소스 파일과 실행 중 생성되는 데이터를 분리한다. `logs/`와 `artifacts/`는 프로젝트 구조에 필요하지만 내부 실행 결과는 Git에 커밋하지 않는다. Git은 빈 디렉터리를 추적하지 않으므로 `.gitkeep` placeholder를 두고, `.gitignore`로 실제 생성 파일을 제외한다. `.gitkeep`은 Git의 공식 기능이 아니라 관례적인 파일 이름이다.

## Codex Q&A 기록

- 질문: `.gitkeep`은 무엇이고 왜 사용하는가?
  답변: Git은 빈 디렉터리를 추적하지 않는다. `.gitkeep` placeholder는 clone 후에도 `logs/`와 `artifacts/` 구조가 존재하게 하며, 실제 로그와 모델 파일은 `.gitignore`로 제외할 수 있게 한다.
- 질문: `configs/`, `src/`, `logs/`, `artifacts/`는 각각 어떤 용도인가?
  답변: `configs/`는 실행 설정, `src/`는 실행 코드, `logs/`는 실행 과정과 상태 기록, `artifacts/`는 학습으로 생성된 모델과 결과물을 담당한다. 설정과 코드가 실행되면 로그와 artifact가 만들어지는 흐름이다.
- 질문: `python src/train_job.py`를 실행했는데 왜 출력되는 것이 없는가?
  답변: 당시에는 함수만 정의되어 있고 함수를 호출하는 CLI 진입점이 없었다. `main()`과 `if __name__ == "__main__":`를 추가한 뒤 같은 명령으로 학습과 JSON 출력이 실행된다.
- 질문: Day 7 architecture 문서는 Day 1~6 내용을 정리한 것인가?
  답변: 맞다. 다만 날짜별 작업을 단순 복사한 것이 아니라, 첫 주에 만든 학습·저장·로그·실패 처리·Docker 기능이 현재 하나의 시스템으로 어떻게 연결되는지 구성요소 책임과 흐름 중심으로 정리한 문서다.
- 질문: `config_loader.py`는 `train.yaml`의 config 값을 불러오면서 조건에 맞는지도 확인하는가?
  답변: 맞다. YAML을 읽고 필수·추가 항목, 자료형과 값 범위를 검사한 뒤 검증된 설정만 반환한다. 조건에 맞지 않으면 학습을 시작하기 전에 오류를 발생시킨다.
- 질문: `experiment_name`은 학습 식별 이름인가?
  답변: 같은 목적의 학습 실행들을 묶는 식별 이름이다. 개별 실행 한 번은 고유한 `run_id`로 구분한다. 하나의 `experiment_name` 아래 여러 run과 model artifact가 존재할 수 있다.
- 질문: Day 10은 config 이전의 과거 run을 새 schema로 수정하는 작업인가?
  답변: 아니다. Config가 기록된 기존 success run은 그대로 보존하고 같은 조건으로 새 run을 만든 뒤 두 결과를 비교한다. Config가 없는 더 오래된 run은 현재 정보만으로 정확하게 재현하기 어렵다.
- 질문: 같은 config라면 같은 결과가 나와야 하는가?
  답변: 현재의 결정적인 Iris 학습에서는 같은 결과를 기대하지만 일반적으로는 data, code, dependency, hardware와 비결정적 연산도 영향을 준다. 같은 config는 필요하지만 완전 재현의 충분조건은 아니다.
- 질문: `compare_runs.py`가 실제 MLOps에서도 필요한가?
  답변: 이 파일 자체는 표준 필수 파일이 아니다. 다만 run의 parameter, metric과 artifact를 비교하는 기능은 MLOps의 핵심이며 실제 환경에서는 MLflow 같은 platform이 대신할 수 있다.
- 질문: Day 14는 전반적으로 지금까지 만든 기능을 검수하는 날인가?
  답변: 맞다. 새 핵심 기능을 늘리기보다 학습, model 저장, run log, Agent Tool, timeout과 audit log가 하나의 운영 흐름으로 연결되는지 확인하고 README와 architecture를 현재 상태에 맞게 정리하는 날이다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [프로젝트 README](../../README.md)
- [Architecture](../architecture.md)
- [Runbook](../runbook.md)
- [로깅과 모니터링](logging-monitoring.md)
