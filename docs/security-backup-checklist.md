# 보안·백업 체크리스트

## 목적

Mini AI Ops Lab의 secret, source, config, log와 model artifact를 보호하고 장애 후 복원할 수 있는 기준을 기록한다. 이 문서는 현재 확인한 상태와 앞으로 적용할 운영 규칙을 구분한다.

모든 명령은 별도 안내가 없으면 WSL의 project root에서 실행한다.

```bash
cd /home/hskim/project/mini-ai-ops-lab
```

## 보호 대상

| 대상 | 예 | 보호 이유 |
|---|---|---|
| Secret | API key, password, token, private key | 노출되면 외부 system 접근과 비용 피해가 발생할 수 있음 |
| Source와 문서 | `src/`, `Dockerfile`, `docs/` | 실행 기능과 운영 절차를 복구하는 기준임 |
| Config | `configs/train.yaml`, `configs/tools.yaml` | 학습 조건과 Tool 허용 정책을 결정함 |
| Run·audit log | `logs/runs.jsonl`, `logs/audit.jsonl` | 실행, 장애와 Agent 요청의 운영 증거임 |
| Model artifact | `artifacts/{run_id}/model.pkl` | 학습 결과이며 run record와 연결됨 |

## 1. Secret 관리

- [x] 실제 secret은 source, YAML config와 Markdown 문서에 직접 작성하지 않는다.
- [x] Local secret이 필요하면 Git에서 제외되는 `.env`를 사용한다.
- [x] `.env.example`에는 변수 이름과 비밀이 아닌 예시만 작성한다.
- [x] 현재 `.env.example`의 `LOG_LEVEL`, `LOG_DIR`, `ARTIFACT_DIR`에는 credential이 없다.
- [x] Audit log에는 Tool 입력 원문과 handler 결과 전체를 저장하지 않는다.
- [ ] 실제 외부 credential을 도입할 때 secret manager 또는 별도 암호화 저장소를 선택한다.

현재 project code는 `.env` 값을 직접 읽지 않는다. `.env.example`은 향후 환경별 설정을 추가할 때 secret과 공유 가능한 기본 형식을 분리하기 위한 template이다.

다음 정보는 commit, 일반 log와 공유 archive에 넣지 않는다.

- API key, access token과 refresh token
- Password와 database connection string의 credential
- SSH·TLS private key
- 개인 식별정보와 원문 Agent 입력
- 신뢰 경계를 확인하지 않은 외부 model 또는 data

## 2. Git 제외 정책

현재 `.gitignore`는 다음 local·운영 파일을 제외한다.

| 규칙 | 제외 대상 | 저장소에 남기는 것 |
|---|---|---|
| `.env`, `.env.*` | 실제 local 환경 설정과 secret 가능 파일 | `!.env.example` |
| `logs/*` | 실행 중 생성된 run·audit log | `logs/.gitkeep` |
| `artifacts/*` | Model과 실행 결과물 | `artifacts/.gitkeep` |
| `.venv/`, `venv/` | Local dependency 환경 | `requirements.txt` |
| `__pycache__/`, `*.py[cod]` | Python cache | Python source |

Log와 model을 Git에서 제외하는 이유는 단순히 파일이 커질 수 있어서만은 아니다. Log에는 경로·오류와 운영정보가 들어갈 수 있고, pickle model은 binary 결과물이므로 source history와 별도의 retention·backup 정책이 필요하다.

### Commit 전 확인

```bash
git status --short
git check-ignore -v .env logs/runs.jsonl artifacts/example/model.pkl
git ls-files .env .env.example logs artifacts
```

- 목적: 새 파일 중 의도하지 않은 secret·운영 결과가 포함됐는지, ignore 규칙과 실제 추적 파일이 일치하는지 확인한다.
- 변경 여부: Git 상태와 규칙을 읽기만 한다.
- 성공 기준: 실제 `.env`, run log와 model 경로는 ignore 규칙에 해당하고, 이 범위에서 `.env.example`과 두 `.gitkeep`만 추적된다.

고신뢰 secret 형태가 추적 파일에 있는지 보조 검사한다.

```bash
git grep -nE 'AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY'
```

- 목적: AWS access key와 private key header처럼 명확한 secret pattern을 찾는다.
- 변경 여부: Git이 추적하는 파일을 읽기만 한다.
- 성공 기준: 일치 항목이 없어 출력이 없고 exit code `1`이다. `git grep`의 exit code `1`은 이 경우 검출 실패가 아니라 검색 결과가 없다는 뜻이다.
- 한계: Pattern 검사는 모든 token과 password를 찾지 못하므로 commit diff와 파일 내용을 사람이 함께 검토한다.

