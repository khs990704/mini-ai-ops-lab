"""학습 실행 기록을 일관된 JSONL 형식으로 저장한다."""

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

# 파일 직접 실행과 module import 모두에서 같은 학습·저장 함수를 사용한다.
if __package__:
    from .storage import generate_run_id, save_model
    from .train_job import train_model
else:
    from storage import generate_run_id, save_model
    from train_job import train_model


RUN_LOG_PATH = Path("logs/runs.jsonl")


def utc_now_iso() -> str:
    """서로 다른 환경에서도 비교할 수 있도록 현재 UTC 시각을 ISO 8601로 반환한다."""
    return datetime.now(UTC).isoformat()


def append_run_log(
    record: Mapping[str, Any], log_path: Path = RUN_LOG_PATH
) -> None:
    """실행 기록 하나를 기존 내용을 보존하면서 JSONL 파일 끝에 추가한다."""
    # 새 환경에서도 로그 경로를 먼저 준비해 파일 생성 실패를 줄인다.
    log_path.parent.mkdir(parents=True, exist_ok=True)

    serialized_record = json.dumps(record, ensure_ascii=False, sort_keys=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        # 한 실행을 한 줄로 구분하면 전체 파일을 읽지 않고도 기록을 추가할 수 있다.
        log_file.write(f"{serialized_record}\n")


def run_training_job() -> dict[str, Any]:
    """학습과 artifact 저장을 실행하고 성공 기록을 남긴다."""
    run_id = generate_run_id()
    started_at = utc_now_iso()
    started_counter = perf_counter()

    model, metrics = train_model()
    artifact_path = save_model(model, run_id)

    # 경과 시간은 시스템 시각 변경에 영향받지 않는 단조 시계로 측정한다.
    duration_seconds = round(perf_counter() - started_counter, 6)
    record = {
        "run_id": run_id,
        "status": "success",
        "started_at": started_at,
        "ended_at": utc_now_iso(),
        "duration_seconds": duration_seconds,
        "metrics": metrics,
        "artifact_path": str(artifact_path),
    }
    append_run_log(record)

    return record


def main() -> None:
    """명령줄에서 학습 작업을 실행하고 저장된 run 기록을 출력한다."""
    record = run_training_job()
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    # 이 파일을 직접 실행했을 때만 새 학습 실행과 로그 기록을 시작한다.
    main()
