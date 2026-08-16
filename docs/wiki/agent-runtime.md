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

Allowlist만 검증하는 명령은 다음과 같다.

```bash
python src/tool_config_loader.py --config configs/tools.yaml
```

이 명령은 설정을 읽고 검증할 뿐 Tool을 실행하지 않는다. 실제 요청은 다음과 같이 실행한다.

```bash
python src/tool_runner.py --tool echo --input "hello" --timeout 1
python src/tool_runner.py --tool list_artifacts --timeout 1
python src/tool_runner.py --tool read_log_summary --timeout 1
python src/tool_runner.py --tool run_train_job --timeout 30
python src/tool_runner.py --tool unknown
tail -n 5 logs/audit.jsonl
```

앞의 세 Tool은 주요 업무 데이터를 변경하지 않지만 모든 Tool 요청은 audit log 한 줄을 추가한다. `run_train_job`은 새 run log와 model artifact도 생성하며, `unknown`은 실행되지 않고 exit code `1`로 거부된 시도가 기록된다.

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

### Day 12 고정 Handler Dispatch

Day 12의 `src/tool_runner.py`는 설정을 실제 실행 통제로 연결한다.

```text
Tool 이름과 선택 입력 수신
        ↓
tools.yaml allowlist 등록 확인
        ↓
input_type과 실제 입력 비교
        ↓
TOOL_HANDLERS의 고정 Python 함수 확인
        ↓
실행 또는 구조화된 거부 결과 반환
```

Allowlist와 handler mapping을 모두 확인하는 이유는 설정에 이름만 추가해도 코드 실행 권한이 생기지 않게 하기 위해서다. Tool 이름을 shell command로 해석하지 않고 코드에서 검토한 Python 함수에만 연결한다.

| Tool | 쉬운 목적 | 동작 |
|---|---|---|
| `echo` | Tool 호출 경로 확인 | 전달받은 문자열을 그대로 반환 |
| `list_artifacts` | 저장된 model 확인 | `artifacts/*/model.pkl`과 run ID 조회 |
| `read_log_summary` | 최근 학습 상태 확인 | 최근 run 5개의 성공·실패와 핵심 결과 요약 |
| `run_train_job` | Agent 요청으로 학습 실행 | 기본 설정 학습 후 run log와 artifact 생성 |

성공과 실패는 `tool_name`, `status`, `result`, `error_type`, `error_message`라는 공통 field를 사용한다. `run_train_job`은 Tool handler 자체의 `status`와 내부 학습의 `training_status`를 구분한다.

### Day 13 Timeout과 Process 격리

Tool handler를 같은 process에서 직접 호출하면 실행이 끝나지 않을 때 Runner도 함께 기다려야 한다. Day 13 runner는 WSL/Linux와 Docker의 별도 child process에서 handler를 실행하고 pipe로 결과를 받는다.

```text
검증된 Tool handler를 child process에서 시작
                    ↓
부모 process가 --timeout 동안 pipe 결과 대기
          ┌─────────┴─────────┐
          ▼                   ▼
    시간 안에 완료       제한 시간 초과
    결과 반환             terminate 후 필요 시 kill
          └─────────┬─────────┘
                    ▼
        success/failed/timeout audit 기록
```

기본 제한 시간은 30초다. `--timeout 0`은 결과를 기다리지 않아 timeout 경로를 재현할 때 사용한다. 음수, 무한대와 `NaN`은 Tool 요청 시작 전에 CLI가 거부한다.

Timeout의 목적은 끝나지 않거나 지나치게 느린 Tool이 Agent 응답, CPU와 memory를 계속 점유하지 못하게 실행 시간의 상한을 두는 것이다. 그러나 process 종료는 transaction rollback이 아니다. 쓰기 Tool이 이미 log, artifact 또는 외부 상태를 만들었다면 일부 결과가 남을 수 있으므로 timeout 뒤에 관련 상태를 확인해야 한다.

## 흔한 실패 사례