## 3. Docker Build Context 제외 정책

현재 `.dockerignore`는 다음 내용을 image build context에서 제외한다.

- `.git/`과 local 개발환경
- `.env`, `.env.*`
- 기존 `logs/`, `artifacts/`
- Project 문서와 editor cache

Docker image에는 `requirements.txt`, `src/`와 `configs/`가 포함된다. 따라서 `configs/`에는 image에 들어가도 되는 비밀이 아닌 실행 정책만 작성한다.

### Docker 제외 규칙 확인

```bash
sed -n '1,220p' .dockerignore
```

- 목적: Secret과 기존 운영 결과가 build context에서 제외되는지 검토한다.
- 변경 여부: 파일을 읽기만 한다.
- 성공 기준: `.env`, `.env.*`, `logs/`, `artifacts/`와 `.git/` 제외 규칙이 존재한다.

`.dockerignore`는 image로 복사되는 범위를 줄이지만 이미 노출된 secret을 폐기하거나 Git history에서 제거하지는 않는다. Secret 노출 대응은 별도의 사고 절차를 따른다.

## 현재 단계 확인표

- [ ] Commit 전에 `git status`와 추적 파일을 확인했는가?
- [ ] 새 config와 문서에 실제 credential이 없는가?
- [ ] `.env.example`에는 비밀이 아닌 값만 있는가?
- [ ] 새 log field에 원문 입력이나 credential이 포함되지 않는가?
- [ ] Docker build context에 `.env`, 기존 log와 model이 제외되는가?
- [ ] 새로운 외부 service를 연결했다면 secret 저장·회전 방법을 정했는가?

## 4. 접근 권한과 실행 경계

### 현재 확인 항목

- [x] Docker image는 root가 아닌 `appuser`로 실행한다.
- [x] Tool 이름을 shell 명령으로 실행하지 않고 Allowlist와 고정 Python handler를 확인한다.
- [x] Audit log에는 Tool 입력 원문 대신 `input_provided`만 기록한다.
- [x] Run ID별 artifact directory를 사용하고 기존 directory를 덮어쓰지 않는다.
- [ ] 여러 Linux 사용자가 같은 host를 공유한다면 log·artifact의 group과 mode를 별도로 제한한다.
- [ ] 운영환경에서는 실행 사용자와 backup 사용자에게 필요한 최소 경로만 허용한다.

현재 WSL은 단일 사용자 학습환경을 기준으로 한다. `755` directory와 `644` file은 소유자만 쓸 수 있지만 다른 local 사용자가 내용을 읽을 수 있다. 공유 server로 옮길 때는 민감도와 운영 group에 따라 directory `750`·file `640` 또는 더 엄격한 `700`·`600`을 검토한다. 실제 service account와 group을 정하기 전에 일괄 `chmod`를 적용하지 않는다.

```bash
stat -c '%a %U:%G %n' \
  .env.example configs/train.yaml configs/tools.yaml \
  logs artifacts logs/runs.jsonl logs/audit.jsonl
find logs artifacts -type f -perm /022 -print
```

- 목적: 주요 파일·directory의 mode와 소유자를 확인하고 group 또는 other가 쓸 수 있는 운영 파일을 찾는다.
- 변경 여부: 권한과 경로를 읽기만 한다.
- 성공 기준: 예상한 project 사용자 소유이며, 의도하지 않은 group·other writable 파일이 출력되지 않는다.

Docker 실행 사용자는 다음처럼 확인한다.

```bash
docker image inspect mini-ai-ops-lab:day13 \
  --format '{{.Config.User}} {{.Config.WorkingDir}}'
```

- 목적: Container가 root가 아닌 전용 사용자와 예상 작업 directory를 사용하는지 확인한다.
- 변경 여부: Image metadata를 읽기만 한다.
- 성공 기준: `appuser /app`이 출력된다.

### Pickle Model 신뢰 경계

`model.pkl`은 단순 data 파일이 아니라 Python pickle이다. Pickle은 불러오는 과정에서 code 실행을 유발할 수 있으므로 출처와 무결성을 신뢰할 수 있는 project artifact만 사용한다.

- 외부에서 받은 임의 `model.pkl`을 운영 process에서 바로 열지 않는다.
- Run log가 가리키는 경로, backup 출처와 checksum을 함께 확인한다.
- Artifact directory에 실행 권한이 없어도 악성 pickle load 위험이 사라지는 것은 아니다.
- 장기적으로는 서명, checksum manifest 또는 더 제한적인 model format을 검토한다.

