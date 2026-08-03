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

## 알아둘 명령어나 코드

```bash
python src/run_job.py --config configs/train.yaml
tail -n 3 logs/runs.jsonl
find artifacts -maxdepth 2 -type f
```

## 흔한 실패 사례

- 실패: 이전 실행을 재현할 수 없음
- 증상: 과거 metric은 있지만 사용한 config 또는 artifact 경로가 없음
- 확인할 것: `logs/runs.jsonl`, `configs/train.yaml`, `artifacts/`
- 복구 방법: 각 실행의 config, metric, artifact 경로를 함께 저장함

## 실용적인 이해

팀이 모델 결과의 생성 과정을 추적할 수 없다면 그 결과는 운영에 사용하기 어렵다. 이 프로젝트에서는 학습마다 파라미터, metric, 상태, artifact 경로를 연결하여 결과를 비교하고 재현한다.

저장소는 소스 파일과 실행 중 생성되는 데이터를 분리한다. `logs/`와 `artifacts/`는 프로젝트 구조에 필요하지만 내부 실행 결과는 Git에 커밋하지 않는다. Git은 빈 디렉터리를 추적하지 않으므로 `.gitkeep` placeholder를 두고, `.gitignore`로 실제 생성 파일을 제외한다. `.gitkeep`은 Git의 공식 기능이 아니라 관례적인 파일 이름이다.

## Codex Q&A 기록

- 질문: `.gitkeep`은 무엇이고 왜 사용하는가?
  답변: Git은 빈 디렉터리를 추적하지 않는다. `.gitkeep` placeholder는 clone 후에도 `logs/`와 `artifacts/` 구조가 존재하게 하며, 실제 로그와 모델 파일은 `.gitignore`로 제외할 수 있게 한다.
- 질문: `configs/`, `src/`, `logs/`, `artifacts/`는 각각 어떤 용도인가?
  답변: `configs/`는 실행 설정, `src/`는 실행 코드, `logs/`는 실행 과정과 상태 기록, `artifacts/`는 학습으로 생성된 모델과 결과물을 담당한다. 설정과 코드가 실행되면 로그와 artifact가 만들어지는 흐름이다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [프로젝트 README](../../README.md)
- [로깅과 모니터링](logging-monitoring.md)
