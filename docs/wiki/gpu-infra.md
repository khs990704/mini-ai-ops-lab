# GPU 인프라

## 짧은 정의

GPU 인프라는 GPU 장치, driver, CUDA 호환성, memory 사용량, utilization, scheduling과 운영 점검을 포함한다.

## 이 프로젝트에서 중요한 이유

초기 구현에는 실제 GPU가 필요하지 않지만, GPU 기반 학습 작업을 어떻게 확인하고 운영할지는 설명할 수 있어야 한다. CPU 환경에서도 실행 가능하게 유지하면서 GPU 장애 점검 방법을 운영 문서에 연결한다.

## 저장소에서 사용되는 위치

- 향후 작성할 `docs/runbook.md`
- 향후 작성할 `docs/failure-scenarios.md`
- 향후 추가할 GPU 점검 기록 또는 script

## 알아둘 명령어나 코드

```bash
nvidia-smi
watch -n 1 nvidia-smi
```

WSL에서 GPU를 사용할 수 없다면 그 제한을 문서에 기록하고 프로젝트는 CPU에서도 실행 가능하게 유지한다.

## 흔한 실패 사례

- 실패: GPU memory 부족
- 증상: 학습 process가 CUDA OOM 오류로 종료됨
- 확인할 것: `nvidia-smi`, batch size, model size, 다른 process의 memory 사용량
- 복구 방법: batch size를 줄이거나 불필요한 process를 종료하고, 다른 GPU로 옮기거나 scheduling을 조정함

## 실용적인 이해

GPU 운영에서는 장치의 존재 여부뿐 아니라 utilization과 memory를 함께 확인해야 한다. 이 프로젝트가 CPU로 실행되더라도 runbook에는 `nvidia-smi` 점검 방법과 OOM 장애 대응 방법을 기록한다.

## Codex Q&A 기록

아직 기록된 질문이 없다.

## 관련 문서

- [프로젝트 계획](../project-plan.md)
- [일별 작업 흐름](../daily-codex-workflow.md)