## 5. Log·Artifact 보존 정책

현재 학습 project의 초기 운영 기준은 다음과 같다. 실제 저장량과 업무 중요도가 바뀌면 수치를 다시 정한다.

| 대상 | Active 보존 | Backup 보존 | 삭제 전 조건 |
|---|---|---|---|
| `logs/runs.jsonl` | 최근 30일 또는 10 MiB 도달 전 | Daily 7개, weekly 4개 | 연결된 model과 재현 기준을 함께 확인 |
| `logs/audit.jsonl` | 최근 30일 또는 10 MiB 도달 전 | Daily 7개, weekly 4개 | 보안·장애 조사 필요 여부 확인 |
| Success model | 최소 30일 | Daily 7개, weekly 4개 archive에 포함 | Success run 참조와 baseline 여부 확인 |
| Failed·부분 artifact | 원인 확인이 끝날 때까지 격리 | 필요한 장애 증거만 포함 | Run ID, 일부 파일과 조사 완료 확인 |
| Config | 현재 version을 Git에 보존 | 운영 data backup에도 사본 포함 | 관련 run 재현 가능성 확인 |

- `Daily 7개`는 최근 7번의 일일 backup archive를 보관한다는 뜻이다.
- `Weekly 4개`는 주간 대표 backup archive를 최근 4번까지 보관한다는 뜻이다.
- 위 수치는 현재 단계에서 정한 초기 기준이며, 이를 자동으로 실행하는 기능은 아직 구현하지 않았다.
- Rotation 조건은 기간과 크기 중 먼저 도달한 기준을 사용한다.
- Log와 artifact는 run ID 연결을 유지한 채 함께 보존한다.
- 참조되지 않는 artifact도 생성 배경을 확인하기 전에는 자동 삭제하지 않는다.
- Backup 생성과 restore 검증이 성공하기 전에는 원본을 정리하지 않는다.
- 현재 rotation과 backup은 자동화되지 않았으므로 운영자가 주기적으로 확인해야 한다.

현재 사용량은 다음 명령으로 확인한다.

```bash
du -sh logs artifacts
wc -l logs/runs.jsonl logs/audit.jsonl
```

- 목적: Backup·rotation이 필요한지 판단할 저장량과 record 수를 확인한다.
- 변경 여부: 읽기 전용이다.
- 성공 기준: 두 directory 크기와 JSONL별 줄 수가 출력된다.

## 6. Backup·복구 목표

Backup 기준은 다음 두 질문으로 정한다.

- RPO(Recovery Point Objective): **장애가 발생했을 때 최근 data를 얼마까지 잃어도 되는가?**
- RTO(Recovery Time Objective): **장애가 발생한 뒤 project를 얼마나 빨리 다시 사용할 수 있어야 하는가?**

Mini AI Ops Lab의 초기 학습 목표는 다음과 같다.

| 목표 | 현재 값 | 쉬운 의미 | 이를 위한 기준 |
|---|---:|---|---|
| RPO | 24시간 | 최대 하루 분량의 최근 운영 data를 잃을 수 있음 | 의미 있는 작업일 종료 후 하루 한 번 운영 data archive 생성 |
| RTO | 2시간 | 장애 후 2시간 안에 복구와 검증을 마치는 것이 목표임 | Git에서 source·문서를 받고 archive에서 config·log·artifact를 복원한 뒤 검증 |

RPO 24시간은 마지막 daily backup 이후 최대 하루의 run과 model을 잃을 수 있다는 뜻이다. RTO 2시간은 복원, JSONL 검사, model checksum과 기본 실행 확인까지 두 시간 안에 끝내는 목표다.

### SLA와의 차이

SLA(Service Level Agreement)는 서비스 제공자가 고객에게 가동률, 대응 시간 또는 복구 시간 등을 어느 수준으로 보장할지 정한 약속이다. 이 project에는 외부 고객과 맺은 SLA가 없다.

현재의 RPO 24시간과 RTO 2시간은 SLA가 아니라 backup·restore 연습을 위한 **내부 목표**다. 아직 schedule, 외부 backup 저장소와 alert가 없어 목표 달성이 자동으로 보장되지는 않는다. 중요한 service로 확장하면 허용 가능한 data 손실·중단 시간, backup 비용과 실제 restore 측정값을 기준으로 다시 정한다.

### RPO/RTO 확인 질문

