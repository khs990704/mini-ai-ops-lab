# Docker

## 짧은 정의

Docker는 애플리케이션과 실행에 필요한 의존성을 함께 묶어 더 재현 가능한 환경에서 실행하게 하는 도구다.

## 이 프로젝트에서 중요한 이유

다른 사람도 같은 방법으로 프로젝트를 실행할 수 있어야 한다. Docker를 사용하면 숨겨진 로컬 설정에 의존하지 않고 정해진 Python 버전과 패키지로 학습 작업과 도구 실행기를 실행할 수 있다.

## 저장소에서 사용되는 위치

- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `.env.example`

## 알아둘 명령어나 코드

```bash
docker build -t mini-ai-ops-lab .
docker run --rm mini-ai-ops-lab python src/run_job.py --config configs/train.yaml
```

## 흔한 실패 사례

- 실패: 로컬 환경과 container의 의존성이 서로 다름
- 증상: 로컬에서는 실행되지만 Docker에서는 실패함
- 확인할 것: `requirements.txt`, Python 버전, 파일 경로
- 복구 방법: 의존성 버전을 명시하고 Docker 안에서 같은 명령을 검증함

## 실용적인 이해

Docker는 학습과 운영 환경을 다른 컴퓨터에서도 재현하는 데 도움을 준다. 이 프로젝트에서는 작업 실행기가 특정 로컬 컴퓨터의 설정에만 의존하지 않는다는 것을 보여주는 용도로 사용한다.

## Codex Q&A 기록

아직 기록된 질문이 없다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
