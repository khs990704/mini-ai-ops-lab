# Agent 실행환경

## 짧은 정의

Agent 실행환경은 tool call 요청을 받고, 요청을 검증하며, 허용된 도구만 실행하고, 그 결과를 기록하는 환경이다.

## 이 프로젝트에서 중요한 이유

Agent가 제한 없이 도구를 실행하면 안정성과 보안 문제가 생길 수 있다. 이 프로젝트는 작은 allowlist 기반 도구 실행기를 통해 실행 통제, timeout, 감사 가능성을 구현한다.

## 저장소에서 사용되는 위치

- `configs/tools.yaml`
- `src/tool_config_loader.py`
- `src/tool_runner.py`
- `src/audit_logger.py`
- `logs/audit.jsonl`

## 알아둘 명령어나 코드

현재 구현된 allowlist 검증 명령은 다음과 같다.

```bash
python src/tool_config_loader.py --config configs/tools.yaml
```

이 명령은 설정을 읽고 검증할 뿐 Tool을 실행하지 않는다. Day 12 이후 사용할 예정인 요청 명령은 다음과 같다.

```bash
python src/tool_runner.py --tool echo --input "hello"
python src/tool_runner.py --tool unknown
tail -n 5 logs/audit.jsonl
```

### Day 11 공통 Tool Allowlist

Agent는 필요한 기능을 판단하고 Tool 사용을 요청하는 주체다. Tool은 로그 읽기나 학습 실행처럼 실제 작업을 수행하는 기능이며, Tool Runner는 요청을 검사하고 허용된 handler만 호출하는 실행 경계다.

```text
Agent의 Tool 요청
        ↓
Tool Runner가 allowlist 확인
        ↓
허용된 Tool handler 실행 또는 거부
```

현재 `configs/tools.yaml`은 다음 네 Tool을 모든 요청에 공통으로 허용할 후보로 정의한다.

| Tool | 입력 | 영향 수준 | Resource |
|---|---|---|---|
| `echo` | text | `none` | 없음 |
| `list_artifacts` | 없음 | `read` | `artifacts/` |
| `read_log_summary` | 없음 | `read` | `logs/runs.jsonl` |
| `run_train_job` | 없음 | `write` | `logs/runs.jsonl`, `artifacts/` |

`src/tool_config_loader.py`는 Tool 이름, 필수 field, 입력 형태, 접근 수준과 resource를 검사한다. 절대 경로나 `..`로 project 밖을 가리키는 resource도 거부한다.

현재는 Agent identity와 role을 구분하지 않으므로 하나의 작은 공통 allowlist를 사용한다. 여러 Agent가 서로 다른 책임을 갖게 되면 monitor 역할에는 읽기 Tool만, training 역할에는 `run_train_job`까지 허용하는 방식으로 최소 권한을 세분화할 수 있다.

## 흔한 실패 사례

- 실패: 허용되지 않은 도구 요청
- 증상: 등록되지 않았거나 위험한 도구 이름이 요청됨
- 확인할 것: `configs/tools.yaml`, `logs/audit.jsonl`
- 복구 방법: 기본적으로 요청을 거부하고 시도 자체를 audit log에 기록함
- 실패: 잘못된 access나 project 밖 resource가 설정에 포함됨
- 증상: `tool_config_loader.py`가 exit code 1과 설정 오류를 반환함
- 확인할 것: `input_type`, `access`, `resources`와 상대 경로 여부
- 복구 방법: 허용된 값과 실제 필요한 project 내부 경로만 남긴 뒤 다시 검증함
- 실패: YAML에 등록했으므로 OS 권한도 제한됐다고 오해함
- 증상: 실행 코드가 설정을 확인하지 않거나 process가 더 넓은 파일 권한을 가짐
- 확인할 것: Tool Runner의 allowlist 검사, handler 구현, Docker·OS 사용자 권한
- 복구 방법: application allowlist와 실행환경 권한 제한을 함께 적용함

## 실용적인 이해

Agent 도구 실행은 일반 함수 호출처럼 보이더라도 외부 상태를 바꿀 수 있다. 이 프로젝트에서는 allowlist, 입력 처리, timeout, audit log를 사용해 실행 범위를 제한하고 호출 이력을 추적한다.

Allowlist는 등록된 항목만 허용하고 나머지는 기본적으로 거부하는 방식이다. Tool 이름을 shell command로 그대로 실행하는 것이 아니라 미리 구현한 Python handler에 연결해야 arbitrary command 실행 위험을 줄일 수 있다.

Day 11의 `access`와 `resources`는 Tool의 의도된 영향 범위를 설명하고 loader가 설정 오류를 잡는 정책 metadata다. 아직 `tool_runner.py`가 없으므로 실제 요청을 차단하거나 Tool을 실행하지 않으며, OS 파일 권한도 자동으로 바꾸지 않는다.

학습용 `config_loader.py`와 Tool용 `tool_config_loader.py`는 모두 YAML을 검증하지만 대상이 다르다. 전자는 `train.yaml`의 학습 조건을 `run_job.py`에 제공하고, 후자는 `tools.yaml`의 허용 목록을 향후 `tool_runner.py`에 제공한다. 사용자가 직접 실행하는 것은 주로 설정 확인과 troubleshooting을 위한 방법이다.

## Codex Q&A 기록

- 질문: 여기서 Agent는 Codex 같은 도구를 의미하는가?
  답변: Codex는 판단하고 Tool 사용을 요청하는 Agent에 가깝다. `echo`, `list_artifacts`, `read_log_summary`, `run_train_job`은 Agent가 요청할 수 있는 Tool이다. 이 프로젝트 설정이 실제 Codex 권한을 제한하는 것은 아니다.
- 질문: Agent마다 Tool 허용 범위는 같은가, 다른가?
  답변: 둘 다 가능하다. 현재 프로젝트는 Agent identity가 없는 단일 실행환경이라 공통 allowlist를 사용한다. 실제 역할이 나뉘면 Agent 또는 role별 최소 권한으로 확장하는 편이 안전하다.
- 질문: 모두 같은 allowlist를 공유하는 방식이 더 좋은가?
  답변: 현재처럼 Agent가 하나이고 Tool이 네 개인 학습 단계에서는 단순한 공통 목록이 적합하다. 여러 역할이 생기면 필요 이상의 권한을 막기 위해 역할별 목록으로 분리해야 한다.
- 질문: 기존 `config_loader.py`는 사용자가 사용하고 `tool_config_loader.py`는 Agent가 사용하는가?
  답변: 사용자와 Agent 기준의 구분이 아니라 설정 종류의 차이다. `config_loader.py`는 학습 조건을, `tool_config_loader.py`는 Agent가 요청할 Tool 허용 목록을 검증한다. 실제 운영에서는 각각 `run_job.py`와 향후 `tool_runner.py`가 내부에서 호출한다.
- 질문: `tool_config_loader.py`는 Agent가 사용할 Tool을 불러오는 것인가?
  답변: 맞다. 더 정확히는 등록된 Tool 정의를 읽고 검증해 향후 Tool Runner가 사용할 공통 allowlist로 반환한다. Loader 자체는 Tool을 실행하지 않는다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [Architecture](../architecture.md)
