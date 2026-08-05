# MLOps

## 짧은 정의

MLOps는 머신러닝 실험, 학습 실행, 모델, 로그, 배포 관련 artifact를 추적하고 재현할 수 있도록 운영하는 방식이다.

## 이 프로젝트에서 중요한 이유

Mini AI Ops Lab은 단순한 학습 스크립트를 운영 가능한 작업으로 발전시킨다. 모델 정확도만 보는 것이 아니라 어떤 config가 어떤 metric과 artifact를 만들었는지 나중에도 확인할 수 있어야 한다.

## 저장소에서 사용되는 위치

- `configs/train.yaml`
- `src/train_job.py`
- `src/run_job.py`
- `logs/runs.jsonl`
- `artifacts/`

### 프로젝트 디렉터리 역할

| 디렉터리 | 역할 | 앞으로 저장할 내용 |
|---|---|---|
| `configs/` | 코드 수정 없이 실행 방식을 바꾸는 설정 보관 | `train.yaml`, `tools.yaml` |
| `src/` | 프로젝트의 실제 동작을 구현하는 소스 코드 보관 | `train_job.py`, `run_job.py`, `tool_runner.py` |
| `logs/` | 실행 과정, 성공·실패 상태, Agent 도구 호출 기록 | `runs.jsonl`, `errors.jsonl`, `audit.jsonl` |
| `artifacts/` | 학습 실행이 만든 결과물 보관 | 실행별 `model.pkl`, 설정 사본, 결과 파일 |

전체 흐름은 다음과 같이 이해할 수 있다.

```text
configs/의 설정
       ↓
src/의 코드 실행
       ↓
├── logs/에 실행 기록
└── artifacts/에 실행 결과물
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

## 알아둘 명령어나 코드

```bash
python src/train_job.py
find artifacts -maxdepth 2 -type f -name 'model.pkl' -printf '%p %s bytes\n' | sort
```

첫 번째 명령은 모델을 학습하고 `artifacts/{run_id}/model.pkl`을 생성한 뒤 metrics와 경로를 JSON으로 출력한다. 두 번째 명령은 저장된 model 경로와 크기를 읽기만 한다. run log는 이후 작업일에 추가한다.

## 흔한 실패 사례

- 실패: 이전 실행을 재현할 수 없음
- 증상: 과거 metric은 있지만 사용한 config 또는 artifact 경로가 없음
- 확인할 것: `logs/runs.jsonl`, `configs/train.yaml`, `artifacts/`
- 복구 방법: 각 실행의 config, metric, artifact 경로를 함께 저장함
- 실패: `python src/train_job.py`를 실행했지만 아무 출력이 없음
- 증상: 오류 없이 바로 종료되지만 terminal에 metrics가 나타나지 않음
- 확인할 것: `main()`과 `if __name__ == "__main__":` 진입점이 있는지 확인
- 복구 방법: 직접 실행할 때 `main()`이 호출되도록 진입점을 연결함
- 실패: 기존 model artifact가 덮어써짐
- 증상: 이전 실행의 model 파일이 사라지고 최신 결과만 남음
- 확인할 것: run ID가 매번 새로 생성되는지, `artifacts/{run_id}/` 구조인지 확인
- 복구 방법: 실행별 고유 run ID 디렉터리를 만들고 기존 디렉터리가 있으면 저장을 거부함

## 실용적인 이해

팀이 모델 결과의 생성 과정을 추적할 수 없다면 그 결과는 운영에 사용하기 어렵다. 이 프로젝트에서는 학습마다 파라미터, metric, 상태, artifact 경로를 연결하여 결과를 비교하고 재현한다.

Python 파일에 함수를 정의하는 것만으로는 함수가 실행되지 않는다. `python src/train_job.py`처럼 파일을 직접 실행했을 때 학습을 시작하려면 `if __name__ == "__main__":` 진입점에서 `main()`을 호출해야 한다. Day 2에서는 이 진입점이 `train_model()`을 실행하고 metrics를 JSON 한 줄로 출력한다.

run ID는 model 파일 이름만으로 알 수 없는 실행 단위를 표현한다. 현재는 run ID와 artifact 경로만 연결했으며, 이후 같은 run ID를 run log와 config에도 기록하면 어떤 설정과 metric이 해당 model을 만들었는지 추적할 수 있다.

저장소는 소스 파일과 실행 중 생성되는 데이터를 분리한다. `logs/`와 `artifacts/`는 프로젝트 구조에 필요하지만 내부 실행 결과는 Git에 커밋하지 않는다. Git은 빈 디렉터리를 추적하지 않으므로 `.gitkeep` placeholder를 두고, `.gitignore`로 실제 생성 파일을 제외한다. `.gitkeep`은 Git의 공식 기능이 아니라 관례적인 파일 이름이다.

## Codex Q&A 기록

- 질문: `.gitkeep`은 무엇이고 왜 사용하는가?
  답변: Git은 빈 디렉터리를 추적하지 않는다. `.gitkeep` placeholder는 clone 후에도 `logs/`와 `artifacts/` 구조가 존재하게 하며, 실제 로그와 모델 파일은 `.gitignore`로 제외할 수 있게 한다.
- 질문: `configs/`, `src/`, `logs/`, `artifacts/`는 각각 어떤 용도인가?
  답변: `configs/`는 실행 설정, `src/`는 실행 코드, `logs/`는 실행 과정과 상태 기록, `artifacts/`는 학습으로 생성된 모델과 결과물을 담당한다. 설정과 코드가 실행되면 로그와 artifact가 만들어지는 흐름이다.
- 질문: `python src/train_job.py`를 실행했는데 왜 출력되는 것이 없는가?
  답변: 당시에는 함수만 정의되어 있고 함수를 호출하는 CLI 진입점이 없었다. `main()`과 `if __name__ == "__main__":`를 추가한 뒤 같은 명령으로 학습과 JSON 출력이 실행된다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [프로젝트 README](../../README.md)
- [로깅과 모니터링](logging-monitoring.md)
