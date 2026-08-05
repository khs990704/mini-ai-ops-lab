# 보안과 백업

## 짧은 정의

보안은 누가 무엇에 접근하거나 무엇을 실행할 수 있는지 통제하는 일이다. 백업과 복구는 데이터가 사라지거나 장애가 발생해도 중요한 정보를 다시 사용할 수 있게 하는 과정이다.

## 이 프로젝트에서 중요한 이유

로그, artifact, config, 비밀정보는 각각 다른 보관 및 접근 규칙이 필요하다. 이 프로젝트는 처음부터 비밀정보 분리, 도구 실행 통제, audit log, artifact와 로그의 백업을 고려한다.

## 저장소에서 사용되는 위치

- `.env.example`
- `.gitignore`
- `configs/`
- `logs/audit.jsonl`
- `artifacts/`
- `src/storage.py`
- 향후 작성할 `docs/security-backup-checklist.md`

## 알아둘 명령어나 코드

```bash
ls -la
find artifacts -maxdepth 2 -type f
du -sh logs artifacts
```

## 흔한 실패 사례

- 실패: 비밀정보가 실수로 Git에 커밋됨
- 증상: API key 또는 password가 Git history나 로그에 나타남
- 확인할 것: `.gitignore`, `.env`, 로그, 저장소 diff
- 복구 방법: 비밀정보를 제거하고 즉시 교체한 뒤 재발 방지 규칙을 문서화함
- 실패: 출처를 신뢰할 수 없는 pickle model을 불러옴
- 증상: model 로딩 과정에서 예상하지 않은 코드가 실행되거나 시스템이 변경됨
- 확인할 것: `model.pkl`의 생성 주체, 전달 경로, 저장 위치
- 복구 방법: 외부 또는 출처가 불명확한 pickle 파일을 열지 않고 신뢰할 수 있는 실행에서 생성된 artifact만 사용함

## 실용적인 이해

운영 시스템은 처음부터 보안과 복구 가능성을 고려해야 한다. 이 프로젝트는 비밀정보를 코드와 분리하고, 도구 호출을 audit log에 기록하며, artifact와 로그의 백업 규칙을 문서화해 검토와 복구가 가능하게 한다.

pickle은 Python 객체를 그대로 저장하고 복원할 수 있어 scikit-learn model artifact에 편리하다. 하지만 pickle 로딩은 단순한 데이터 읽기가 아니며 악의적인 코드가 실행될 수 있으므로, 이 프로젝트에서 직접 생성하고 출처를 확인할 수 있는 `artifacts/{run_id}/model.pkl`만 신뢰한다.

## Codex Q&A 기록

아직 기록된 질문이 없다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
