"""학습 실행을 관리하고 결과를 일관된 JSONL 형식으로 저장한다."""

import argparse
import json
import sys
import traceback
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


def parse_args() -> argparse.Namespace:
    """실패 처리 경로를 안전하게 검증할 수 있는 CLI option을 해석한다."""
    parser = argparse.ArgumentParser(description="Iris 학습 작업을 실행합니다.")
    parser.add_argument(
        "--fail",
        action="store_true",
        help="실패 처리 검증을 위해 의도적인 오류를 발생시킵니다.",
    )
    return parser.parse_args()


def run_training_job(force_failure: bool = False) -> dict[str, Any]:
    """학습 작업을 실행하고 성공 또는 실패 결과를 빠짐없이 기록한다."""
    run_id = generate_run_id()
    started_at = utc_now_iso()
    started_counter = perf_counter()

    try:
        if force_failure:
            # 외부 환경을 손상시키지 않고 같은 실패를 반복해 처리 경로를 검증한다.
            raise RuntimeError("검증을 위해 의도적으로 발생시킨 학습 실패입니다.")

        model, metrics = train_model()
        artifact_path = save_model(model, run_id)
        record = {
            "run_id": run_id,
            "status": "success",
            "started_at": started_at,
            "ended_at": utc_now_iso(),
            # 경과 시간은 시스템 시각 변경에 영향받지 않는 단조 시계로 측정한다.
            "duration_seconds": round(perf_counter() - started_counter, 6),
            "metrics": metrics,
            "artifact_path": str(artifact_path),
            "error_type": None,
            "error_message": None,
            "traceback": None,
        }
    except Exception as error:
        # 실패해도 동일한 run ID로 원인과 실행 시점을 추적할 수 있게 record를 완성한다.
        record = {
            "run_id": run_id,
            "status": "failed",
            "started_at": started_at,
            "ended_at": utc_now_iso(),
            "duration_seconds": round(perf_counter() - started_counter, 6),
            "metrics": None,
            "artifact_path": None,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }

    append_run_log(record)

    return record


def main() -> int:
    """저장된 run 기록을 출력하고 상태에 맞는 process exit code를 반환한다."""
    args = parse_args()
    record = run_training_job(force_failure=args.fail)
    output_stream = sys.stderr if record["status"] == "failed" else sys.stdout
    print(
        json.dumps(record, ensure_ascii=False, sort_keys=True),
        file=output_stream,
    )
    return 1 if record["status"] == "failed" else 0


if __name__ == "__main__":
    # 이 파일을 직접 실행했을 때만 새 학습 실행과 로그 기록을 시작한다.
    raise SystemExit(main())
