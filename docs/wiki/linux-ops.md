# Linux 운영

## 짧은 정의

Linux 운영은 Linux 시스템에서 process, 파일, 로그, disk 사용량, 권한, 실행 상태를 확인하고 관리하는 일이다.

## 이 프로젝트에서 중요한 이유

이 프로젝트는 WSL에서 개발되며 작은 운영 시스템처럼 동작해야 한다. 생성된 로그와 artifact, 실행 중인 process, 파일 권한을 Linux 명령으로 확인할 수 있어야 한다.

## 저장소에서 사용되는 위치

- `logs/`
- `artifacts/`
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

## 흔한 실패 사례

- 실패: 출력 파일을 찾을 수 없음
- 증상: 명령은 실행됐지만 로그 또는 artifact가 생성되지 않음
- 확인할 것: 현재 작업 디렉터리, 상대 경로, 쓰기 권한
- 복구 방법: 프로젝트 root에서 실행하고 필요한 디렉터리가 존재하는지 확인함

## 실용적인 이해

운영 작업에서는 코드만 읽는 것이 아니라 실제 실행환경에서 관찰 가능한 증거를 확인해야 한다. 이 프로젝트는 Linux 명령을 사용해 로그, artifact, 경로, 파일 크기를 확인하고 장애 원인을 좁힌다.

## Codex Q&A 기록

아직 기록된 질문이 없다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [MLOps](mlops.md)