- 마지막 성공 backup 시각을 알 수 있는가?
- Backup이 source와 다른 저장장치 또는 계정에도 존재하는가?
- Restore 절차를 실제로 실행하고 소요 시간을 측정했는가?
- 복원된 JSONL, config와 model checksum을 검증했는가?
- 목표를 넘겼을 때 누가 대응할지 정했는가?

## 7. Backup·restore 검증 절차

다음 절차는 원본을 덮어쓰지 않고 `/tmp`의 별도 directory에서 backup과 restore가 가능한지 시험한다. `/tmp`는 원본과 같은 host에 있으므로 이 결과물은 실제 장애에 대비한 외부 backup이 아니라 **복원 절차 검증용**이다.

### 현재 backup 범위

| 구분 | 대상 | 복구 방법 |
|---|---|---|
| 운영 data backup | `configs/`, `logs/`, `artifacts/` | 검증된 archive에서 복원 |
| Source와 문서 | `src/`, `docs/`, `README.md`, `Dockerfile` 등 Git 추적 파일 | Git 저장소에서 다시 받음 |
| Secret | `.env`, API key, token, private key | 일반 archive에 넣지 않고 별도의 암호화 저장소나 secret manager에서 복구 |

따라서 현재 archive에는 학습 조건, Tool 정책, 실행·감사 기록과 model artifact가 들어간다. Source와 문서를 중복해서 넣지 않는 것은 Git이 그 복구 기준이기 때문이다. 단, 실제 운영에서는 Git remote와 backup archive도 원본 host와 분리된 위치에 있어야 한다.

### 1) 시험 공간과 archive 생성

```bash
backup_test_dir=$(mktemp -d /tmp/mini-ai-ops-backup-test.XXXXXX)
mkdir "$backup_test_dir/restored"
tar -czf "$backup_test_dir/mini-ai-ops-data.tar.gz" configs logs artifacts
```

- 목적: `configs/`, `logs/`, `artifacts/`를 하나의 압축 archive로 backup한다.
- 변경 여부: `/tmp`에 시험 directory와 archive를 생성하지만 project 원본은 변경하지 않는다.
- 성공 기준: `mini-ai-ops-data.tar.gz`가 생성되고 명령이 exit code `0`으로 끝난다.
- 주의: `backup_test_dir` 변수는 이 명령을 실행한 shell에서만 유지되므로 이어지는 명령도 같은 terminal에서 실행한다.

### 2) Archive 내용 확인과 별도 경로 복원

```bash
tar -tzf "$backup_test_dir/mini-ai-ops-data.tar.gz"
tar -xzf "$backup_test_dir/mini-ai-ops-data.tar.gz" -C "$backup_test_dir/restored"
```

- 목적: Archive 안에 보호 대상이 있는지 확인하고 원본과 분리된 경로에 복원한다.
- 변경 여부: 첫 명령은 읽기 전용이고, 두 번째 명령은 `/tmp`의 `restored/` 아래에 파일을 생성한다.
- 성공 기준: 목록에 세 directory가 표시되고 복원 명령이 exit code `0`으로 끝난다.

### 3) 원본과 복원본 일치 확인

```bash
diff -rq configs "$backup_test_dir/restored/configs"
diff -rq logs "$backup_test_dir/restored/logs"
diff -rq artifacts "$backup_test_dir/restored/artifacts"
find "$backup_test_dir/restored/artifacts" -name model.pkl -type f | wc -l
```

- 목적: 원본과 복원본의 파일 내용이 같은지 비교하고 model 개수를 확인한다.
- 변경 여부: 모두 읽기 전용이다.
- 성공 기준: 세 `diff` 명령은 차이 없이 출력이 없고 exit code `0`이며, model 개수가 원본과 같다.

복원된 log는 각 줄이 유효한 JSON인지 추가로 확인한다.

```bash
python -c 'import json; from pathlib import Path; paths = [Path("'$backup_test_dir'/restored/logs/runs.jsonl"), Path("'$backup_test_dir'/restored/logs/audit.jsonl")]; print({str(path): sum(1 for line in path.read_text(encoding="utf-8").splitlines() if json.loads(line)) for path in paths})'
```

- 목적: 파일이 존재하는지만 확인하지 않고 복원된 JSONL record를 실제로 읽을 수 있는지 검증한다.
- 변경 여부: 복원된 log를 읽기만 한다.
- 성공 기준: JSON 오류 없이 각 파일의 record 수가 출력된다.

### 2026-08-20 실제 검증 결과

