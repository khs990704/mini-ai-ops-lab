"""원본 run과 재현 run의 조건, 결과와 artifact를 비교한다."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


RUN_LOG_PATH = Path("logs/runs.jsonl")


def parse_args() -> argparse.Namespace:
    """비교할 원본 run ID와 재현 후보 run ID를 읽는다."""
    parser = argparse.ArgumentParser(description="두 성공 run의 재현 결과를 비교합니다.")
    parser.add_argument("--source-run", required=True, help="재현 기준인 원본 run ID")
    parser.add_argument("--candidate-run", required=True, help="재현한 후보 run ID")
    return parser.parse_args()


def load_run_records(log_path: Path) -> dict[str, dict[str, Any]]:
    """run ID로 정확히 한 record를 찾을 수 있도록 JSONL을 읽는다."""
    records: dict[str, dict[str, Any]] = {}

    with log_path.open(encoding="utf-8") as log_file:
        for line_number, line in enumerate(log_file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{line_number}번째 JSONL record를 읽을 수 없습니다: {error}"
                ) from error

            if not isinstance(record, dict) or not isinstance(record.get("run_id"), str):
                raise ValueError(
                    f"{line_number}번째 record에 유효한 run_id가 없습니다."
                )

            run_id = record["run_id"]
            if run_id in records:
                raise ValueError(f"중복된 run_id가 있습니다: {run_id}")
            records[run_id] = record

    return records


def require_successful_run(
    records: dict[str, dict[str, Any]], run_id: str, role: str
) -> dict[str, Any]:
    """재현 비교에는 결과와 artifact가 있는 성공 run만 허용한다."""
    if run_id not in records:
        raise ValueError(f"{role} run을 찾을 수 없습니다: {run_id}")

    record = records[run_id]
    if record.get("status") != "success":
        raise ValueError(
            f"{role} run은 success 상태여야 합니다: "
            f"{run_id} ({record.get('status', '-')})"
        )
    if not isinstance(record.get("parameters"), dict):
        raise ValueError(f"{role} run에 비교할 parameters가 없습니다: {run_id}")
    if not isinstance(record.get("metrics"), dict):
        raise ValueError(f"{role} run에 비교할 metrics가 없습니다: {run_id}")
    if not isinstance(record.get("artifact_path"), str):
        raise ValueError(f"{role} run에 artifact_path가 없습니다: {run_id}")

    return record


def compare_runs(
    source: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    """재현돼야 할 값과 실행마다 달라야 할 식별값을 구분해 비교한다."""
    source_artifact = Path(source["artifact_path"])
    candidate_artifact = Path(candidate["artifact_path"])
    checks = {
        "experiment_name_matches": (
            source.get("experiment_name") == candidate.get("experiment_name")
        ),
        "parameters_match": source["parameters"] == candidate["parameters"],
        "metrics_match": source["metrics"] == candidate["metrics"],
        "source_artifact_exists": source_artifact.is_file(),
        "candidate_artifact_exists": candidate_artifact.is_file(),
        "run_ids_are_distinct": source["run_id"] != candidate["run_id"],
        "artifact_paths_are_distinct": source_artifact != candidate_artifact,
    }

    return {
        "source_run_id": source["run_id"],
        "candidate_run_id": candidate["run_id"],
        "source_artifact_path": str(source_artifact),
        "candidate_artifact_path": str(candidate_artifact),
        "checks": checks,
        "reproduced": all(checks.values()),
    }


def main() -> int:
    """비교 결과를 JSON으로 출력하고 재현 여부를 process 상태로 반환한다."""
    args = parse_args()

    if args.source_run == args.candidate_run:
        print("원본 run과 재현 run은 서로 달라야 합니다.", file=sys.stderr)
        return 1

    try:
        records = load_run_records(RUN_LOG_PATH)
        source = require_successful_run(records, args.source_run, "원본")
        candidate = require_successful_run(records, args.candidate_run, "재현 후보")
    except (OSError, ValueError) as error:
        print(f"run을 비교할 수 없습니다: {error}", file=sys.stderr)
        return 1

    result = compare_runs(source, candidate)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
