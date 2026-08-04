# Mini AI Ops Lab

## 프로젝트 소개

Mini AI Ops Lab은 AI 작업을 운영하는 방법을 배우기 위한 작고 이해하기 쉬운 시스템이다. 학습 작업을 실행하고, 성공과 실패 결과를 기록하며, 모델 artifact를 저장한다. 또한 Agent의 도구 호출을 allowlist, timeout, audit log로 통제한다.

이 프로젝트는 모델 정확도보다 추적과 복구 가능성을 중요하게 생각한다. 어떤 설정으로 실행했는지, 성공했는지, 어떤 metric과 artifact가 생성됐는지를 나중에도 확인할 수 있어야 한다.

## 아키텍처

구현할 전체 운영 흐름은 다음과 같다.

```text
학습 설정 -> 작업 실행기 -> 학습 작업
                   |-> JSONL 실행 및 실패 로그
                   `-> 실행별 모델 artifact

도구 요청 -> allowlist와 입력 검증 -> 통제된 도구 실행
                                      `-> JSONL audit log
```

매일 구현과 검증이 가능한 작은 단위로 기능을 추가하며, 각 작업일에는 코드 또는 문서 형태의 증거를 남긴다.

## 주요 기능

구현할 핵심 기능은 다음과 같다.

- 명령줄 기반 학습 작업 실행
- 설정 파일 기반 실험 추적
- 실행별 모델 artifact 저장
- 성공 및 실패 structured log
- allowlist 기반 Agent 도구 실행
- 도구 timeout 및 audit log
- 운영 runbook, 장애 시나리오, 보안·백업 체크리스트
- 프로젝트 내부 기술 위키

## 시작 방법

Day 1에서는 프로젝트 기본 구조를 준비했고, Day 2에서는 명령줄에서 실행할 수 있는 기본 학습 작업을 추가했다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`.env`, 실행 중 생성된 로그, 모델 artifact는 Git에 커밋하지 않는다. 안전한 설정 예시는 `.env.example`을 사용한다.

## 학습 작업 관리

기본 학습 작업은 scikit-learn 내장 Iris dataset을 학습용 80%, 검증용 20%로 나눈 뒤 `LogisticRegression` 모델을 학습하고 accuracy를 계산한다.

프로젝트 root에서 다음 명령을 실행한다.

```bash
python src/train_job.py
```

정상 실행되면 다음과 같은 JSON 한 줄이 출력된다.

```json
{"accuracy": 0.9666666666666667, "test_samples": 30, "train_samples": 120}
```

현재 단계에서는 CPU와 memory에서만 모델을 학습하며 파일을 생성하지 않는다. 고유한 run ID, 모델 artifact 저장, 성공·실패 상태와 run log는 이후 작업일에 추가한다.

## 실험 추적

학습 파라미터는 `configs/` 아래에서 관리한다. 실행별로 파라미터, metric, 상태, artifact 경로를 연결하여 실험을 비교하고 재현할 수 있게 한다.

## Agent 도구 실행기

도구 실행기는 allowlist에 정의된 도구만 허용한다. 등록되지 않은 도구는 거부하고, 허용된 실행에도 timeout을 적용한다.

## 로그와 감사 기록

실행 중 생성되는 운영 기록은 JSON Lines(JSONL) 형식을 사용한다.

- `logs/runs.jsonl`: 학습 실행과 실패 기록
- `logs/audit.jsonl`: Agent 도구 호출 기록

생성된 로그 파일은 Git에서 제외한다. 빈 디렉터리는 `.gitkeep` placeholder를 사용해 저장소에 유지한다.

## 장애 시나리오

학습 실패, artifact 저장 실패, 설정 오류, 도구 timeout, 허용되지 않은 도구 요청, 과도한 로그 증가를 확인하고 복구하는 방법을 문서화한다.

## 보안과 백업 고려사항

- 실제 비밀정보를 Git에 저장하지 않는다.
- 안전한 예시 설정만 커밋한다.
- 로그에 민감한 운영 정보가 포함될 수 있다고 가정한다.
- artifact가 쌓이기 전에 보존 기간과 백업 절차를 정한다.
- 도구 실행기에는 allowlist에 필요한 최소 권한만 부여한다.

## 기술 위키와 작업 기록

프로젝트에 필요한 개념은 [기술 위키](docs/wiki/README.md)에 정리한다. 날짜별 구현 기록은 [작업 일지 인덱스](docs/work-logs/README.md)에서 확인할 수 있다. 전체 방향은 [프로젝트 계획](docs/project-plan.md), 일별 진행 방식은 [일별 작업 흐름](docs/daily-codex-workflow.md)을 참고한다.
