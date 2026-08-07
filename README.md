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

학습과 artifact 저장만 직접 확인하려면 프로젝트 root에서 다음 명령을 실행한다.

```bash
python src/train_job.py
```

정상 실행되면 다음과 같은 JSON 한 줄이 출력된다.

```json
{"artifact_path": "artifacts/20260805T043140293097Z-eed6e816/model.pkl", "metrics": {"accuracy": 0.9666666666666667, "test_samples": 30, "train_samples": 120}, "run_id": "20260805T043140293097Z-eed6e816"}
```

run ID는 실행할 때마다 달라진다. 실제 운영 흐름에서는 아래의 `src/run_job.py`를 사용해 학습 결과를 run log와 함께 기록한다.

## 모델 Artifact 저장

각 학습 실행은 UTC 생성 시각과 UUID suffix를 조합한 run ID를 사용한다. 학습된 model은 다른 실행 결과를 덮어쓰지 않도록 다음 경로에 저장한다.

```text
artifacts/{run_id}/model.pkl
```

저장된 model 파일은 다음 명령으로 확인한다.

```bash
find artifacts -maxdepth 2 -type f -name 'model.pkl' -printf '%p %s bytes\n' | sort
```

이 명령은 파일을 변경하지 않고 artifact 경로와 크기를 출력한다. `artifacts/`의 실행 결과는 `.gitignore`에 따라 Git에서 제외된다. `model.pkl`은 Python pickle 형식이므로 신뢰할 수 없는 외부 파일을 불러오지 않는다.

## 실험 추적

학습 파라미터는 `configs/` 아래에서 관리한다. 실행별로 파라미터, metric, 상태, artifact 경로를 연결하여 실험을 비교하고 재현할 수 있게 한다.

## Agent 도구 실행기

도구 실행기는 allowlist에 정의된 도구만 허용한다. 등록되지 않은 도구는 거부하고, 허용된 실행에도 timeout을 적용한다.

## 로그와 감사 기록

실행 중 생성되는 운영 기록은 JSON Lines(JSONL) 형식을 사용한다.

- `logs/runs.jsonl`: 학습 실행 기록
- `logs/audit.jsonl`: Agent 도구 호출 기록

성공한 학습 실행을 기록하려면 프로젝트 root에서 다음 명령을 실행한다.

```bash
python src/run_job.py
```

이 명령은 새로운 model artifact를 생성하고 `logs/runs.jsonl` 끝에 실행 기록 한 줄을 추가한다. 성공과 실패 기록은 공통으로 `run_id`, `status`, `started_at`, `ended_at`, `duration_seconds`, `metrics`, `artifact_path`, `error_type`, `error_message`, `traceback`을 포함한다. 성공하면 metric과 artifact 경로가 채워지고 error field는 `null`이 된다.

실패 처리 경로는 다음 명령으로 안전하게 재현한다.

```bash
python src/run_job.py --fail
echo $?
tail -n 1 logs/runs.jsonl
```

`--fail`은 실제 환경을 손상시키지 않고 검증용 `RuntimeError`를 발생시킨다. 이 실행은 model artifact를 만들지 않고 `failed` record를 한 줄 추가하며 exit code `1`을 반환한다. 바로 이어 실행한 `echo $?`가 `1`을 출력하고 마지막 log에 오류 종류, 메시지, traceback이 있으면 예상대로 처리된 것이다.

최근 실행 기록은 다음 명령으로 확인한다.

```bash
tail -n 3 logs/runs.jsonl
```

`tail` 명령은 로그를 변경하지 않고 마지막 세 줄을 출력한다. JSONL은 한 실행을 독립된 JSON 한 줄로 저장하므로 기존 전체 내용을 다시 쓰지 않고 새 기록을 추가할 수 있다.

생성된 로그 파일은 Git에서 제외한다. 빈 디렉터리는 `.gitkeep` placeholder를 사용해 저장소에 유지한다.

## 장애 시나리오

학습 실패, artifact 저장 실패, 설정 오류, 도구 timeout, 허용되지 않은 도구 요청, 과도한 로그 증가를 확인하고 복구하는 방법을 문서화한다.

현재 구현한 학습 실패 재현과 복구 확인 절차는 [장애 시나리오](docs/failure-scenarios.md)에서 확인할 수 있다.

## 보안과 백업 고려사항

- 실제 비밀정보를 Git에 저장하지 않는다.
- 안전한 예시 설정만 커밋한다.
- 로그에 민감한 운영 정보가 포함될 수 있다고 가정한다.
- artifact가 쌓이기 전에 보존 기간과 백업 절차를 정한다.
- 도구 실행기에는 allowlist에 필요한 최소 권한만 부여한다.

## 기술 위키와 작업 기록

프로젝트에 필요한 개념은 [기술 위키](docs/wiki/README.md)에 정리한다. 날짜별 구현 기록은 [작업 일지 인덱스](docs/work-logs/README.md)에서 확인할 수 있다. 전체 방향은 [프로젝트 계획](docs/project-plan.md), 일별 진행 방식은 [일별 작업 흐름](docs/daily-codex-workflow.md)을 참고한다.
