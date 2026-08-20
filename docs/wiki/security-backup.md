# 보안과 백업

## 짧은 정의

보안은 Secret과 운영 data에 누가 접근하고 무엇을 실행할 수 있는지 통제하는 일이다. Backup은 장애 전에 복구할 data 사본을 만드는 일이고, restore는 그 사본을 실제로 다시 사용할 수 있는 상태로 되돌리는 과정이다.

## 이 프로젝트에서 중요한 이유

Mini AI Ops Lab은 source뿐 아니라 실행 중에 쌓이는 config, JSONL log와 model artifact가 있어야 과거 작업을 확인하고 재현할 수 있다. 이 파일들은 Git에서 제외되므로 별도의 보존·backup 기준이 필요하다. 또한 log, Docker image와 공유 archive에 Secret이 들어가지 않도록 저장 위치와 확인 절차를 분리해야 한다.

## 저장소에서 사용되는 위치

- `.env.example`: Secret이 아닌 환경변수 형식만 공유한다. 현재 code가 `.env`를 직접 읽는 것은 아니다.
- `.gitignore`: `.env`, 실제 log와 model artifact를 Git 추적에서 제외한다.
- `.dockerignore`: Secret 가능 파일과 기존 운영 결과를 Docker build context에서 제외한다.
- `configs/`: 학습 조건과 Agent Tool 허용 정책으로, 현재 운영 data archive에 포함한다.
- `logs/`: Run·audit record로, 현재 운영 data archive에 포함한다.
- `artifacts/`: Run ID별 model로, 현재 운영 data archive에 포함한다.
- `docs/security-backup-checklist.md`: 접근 제어, 보존, backup·restore와 Secret 사고 대응 기준이다.

현재 복구 경계는 다음과 같다.

| 대상 | 복구 기준 |
|---|---|
| `configs/`, `logs/`, `artifacts/` | 검증된 운영 data backup archive |
| Source와 문서 | Git 저장소 |
| `.env`, API key, token과 private key | 일반 archive가 아닌 별도 암호화 저장소 또는 secret manager |

## 알아둘 명령어나 코드

### Git과 Secret 제외 확인

```bash
git check-ignore -v .env logs/runs.jsonl artifacts/example/model.pkl
git ls-files .env .env.example logs artifacts
git grep -nE 'AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY'
```

첫 두 명령은 ignore 규칙과 실제 Git 추적 대상을 읽는다. 마지막 명령은 추적 파일에서 명확한 AWS key 또는 private key header 형태를 찾는 보조 검사다. 검색 결과가 없을 때 `git grep`의 exit code `1`은 오류가 아니라 일치 항목이 없다는 뜻이다.

### 운영 data archive 생성과 별도 경로 복원

```bash
backup_test_dir=$(mktemp -d /tmp/mini-ai-ops-backup-test.XXXXXX)
mkdir "$backup_test_dir/restored"
tar -czf "$backup_test_dir/mini-ai-ops-data.tar.gz" configs logs artifacts
tar -tzf "$backup_test_dir/mini-ai-ops-data.tar.gz"
tar -xzf "$backup_test_dir/mini-ai-ops-data.tar.gz" -C "$backup_test_dir/restored"
diff -rq configs "$backup_test_dir/restored/configs"
diff -rq logs "$backup_test_dir/restored/logs"
diff -rq artifacts "$backup_test_dir/restored/artifacts"
```

`tar -czf`는 archive를 생성하고 `tar -xzf`는 `/tmp`의 별도 경로에 파일을 만든다. 세 `diff`가 출력 없이 exit code `0`이면 원본과 복원본에 차이가 없다는 뜻이다. `/tmp`는 원본과 같은 host이므로 이 archive는 절차 시험용이며 실제 장애용 backup은 다른 저장장치나 별도 계정에 보관해야 한다.

## RPO, RTO와 SLA

- RPO(Recovery Point Objective): 장애가 발생했을 때 최근 data를 얼마까지 잃어도 되는지 정한 목표다.
- RTO(Recovery Time Objective): 장애 후 project를 얼마나 빨리 다시 사용할 수 있어야 하는지 정한 목표다.
- SLA(Service Level Agreement): 서비스 제공자가 고객에게 가동률이나 대응·복구 수준을 보장하는 약속이다.

현재 project의 RPO 24시간과 RTO 2시간은 외부 고객에게 보장하는 SLA가 아니다. 하루 한 번 backup한다는 가정과 두 시간 안에 복원·검증을 마친다는 **내부 학습 기준**이다. 자동 schedule, 외부 backup 저장소와 alert가 없으므로 현재 이 목표는 자동으로 보장되지 않는다.