- Archive: `/tmp/mini-ai-ops-backup-test.ZlqkE5/mini-ai-ops-data.tar.gz`
- Archive 크기: `8.0K`
- Archive SHA-256: `817f68bb13ddd011d8b77d951d3516125e3e206184648c3d71bb66405b8e596f`
- `configs/`, `logs/`, `artifacts/`의 원본·복원본 비교: 차이 없음
- 복원 model: 원본과 같은 17개
- 복원 log: run 21개, audit 12개 record 모두 JSON parsing 성공
- 복원된 `configs/train.yaml`: 기존 config 검증 통과
- 모든 검증 명령: exit code `0`

시험 archive는 `/tmp`에 남아 있으며 system 재시작이나 임시 파일 정리 과정에서 삭제될 수 있다. 실제 backup은 다른 저장장치 또는 별도 계정의 저장소에 보관해야 한다.

## 8. 장애 복구 절차

### Project data 손상·유실

1. 학습과 Tool 실행을 중단해 손상된 log나 artifact에 추가로 쓰지 않는다.
2. 현재 상태를 즉시 삭제하지 말고 별도 위치에 보존해 장애 원인을 조사할 증거를 남긴다.
3. Git에서 신뢰할 수 있는 source와 문서를 준비한다.
4. 사용할 backup archive의 생성 시각과 checksum을 확인한다.
5. Archive를 운영 경로가 아닌 별도 staging directory에 먼저 푼다.
6. Config 검증, JSONL parsing, 원본 record 수와 model checksum을 확인한다.
7. 검증된 복원본만 운영 경로에 반영하고 읽기 전용 조회로 상태를 확인한다.
8. 장애 시각, 마지막 정상 backup, 실제 data 손실 구간과 복구 소요 시간을 기록한다.

복구 확인에는 다음 읽기 전용 명령을 사용한다.

```bash
python -c "from src.config_loader import load_train_config; print(load_train_config('configs/train.yaml'))"
python src/list_runs.py --limit 3
tail -n 3 logs/audit.jsonl
find artifacts -maxdepth 2 -type f -name 'model.pkl' -printf '%p %s bytes\n' | sort
```

- 목적: 복구된 config, 최근 run·audit record와 model 파일이 운영 코드에서 읽히는지 확인한다.
- 변경 여부: 모두 읽기 전용이며 새 run, log 또는 model을 만들지 않는다.
- 성공 기준: Config 검증과 run 조회가 오류 없이 끝나고, audit record와 0 byte보다 큰 model 파일이 표시된다.
- 주의: 출처가 불분명한 pickle model은 확인을 위해서라도 직접 load하지 않는다.

### Backup 생성·복원 실패

- Archive 생성이 실패하면 원본 log와 artifact를 정리하지 않는다.
- Disk 여유 공간, 대상 directory 권한과 실패 메시지를 확인한 뒤 새로운 archive 이름으로 다시 시도한다.
- `tar -tzf <archive-path>`가 실패하면 해당 archive를 운영 경로에 풀지 않는다.
- 복원본 검증이 실패하면 운영 경로를 덮어쓰지 않고 다른 정상 backup을 선택한다.
- 정상 backup이 없다면 남아 있는 Git source, config, log와 artifact를 각각 조사하고 복구 불가능한 구간을 기록한다.

## 9. Secret 노출 대응

Secret이 Git, log, Docker image 또는 공유 archive에 들어갔다면 파일에서 문자열을 지우는 것만으로는 대응이 끝나지 않는다. 이미 복사된 Secret은 계속 사용될 수 있기 때문이다.

1. 노출된 key, token 또는 password를 제공 service에서 즉시 폐기하거나 회전한다.
2. 새 credential의 권한을 필요한 최소 범위로 제한한다.
3. Git history, log, Docker image, backup과 외부 공유 위치까지 노출 범위를 확인한다.
4. 현재 파일에서 Secret을 제거하고 `.env` 또는 승인된 secret 저장소로 옮긴다.
5. History나 공유 archive 정리가 필요하면 협업자와 영향 범위를 확인한 뒤 별도 절차로 수행한다.
6. 이전 credential이 더 이상 작동하지 않고 새 credential만 정상 동작하는지 확인한다.
7. 실제 Secret 값은 다시 기록하지 않고 노출 위치, 시각, 영향과 조치 결과만 사고 기록에 남긴다.

Secret 삭제를 위한 Git history 재작성은 다른 clone과 branch에도 영향을 주므로 자동으로 수행하지 않는다. 먼저 credential을 폐기하는 것이 가장 중요한 차단 조치다.

## 관련 문서

- [프로젝트 README](../README.md)
- [Runbook](runbook.md)
- [Architecture](architecture.md)
- [장애 시나리오](failure-scenarios.md)
