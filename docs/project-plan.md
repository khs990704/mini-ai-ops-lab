# Project Plan

## 목적

이 문서는 Mini AI Ops Lab 프로젝트의 실행 계획이다. WSL의 프로젝트 폴더 안에서 직접 참조할 수 있도록 작성한 self-contained 문서다.

지금 단계의 목표는 실제로 작은 AI 운영 시스템을 만들면서 필요한 개념을 익히는 것이다.

핵심 전략:

> 작은 AI 운영 시스템을 직접 만들고, 그 과정에서 MLOps, Agent 실행환경, 로그, 장애 대응, 권한, 백업을 학습한다.

지금 알고 있는 것이 부족하다는 전제를 두고, 어려운 기술을 한 번에 다루지 않는다. 대신 "기능 구현 -> 로그 남기기 -> 실패 상황 만들기 -> 운영 문서 작성 -> 기술 위키 정리" 순서로 진행한다.

## 만들 프로젝트

프로젝트 이름:

> Mini AI Ops Lab

실제 프로젝트 폴더:

- `mini-ai-ops-lab/`
- Codex 작업 지침: `AGENTS.md`
- 프로젝트 계획: `docs/project-plan.md`
- 일별 실행 계획: `docs/daily-codex-workflow.md`
- 일별 작업 기록: `docs/daily-log.md`
- 기술 위키: `docs/wiki/`

이 프로젝트는 모델 성능을 높이는 프로젝트가 아니다. 학습 작업과 Agent 도구 실행을 운영 가능한 형태로 관리하는 프로젝트다.

### 한 문장 설명

학습 작업을 실행하고, 실행 결과와 실패 로그를 기록하며, Agent 도구 호출을 제한된 환경에서 실행하고, 운영자가 확인할 수 있는 문서를 남기는 미니 운영 시스템.

## 프로젝트에서 다룰 영역


| 영역 | 프로젝트에서 만들 것 | 학습할 내용 |
|---|---|---|
| 학습 작업 실행 | 명령어로 실행되는 training job | Python script, job 실행 흐름 |
| 실험 기록 | config, metric, artifact 경로 저장 | MLOps, 재현성, 실험 비교 |
| artifact 관리 | run id별 모델 파일 저장 | 결과물 추적, 저장 경로 설계 |
| 로그 | JSONL 기반 run log와 error log | structured logging, 장애 추적 |
| Agent 실행환경 | allowlist 기반 tool runner | tool call, 입력 검증, 실행 제한 |
| audit log | tool 실행 이력 저장 | 감사 가능성, traceability |
| 장애 대응 | 실패 시나리오와 복구 절차 | 원인 분석, runbook |
| 보안/백업 | secret, 권한, 백업 체크리스트 | 최소 권한, 복구 절차 |
| 기술 위키 | 개념별 짧은 문서 | 구현하면서 개념 정리 |

## 최종 결과물

필수 결과물:

- GitHub 저장소 또는 로컬 프로젝트 폴더
- `README.md`
- `docs/architecture.md`
- `docs/runbook.md`
- `docs/failure-scenarios.md`
- `docs/security-backup-checklist.md`
- `docs/wiki/`
- 실행 로그 예시
- 실험 기록 예시
- Agent tool call audit log 예시

있으면 좋은 결과물:

- Docker Compose 실행
- 간단한 FastAPI API
- MLflow 연동
- Prometheus metric endpoint
- 테스트 코드 일부

## 프로젝트 범위

### 반드시 할 것

1. 학습 작업 실행
2. 실행 결과 기록
3. 실패 로그 기록
4. 모델 파일 저장
5. Agent tool runner 구현
6. tool 실행 timeout 처리
7. audit log 저장
8. 장애 대응 문서 작성
9. 백업/권한 체크리스트 작성
10. 기술 위키 갱신

### 하지 않을 것

- 모델 정확도 개선에 많은 시간 쓰기
- 대시보드 UI를 크게 만들기
- Kubernetes를 깊게 파기
- GPU 서버를 실제로 구해야만 한다고 생각하기
- LLM Agent를 복잡하게 만들기
- 모든 기술을 완벽히 이해한 뒤 시작하기

이 프로젝트에서는 "얼마나 큰 시스템인가"보다 "작게라도 운영 가능한 흐름이 있는가"가 더 중요하다.

## 기술 스택

초기 난이도를 낮추기 위해 다음 조합을 추천한다.