- 실패: 허용되지 않은 도구 요청
- 증상: 등록되지 않았거나 위험한 도구 이름이 요청됨
- 확인할 것: `configs/tools.yaml`, `TOOL_HANDLERS`, 반환된 `ToolNotAllowedError`와 audit log
- 복구 방법: 기본적으로 요청을 거부하고 시도 자체를 `status: failed`로 기록함
- 실패: Allowlist에는 있지만 handler가 구현되지 않음
- 증상: `ToolHandlerNotImplementedError`와 exit code `1`이 반환됨
- 확인할 것: 설정에 이름만 추가한 것인지, 검토된 handler가 `TOOL_HANDLERS`에 연결됐는지 확인함
- 복구 방법: 필요한 입력과 resource 범위를 먼저 검토한 뒤 고정 Python handler를 구현함
- 실패: `input_type: none` Tool에 입력을 전달함
- 증상: Tool 기능 실행 전에 입력 오류와 exit code `1`이 반환됨
- 확인할 것: `configs/tools.yaml`의 `input_type`과 CLI의 `--input`
- 복구 방법: 입력을 제거하거나 text 입력을 받도록 검토된 Tool을 사용함
- 실패: 잘못된 access나 project 밖 resource가 설정에 포함됨
- 증상: `tool_config_loader.py`가 exit code 1과 설정 오류를 반환함
- 확인할 것: `input_type`, `access`, `resources`와 상대 경로 여부
- 복구 방법: 허용된 값과 실제 필요한 project 내부 경로만 남긴 뒤 다시 검증함
- 실패: YAML에 등록했으므로 OS 권한도 제한됐다고 오해함
- 증상: 실행 코드가 설정을 확인하지 않거나 process가 더 넓은 파일 권한을 가짐
- 확인할 것: Tool Runner의 allowlist 검사, handler 구현, Docker·OS 사용자 권한
- 복구 방법: application allowlist와 실행환경 권한 제한을 함께 적용함
- 실패: Tool이 제한 시간 안에 끝나지 않음
- 증상: `status: timeout`, `ToolTimeoutError`와 exit code `1`이 반환됨
- 확인할 것: audit log의 `duration_seconds`, `timeout_seconds`, 관련 run log와 artifact
- 복구 방법: 일부 결과 여부와 자원·외부 dependency 상태를 확인한 뒤 원인을 해결하거나 적정 timeout으로 새 요청을 실행함

## 실용적인 이해

Agent 도구 실행은 일반 함수 호출처럼 보이더라도 외부 상태를 바꿀 수 있다. 이 프로젝트에서는 allowlist, 입력 처리, timeout, audit log를 사용해 실행 범위를 제한하고 호출 이력을 추적한다.

Allowlist는 등록된 항목만 허용하고 나머지는 기본적으로 거부하는 방식이다. Tool 이름을 shell command로 그대로 실행하는 것이 아니라 미리 구현한 Python handler에 연결해야 arbitrary command 실행 위험을 줄일 수 있다.

Day 11의 `access`와 `resources`는 Tool의 의도된 영향 범위를 설명하고 loader가 설정 오류를 잡는 정책 metadata다. Day 12 runner는 이름, 입력과 고정 handler를 실제로 강제하지만 이 metadata를 OS 파일 권한으로 자동 적용하지는 않는다. Docker의 비 root 사용자와 고정된 handler 경로가 별도의 실행환경 경계를 보완한다.

학습용 `config_loader.py`와 Tool용 `tool_config_loader.py`는 모두 YAML을 검증하지만 대상이 다르다. 전자는 `train.yaml`의 학습 조건을 `run_job.py`에 제공하고, 후자는 `tools.yaml`의 허용 목록을 `tool_runner.py`에 제공한다. 사용자가 loader를 직접 실행하는 것은 주로 설정 확인과 troubleshooting을 위한 방법이다.

