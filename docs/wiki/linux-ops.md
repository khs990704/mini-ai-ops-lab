# Linux 운영

## 짧은 정의

Linux 운영은 Linux 시스템에서 process, 파일, 로그, disk 사용량, 권한, 실행 상태를 확인하고 관리하는 일이다.

## 이 프로젝트에서 중요한 이유

이 프로젝트는 WSL에서 개발되며 작은 운영 시스템처럼 동작해야 한다. 생성된 로그와 artifact, 실행 중인 process, 파일 권한을 Linux 명령으로 확인할 수 있어야 한다.

## 저장소에서 사용되는 위치

- `logs/`
- `artifacts/`
- `src/run_job.py`
- 향후 작성할 `docs/runbook.md`
- 검증에 사용하는 shell 명령

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

## 실용적인 이해

운영 작업에서는 코드만 읽는 것이 아니라 실제 실행환경에서 관찰 가능한 증거를 확인해야 한다. 이 프로젝트는 Linux 명령을 사용해 로그, artifact, 경로, 파일 크기를 확인하고 장애 원인을 좁힌다.

`Path("logs/runs.jsonl")`은 현재 작업 디렉터리를 기준으로 해석되는 상대 경로다. 따라서 프로젝트가 기대하는 `logs/`에 기록하려면 프로젝트 root에서 명령을 실행한다. 부모 디렉터리를 먼저 만든 뒤 파일을 append mode로 열면 새 환경에서도 로그 파일을 만들고 기존 기록은 보존할 수 있다.

## Codex Q&A 기록

- 질문: `log_path.parent.mkdir(parents=True, exist_ok=True)`는 어떻게 동작하는가?
  답변: `runs.jsonl` 파일 자체가 아니라 부모인 `logs/`를 준비한다. 중간 상위 경로가 없으면 함께 만들고 이미 디렉터리가 존재하면 그대로 사용한다. 그다음 파일을 append mode로 열어 기존 로그 뒤에 새 기록을 추가한다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [MLOps](mlops.md)
