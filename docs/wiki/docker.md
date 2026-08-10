# Docker

## 짧은 정의

Docker는 애플리케이션과 실행에 필요한 의존성을 함께 묶어 더 재현 가능한 환경에서 실행하게 하는 도구다.

- image: Linux 기반 환경, Python, dependency, 코드와 기본 명령을 묶은 재사용 가능한 실행 설계도
- container: image로부터 만들어져 실제 명령을 수행하는 실행 인스턴스
- build context: image build 때 Docker daemon에 전달되는 파일 범위
- bind mount: container 경로와 host 경로를 연결하여 실행 결과를 host에 보존하는 방식

## 이 프로젝트에서 중요한 이유

다른 사람도 같은 방법으로 프로젝트를 실행할 수 있어야 한다. Docker를 사용하면 숨겨진 로컬 설정에 의존하지 않고 정해진 Python 버전과 패키지로 학습 작업과 도구 실행기를 실행할 수 있다.

## 저장소에서 사용되는 위치

- `Dockerfile`
- `.dockerignore`
- `requirements.txt`
- `src/`
- `logs/`
- `artifacts/`

Day 6 image는 Python 3.12, `requirements.txt` dependency, `src/` 코드, 결과 경로와 `python src/run_job.py` 기본 명령을 포함한다. 실제 실행은 root가 아닌 `appuser`를 기본 사용자로 삼는다.

## 알아둘 명령어나 코드

```bash
docker build -t mini-ai-ops-lab:day6 .
docker run --rm mini-ai-ops-lab:day6
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --mount type=bind,source="$PWD/logs",target=/app/logs \
  --mount type=bind,source="$PWD/artifacts",target=/app/artifacts \
  mini-ai-ops-lab:day6
```

첫 번째 명령은 image와 build cache를 만든다. 두 번째 명령은 동작만 확인하고 종료된 container와 내부 결과를 제거한다. 세 번째 명령은 현재 WSL 사용자 권한으로 실행하며 success log와 model artifact를 host에 보존한다.

## 흔한 실패 사례

- 실패: 로컬 환경과 container의 의존성이 서로 다름
- 증상: 로컬에서는 실행되지만 Docker에서는 실패함
- 확인할 것: `requirements.txt`, Python 버전, 파일 경로
- 복구 방법: 의존성 버전을 명시하고 Docker 안에서 같은 명령을 검증함
- 실패: container 종료 후 log와 artifact가 사라짐
- 증상: terminal 출력은 있었지만 host의 `logs/`와 `artifacts/`에는 결과가 없음
- 확인할 것: bind mount option과 host source 경로
- 복구 방법: `/app/logs`와 `/app/artifacts`를 프로젝트의 host 경로에 bind mount함
- 실패: container가 만든 파일을 WSL 사용자가 수정하지 못함
- 증상: 결과 파일이 root 소유자로 생성됨
- 확인할 것: `--user` option과 host UID·GID
- 복구 방법: `--user "$(id -u):$(id -g)"`로 현재 WSL 사용자 권한을 전달함

## 실용적인 이해

Docker는 학습과 운영 환경을 다른 컴퓨터에서도 재현하는 데 도움을 준다. 이 프로젝트에서는 기존 Python 기능을 Docker 전용 코드로 변경하지 않고, 같은 `src/run_job.py`를 별도 실행환경에서도 동작하게 한다.

현재 학습은 한 번 실행하고 끝나는 batch job이다. 따라서 image는 재사용하고, 실행마다 깨끗한 container를 만든 뒤 `--rm`으로 제거하며, 보존할 결과만 bind mount로 host에 남기는 방식을 사용한다. 종료된 container 내부를 조사해야 할 때는 `--rm`을 생략할 수 있고, 이름 있는 container를 `docker start -a`로 재사용하거나 개발용 container에서 `docker exec`를 사용할 수도 있다. 다만 이전 filesystem과 오래된 image 상태가 남으므로 현재 batch job에는 새 container 방식이 더 명확하다.

`CMD ["python", "src/run_job.py"]`가 있으므로 `docker run ... mini-ai-ops-lab:day6`만 입력해도 container 안에서 Python 명령이 실행된다. Image 이름 뒤에 `python src/run_job.py --fail`을 붙이면 기본 명령을 덮어쓴다.

현재 `requirements.txt`는 호환 가능한 version 범위를 사용한다. 한번 만든 image는 package 조합을 유지하지만 미래의 rebuild까지 완전히 같은 version을 보장하지는 않는다. 실제 Day 6 검증에서는 host의 scikit-learn 1.5.1과 container의 1.9.0이 같은 metric을 만들었지만 pickle 크기는 각각 834바이트와 824바이트였다. 완전히 같은 rebuild가 필요하면 lock file이나 정확한 version 고정이 필요하고, pickle은 가능한 한 생성한 image 환경에서 불러온다.

## Codex Q&A 기록

- 질문: Docker container를 만드는 목적은 무엇인가?
  답변: 현재 WSL에 우연히 설치된 Python과 package에 의존하지 않고, 다른 환경에서도 같은 코드와 실행 방법을 사용할 수 있음을 검증하기 위해서다.
- 질문: Day 5까지의 동작을 Docker 기반으로 수정한 것인가?
  답변: 아니다. 기존 `src/` 코드는 그대로 두고 Python 3.12, dependency, 코드와 실행 명령을 담은 별도 실행환경을 추가했다. local Python 실행도 계속 가능하다.
- 질문: `requirements.txt` 같은 실행환경을 Docker로 만든 것인가?
  답변: 맞다. 더 정확히는 Linux 기반 환경, Python, dependency, `src/` 코드와 기본 명령을 함께 image로 묶었다.
- 질문: 실행할 때도 `python src/run_job.py`를 입력하는가?
  답변: WSL에서는 `docker run`을 입력하고 Dockerfile의 `CMD`가 container 내부에서 Python 명령을 자동 실행한다. Image 이름 뒤에 다른 Python 명령을 붙여 기본 명령을 덮어쓸 수도 있다.
- 질문: 왜 `--rm`을 사용하는가?
  답변: batch job이 끝난 뒤 더 이상 필요하지 않은 container를 자동 제거하기 위해서다. Image와 bind mount의 log·artifact는 유지된다.
- 질문: 매번 `--rm`을 사용하는 방법밖에 없는가?
  답변: 아니다. 이름 있는 container 재시작, 계속 실행하는 개발 container와 Docker Compose도 가능하다. 현재는 매번 깨끗한 상태로 실행하고 결과만 보존하는 방식이 학습 batch job 목적에 가장 부합한다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [프로젝트 README](../../README.md)
