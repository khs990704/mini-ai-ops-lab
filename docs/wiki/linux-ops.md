# Linux 운영

## 짧은 정의

Linux 운영은 Linux 시스템에서 process, 파일, 로그, disk 사용량, 권한, 실행 상태를 확인하고 관리하는 일이다.

## 이 프로젝트에서 중요한 이유

이 프로젝트는 WSL에서 개발되며 작은 운영 시스템처럼 동작해야 한다. 생성된 로그와 artifact, 실행 중인 process, 파일 권한을 Linux 명령으로 확인할 수 있어야 한다.

## 저장소에서 사용되는 위치

- `logs/`
- `artifacts/`
- `src/run_job.py`
- `docs/runbook.md`
- 검증에 사용하는 shell 명령

### Day 16 운영 Runbook

Runbook은 기능을 새로 구현하는 code가 아니라 운영자가 기존 기능을 올바른 순서로 사용하는 절차서다.

```text
환경·설정 점검
      ↓
학습 또는 Tool 실행
      ↓
run·audit log와 model 확인
      ↓
필요하면 이전 run 재현
      ↓
장애 원인 확인과 새 실행으로 복구
      ↓
삭제 전 사용량과 정확한 대상 확인
```

운영 명령은 결과를 읽기만 하는지, log·artifact·Docker 상태를 바꾸는지 먼저 구분한다.

| 명령 유형 | 예 | 상태 변화 |
|---|---|---|
| 사전 점검 | Python import, config loader, `docker image inspect` | 없음 |
| 직접 학습 | `python src/run_job.py` | run log, 성공 시 model 추가 |
| Tool 요청 | `python src/tool_runner.py` | audit log 추가, 쓰기 Tool은 run과 model도 추가 |
| 결과 확인 | `list_runs.py`, `tail`, `find`, `du` | 없음 |
| Docker smoke test | `docker run --rm`과 host mount 없음 | Container 내부 결과는 종료 시 제거됨 |

`src/config_loader.py`는 import용 module이고 직접 실행하는 `main()`이 없다. 따라서 `python src/config_loader.py --config ...`는 오류 없이 끝나도 loader 함수를 호출하거나 결과를 출력하지 않는다. Runbook에서는 다음처럼 실제 함수를 호출한다.

```bash
python -c "import json; from src.config_loader import load_train_config; print(json.dumps(load_train_config('configs/train.yaml'), ensure_ascii=False, indent=2, sort_keys=True))"
```

안전한 정리는 오래되거나 종료됐다는 이유만으로 삭제하는 일이 아니다. `docker ps -a`에는 다른 project container도 함께 나오므로 소유 project와 보존할 결과를 확인해야 한다. Log와 artifact도 run 추적과 장애 증거일 수 있어 backup·retention 기준 없이 자동 삭제하지 않는다.

## 알아둘 명령어나 코드

```bash
pwd
ls -la
find artifacts -maxdepth 2 -type f
tail -n 5 logs/runs.jsonl
du -sh logs artifacts
```

Python에서 로그 파일의 부모 디렉터리를 준비하는 코드는 다음과 같다.

```python
log_path.parent.mkdir(parents=True, exist_ok=True)
```

`log_path.parent`는 파일 경로에서 부모 디렉터리를 선택한다. `parents=True`는 필요한 상위 디렉터리도 만들고, `exist_ok=True`는 디렉터리가 이미 있을 때 오류 없이 계속하게 한다.

## 흔한 실패 사례

- 실패: 출력 파일을 찾을 수 없음
- 증상: 명령은 실행됐지만 로그 또는 artifact가 생성되지 않음
- 확인할 것: 현재 작업 디렉터리, 상대 경로, 쓰기 권한
- 복구 방법: 프로젝트 root에서 실행하고 필요한 디렉터리가 존재하는지 확인함
- 실패: Import용 Python module을 실행했으므로 설정이 검증됐다고 판단함
- 증상: Exit code는 `0`이지만 검증 결과나 출력이 없음
- 확인할 것: 파일에 `main()` 진입점이 있는지, 실제 loader 함수를 호출했는지
- 복구 방법: Runbook의 함수 호출 명령을 사용하거나 해당 module을 사용하는 운영 진입점을 실행함

## 실용적인 이해

운영 작업에서는 코드만 읽는 것이 아니라 실제 실행환경에서 관찰 가능한 증거를 확인해야 한다. 이 프로젝트는 Linux 명령을 사용해 로그, artifact, 경로, 파일 크기를 확인하고 장애 원인을 좁힌다.

`Path("logs/runs.jsonl")`은 현재 작업 디렉터리를 기준으로 해석되는 상대 경로다. 따라서 프로젝트가 기대하는 `logs/`에 기록하려면 프로젝트 root에서 명령을 실행한다. 부모 디렉터리를 먼저 만든 뒤 파일을 append mode로 열면 새 환경에서도 로그 파일을 만들고 기존 기록은 보존할 수 있다.

문서 작업도 운영 결과물이 될 수 있다. Day 16에는 source 기능을 추가하지 않았지만 기존 명령을 실제 실행해 효과를 확인하고, 정상 운영과 장애 복구 순서를 하나의 Runbook으로 만들었다. 코드가 동작하는 것과 운영자가 안전하게 반복 사용할 수 있는 것은 별개의 완성 기준이다.

## Codex Q&A 기록

- 질문: `log_path.parent.mkdir(parents=True, exist_ok=True)`는 어떻게 동작하는가?
  답변: `runs.jsonl` 파일 자체가 아니라 부모인 `logs/`를 준비한다. 중간 상위 경로가 없으면 함께 만들고 이미 디렉터리가 존재하면 그대로 사용한다. 그다음 파일을 append mode로 열어 기존 로그 뒤에 새 기록을 추가한다.
- 질문: Day 16은 장애 발생 시 행동을 더 구체적으로 작성하는 날인가?
  답변: 장애 대응도 포함하지만 더 넓게는 환경 준비, 정상 실행, 결과 확인, 재현, 복구와 정리를 하나의 운영 순서로 연결하는 날이다. Day 15 장애 문서는 원인 중심이고 Runbook은 실제 실행 순서 중심이다.
- 질문: 오늘은 기존 기능과 내용을 목적에 맞게 정리한 문서 작업인가?
  답변: 맞다. 실행 source와 설정은 변경하지 않고 기존 기능을 운영자가 문서 하나로 사용할 수 있게 정리했다. 다만 문서 명령이 실제로 맞는지 확인하기 위해 정상 학습, Tool, Docker와 재현 비교를 실행했다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [MLOps](mlops.md)
- [Runbook](../runbook.md)