| 영역 | 추천 기술 | 이유 |
|---|---|---|
| 언어 | Python | MLOps, Agent, 운영 스크립트에 모두 적합 |
| API | FastAPI | 필요하면 간단히 API화 가능 |
| 실행환경 | Docker, Docker Compose | 재현 가능한 환경을 만들기 좋음 |
| 실험 기록 | JSON 파일, 이후 MLflow 선택 | 처음에는 단순한 로그 기반으로 시작 |
| 로그 | Python logging, JSONL | 구현이 쉽고 구조화된 로그를 만들기 좋음 |
| 모델 | scikit-learn 또는 작은 PyTorch 예제 | 모델 자체보다 운영 구조가 목적 |
| 설정 | YAML 또는 `.env` | 운영 환경 분리 설명 가능 |
| 문서 | Markdown | 프로젝트 내부 문서와 위키에 적합 |

처음부터 MLflow, FastAPI, Docker를 모두 붙이려고 하지 않는다. 순서는 JSON 로그 기반으로 먼저 완성하고, 시간이 남으면 MLflow와 API를 붙인다.

## 폴더 구조

추천 구조:

```text
mini-ai-ops-lab/
  README.md
  AGENTS.md
  docker-compose.yml
  Dockerfile
  requirements.txt
  .env.example
  configs/
    train.yaml
    tools.yaml
  src/
    train_job.py
    run_job.py
    tool_runner.py
    audit_logger.py
    storage.py
  artifacts/
    .gitkeep
  logs/
    .gitkeep
  docs/
    project-plan.md
    daily-codex-workflow.md
    daily-log.md
    architecture.md
    runbook.md
    failure-scenarios.md
    security-backup-checklist.md
    wiki/
      README.md
      template.md
```

GitHub에는 실제 secret이나 큰 모델 파일을 올리지 않는다. `logs/`와 `artifacts/`는 예시 파일만 올리거나 `.gitignore`로 관리한다.

## 단계별 구현 계획

### 1단계: 학습 작업 실행기

목표:

Python으로 간단한 학습 작업을 실행하고, 실행 결과를 파일로 남긴다.

할 일:

- `src/train_job.py` 작성
- scikit-learn으로 간단한 분류 모델 학습
- accuracy 같은 metric 기록
- 모델 파일을 `artifacts/`에 저장
- 실행마다 `run_id` 생성

완료 기준:

- 명령어 한 줄로 학습이 실행된다.
- 실행 결과가 `logs/runs.jsonl`에 남는다.
- 모델 파일이 `artifacts/{run_id}/model.pkl` 형태로 저장된다.

### 2단계: 실행 로그와 실패 로그

목표:

성공한 작업뿐 아니라 실패한 작업도 추적할 수 있게 만든다.

할 일:

- `src/run_job.py` 작성
- job status를 `running/success/failed`로 기록
- 시작 시간, 종료 시간, 실행 시간 기록
- exception 발생 시 에러 메시지와 stack trace 저장
- 실패 예시를 일부러 만들어 로그로 남김

완료 기준:

- 성공 로그와 실패 로그 예시가 모두 있다.
- README에 "실패한 작업 확인 방법"이 적혀 있다.

### 3단계: 실험 기록

목표:

실험을 다시 재현할 수 있게 파라미터와 결과를 같이 저장한다.

할 일:

- `configs/train.yaml` 작성
- 학습 파라미터 기록
- config 파일 내용을 run log에 함께 저장
- 같은 config로 재실행하는 방법 문서화

완료 기준:

- 어떤 파라미터로 어떤 결과가 나왔는지 확인할 수 있다.
- README 또는 runbook에 "재현 실행 방법"이 있다.

### 4단계: Agent Tool Runner

목표:

Agent가 아무 명령이나 실행하지 못하도록 허용된 tool만 실행하는 구조를 만든다.

할 일:

- `configs/tools.yaml`에 허용 tool 목록 작성
- `src/tool_runner.py` 작성
- tool name과 input을 받아 실행
- 허용되지 않은 tool은 거절
- timeout 설정
- stdout, stderr, status, duration 기록

처음에 만들 tool:

- `echo`
- `read_log_summary`
- `list_artifacts`
- `run_train_job`

완료 기준:

- 허용 tool은 실행된다.
- 허용되지 않은 tool은 차단된다.
- 모든 tool call이 `logs/audit.jsonl`에 기록된다.

### 5단계: 운영 문서

목표:

프로젝트를 "코드"에서 "운영 가능한 시스템"으로 정리한다.