Audit logger는 시간을 기록하는 별도 Tool이 아니다. 기존 네 Tool의 모든 요청을 Runner가 감싸서 성공, 거부, 실패와 timeout을 자동으로 기록하는 공통 운영 기능이다.

## Codex Q&A 기록

- 질문: 여기서 Agent는 Codex 같은 도구를 의미하는가?
  답변: Codex는 판단하고 Tool 사용을 요청하는 Agent에 가깝다. `echo`, `list_artifacts`, `read_log_summary`, `run_train_job`은 Agent가 요청할 수 있는 Tool이다. 이 프로젝트 설정이 실제 Codex 권한을 제한하는 것은 아니다.
- 질문: Agent마다 Tool 허용 범위는 같은가, 다른가?
  답변: 둘 다 가능하다. 현재 프로젝트는 Agent identity가 없는 단일 실행환경이라 공통 allowlist를 사용한다. 실제 역할이 나뉘면 Agent 또는 role별 최소 권한으로 확장하는 편이 안전하다.
- 질문: 모두 같은 allowlist를 공유하는 방식이 더 좋은가?
  답변: 현재처럼 Agent가 하나이고 Tool이 네 개인 학습 단계에서는 단순한 공통 목록이 적합하다. 여러 역할이 생기면 필요 이상의 권한을 막기 위해 역할별 목록으로 분리해야 한다.
- 질문: 기존 `config_loader.py`는 사용자가 사용하고 `tool_config_loader.py`는 Agent가 사용하는가?
  답변: 사용자와 Agent 기준의 구분이 아니라 설정 종류의 차이다. `config_loader.py`는 학습 조건을, `tool_config_loader.py`는 Agent가 요청할 Tool 허용 목록을 검증한다. 실제 운영에서는 각각 `run_job.py`와 `tool_runner.py`가 내부에서 호출한다.
- 질문: `tool_config_loader.py`는 Agent가 사용할 Tool을 불러오는 것인가?
  답변: 맞다. 더 정확히는 등록된 Tool 정의를 읽고 검증해 Tool Runner가 사용할 공통 allowlist로 반환한다. Loader 자체는 Tool을 실행하지 않는다.
- 질문: Day 12는 Tool의 구체적인 사용 내용을 만드는 작업인가?
  답변: 맞다. Day 11이 허용 정책을 정의했다면 Day 12는 각 이름이 요청됐을 때 실행할 Python handler를 만들고 실제 허용·거부를 검증하는 단계다.
- 질문: `tool_runner.py`는 Tool 실행 파일인가?
  답변: 맞다. 요청 이름과 입력을 받고 allowlist, 입력 형태와 고정 handler를 확인한 뒤 성공 또는 실패 JSON을 반환하는 중앙 실행 경계다.
- 질문: 추가한 Tool의 목표를 쉽게 요약하면 무엇인가?
  답변: `echo`는 호출 경로 확인, `list_artifacts`는 저장 model 조회, `read_log_summary`는 최근 학습 상태 확인, `run_train_job`은 새 학습 실행을 담당한다.
- 질문: Day 13은 시간을 기록하는 Tool을 설정하는 것인가?
  답변: 별도 Tool을 추가하는 것이 아니다. 기존 Tool을 실행할 때 Runner와 Audit Logger가 시작·종료 시각, duration과 결과를 자동으로 기록하고 제한 시간도 적용한다.
- 질문: Tool에 제한 시간을 두는 이유는 무엇인가?
  답변: 끝나지 않거나 지나치게 느린 Tool이 Agent의 응답과 CPU·memory를 계속 점유하지 않게 상한을 두기 위해서다. Timeout 뒤에도 이미 발생한 상태 변경은 자동 복구되지 않는다.
- 질문: 기존 Tool들에 대한 기록을 남기는 것인가?
  답변: 맞다. 허용된 실행뿐 아니라 미등록 요청과 timeout까지 `logs/audit.jsonl`에 남겨 나중에 Agent가 어떤 Tool을 요청했고 결과가 어땠는지 추적한다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
- [Architecture](../architecture.md)