`Daily 7개`, `Weekly 4개`는 최근 일일 archive 7개와 주간 대표 archive 4개를 보관하겠다는 초기 기준이다. 자동화가 구현됐다는 뜻은 아니다.

## 흔한 실패 사례

### Secret이 Git이나 log에 노출됨

- 증상: API key, token, password 또는 private key가 추적 파일, history, image나 archive에 나타난다.
- 우선 조치: 파일 삭제보다 먼저 해당 credential을 제공 service에서 폐기하거나 회전한다.
- 후속 조치: Git history, log, Docker image, backup과 공유 위치까지 범위를 확인하고 새 credential을 최소 권한으로 발급한다.
- 주의: 현재 파일에서 문자열을 지워도 이미 복사된 Secret은 계속 사용될 수 있다.

### Backup archive를 만들었지만 복원하지 못함

- 증상: `tar -tzf`가 실패하거나 복원본의 log·model이 원본과 다르다.
- 대응: 원본을 삭제하지 않고 새 archive나 다른 정상 backup을 선택한다. 운영 경로가 아닌 staging 경로에 먼저 복원하고 JSONL parsing, config 검증, 파일 수와 checksum을 확인한다.

### 출처가 불분명한 pickle model을 불러옴

- 위험: Pickle load는 단순 data 읽기가 아니며 예상하지 않은 code 실행을 일으킬 수 있다.
- 대응: Project가 생성하고 run log·backup 출처를 확인할 수 있는 model만 사용한다. 실행 권한을 제거하는 것만으로 악성 pickle 위험이 없어지지는 않는다.

### 접근 권한이 환경에 맞지 않음

현재 WSL 단일 사용자 환경의 directory `755`, file `644`는 소유자만 쓸 수 있지만 다른 local 사용자가 읽을 수 있다. 공유 server에서는 service account와 group을 먼저 정한 뒤 `750`·`640` 또는 더 엄격한 권한을 검토한다. 대상을 확인하지 않은 일괄 `chmod`는 사용하지 않는다.

## 실용적인 이해

Backup은 압축 파일을 만든 것으로 끝나지 않는다. 실제로 별도 위치에 풀고 config, log와 model이 읽히며 원본과 일치하는지 확인해야 복구 가능한 backup이라고 판단할 수 있다.

이 project에서는 Git이 source와 문서의 복구 기준이고 운영 data archive가 config, log와 artifact의 복구 기준이다. Secret은 두 경로와 분리한다. 장애가 발생하면 현재 상태를 즉시 덮어쓰지 않고 증거를 보존한 뒤 staging 경로에서 검증된 복원본만 운영 경로에 반영한다.

## Codex Q&A 기록

- 질문: RPO와 RTO는 무엇인가?
  답변: RPO는 최대 어느 시점까지의 data 손실을 허용할지, RTO는 장애 후 어느 시간 안에 복구할지를 정한 목표다. 현재 기준은 각각 24시간과 2시간이다.
- 질문: SLA는 무엇이며 현재 project에도 있는가?
  답변: SLA는 고객과 합의한 서비스 보장 수준이다. 현재 project에는 고객 SLA가 없으며 RPO·RTO는 backup 연습을 위한 내부 기준이다.
- 질문: 2단계에서는 무엇을 한 것인가?
  답변: 보관 기간, backup 주기, 접근 권한, 허용 data 손실과 목표 복구 시간의 기준점을 정했다. 자동 backup을 구현한 단계는 아니다.
- 질문: Backup할 때 무엇을 보관하는가?
  답변: 현재 archive에는 `configs/`, `logs/`, `artifacts/`를 넣는다. Source와 문서는 Git에서 복구하고 Secret은 일반 archive가 아닌 별도 보호 저장소에서 복구한다.
- 질문: Day 17은 문서만 작성하는 날인가?
  답변: 주 결과물은 문서지만 실제 Git 제외·권한 상태를 점검하고 `/tmp`에서 archive 생성, 별도 복원, 원본 비교, JSONL parsing과 config 검증까지 수행했다.

## 관련 문서

- [보안·백업 체크리스트](../security-backup-checklist.md)
- [Runbook](../runbook.md)
- [Architecture](../architecture.md)
- [장애 시나리오](../failure-scenarios.md)
- [프로젝트 계획](../project-plan.md)