작성할 문서:

- `docs/architecture.md`: 전체 구조 설명
- `docs/runbook.md`: 실행, 확인, 복구 절차
- `docs/failure-scenarios.md`: 장애 시나리오와 대응
- `docs/security-backup-checklist.md`: secret, 권한, 백업 점검
- `docs/wiki/`: 구현 중 배운 기술 개념 정리

반드시 넣을 장애 시나리오:

1. 학습 작업이 실패하는 경우
2. 모델 artifact 저장에 실패하는 경우
3. tool call이 timeout 되는 경우
4. 허용되지 않은 tool 실행 요청이 들어오는 경우
5. 로그 파일이 너무 커지는 경우

완료 기준:

- 문서만 보고 프로젝트를 실행할 수 있다.
- 실패 상황에서 어떤 로그를 봐야 하는지 알 수 있다.
- 기술 위키가 구현 내용과 연결된다.

## 3주 집중 일정

앱 런칭 프로젝트를 병행한다는 전제로, Mini AI Ops Lab은 하루 1.5~2시간을 기본으로 잡는다. 코딩테스트는 이 기간의 주력 루틴에서 제외한다. 지금은 프로젝트 구현과 학습 기록이 더 중요하다.

세부 Day별 계획은 `docs/daily-codex-workflow.md`를 따른다.

## 일일 루틴

평일 루틴:


| 순서 | 시간 | 할 일 |
|---|---|---|
| 1 | 60~90분 | 프로젝트 구현 |
| 2 | 30~40분 | README, runbook, 장애 문서 중 필요한 것 갱신 |
| 3 | 20분 | 오늘 사용한 개념을 `docs/wiki/`에 정리 |
| 4 | 남는 시간 | 앱 런칭 프로젝트 진행 |

주말 루틴:


| 순서 | 시간 | 할 일 |
|---|---|---|
| 1 | 2~3시간 | 프로젝트 막힌 구현 해결 |
| 2 | 1시간 | 문서와 로그 예시 정리 |
| 3 | 30분 | 기술 위키 보강 |
| 4 | 남는 시간 | 앱 런칭 프로젝트 핵심 작업 |

앱 런칭 프로젝트도 완전히 별개로 보지 않는다. 앱에서 발생하는 배포, 로그, 오류, 환경변수, 백업, 권한 문제는 이 프로젝트의 운영 관점 학습과 연결해서 생각한다.

## 매일 기록할 것

매일 작업 후 10분 안에 `docs/daily-log.md`에 아래 형식으로 기록한다.

```text
날짜:
오늘 만든 것:
실행한 명령:
검증 결과:
막힌 문제:
확인한 로그/에러:
해결 방법 또는 다음 결정:
운영 관점에서 배운 점:
갱신한 기술 위키:
다음 작업:
```

예시:

```text
날짜: 2026-08-03
오늘 만든 것: 학습 작업 실행 후 run_id와 metric을 JSONL 로그로 저장
실행한 명령: python src/run_job.py
검증 결과: logs/runs.jsonl에 success 로그가 추가됨
막힌 문제: artifact 저장 경로가 없을 때 FileNotFoundError 발생
확인한 로그/에러: artifacts 디렉터리 미생성으로 저장 실패
해결 방법 또는 다음 결정: 실행 시작 시 run_id별 artifact 디렉터리 생성 로직 추가
운영 관점에서 배운 점: 작업 실행 전 필요한 디렉터리와 권한을 사전 점검해야 함
갱신한 기술 위키: docs/wiki/logging-monitoring.md
다음 작업: 실패 로그와 복구 절차 작성
```

## README 목차

README는 아래 순서로 작성한다.

```text
# Mini AI Ops Lab

## Overview
## Architecture
## Features
## Quick Start
## Training Job Management
## Experiment Tracking
## Agent Tool Runner
## Logging and Audit
## Failure Scenarios
## Security and Backup Considerations
## Technical Wiki
```

README에서 가장 중요한 것은 기능 목록보다 운영 흐름이다.

강조할 내용:

- 학습 작업을 실행 가능한 코드에서 운영 가능한 job으로 바꾸었다.
- 실패 로그와 실행 상태를 남겨 원인 추적이 가능하게 했다.
- Agent tool call은 allowlist, timeout, audit log를 기준으로 통제했다.
- artifact와 config를 함께 기록해 실험 재현성을 확보했다.
- 운영 문서와 장애 대응 시나리오를 함께 작성했다.
