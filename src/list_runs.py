"""최근 학습 run의 실험, parameter, metric과 artifact를 비교해 출력한다."""

import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any


RUN_LOG_PATH = Path("logs/runs.jsonl")
HEADERS = (
    "started_at",
    "experiment_name",
    "status",
    "accuracy",
    "test_size",
    "random_state",
    "max_iterations",
    "run_id",
    "artifact_path",
)


def positive_int(value: str) -> int:
    """조회 개수가 1 이상인지 명령 실행 전에 검증한다."""
    parsed_value = int(value)
    if parsed_value < 1:
        raise argparse.ArgumentTypeError("limit은 1 이상의 정수여야 합니다.")
    return parsed_value


def parse_args() -> argparse.Namespace:
    """최근 run 조회 개수와 선택적인 실험 이름을 읽는다."""
    parser = argparse.ArgumentParser(description="최근 학습 run을 비교합니다.")
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=5,
        help="출력할 최근 run 개수 (기본값: 5)",
    )
    parser.add_argument(
        "--experiment",
        help="지정한 experiment_name의 run만 출력합니다.",
    )
    return parser.parse_args()


def get_experiment_name(record: dict[str, Any]) -> Any:
    """새 field가 없는 과거 record에서는 config를 대체 정보로 확인한다."""
    if record.get("experiment_name") is not None:
        return record["experiment_name"]

    config = record.get("config")
    if isinstance(config, dict):
        return config.get("experiment_name")
    return None


def get_parameters(record: dict[str, Any]) -> dict[str, Any]:
    """Day 9 이전 record도 비교할 수 있도록 config에서 parameter를 보완한다."""
    parameters = record.get("parameters")
    if isinstance(parameters, dict):
        return parameters

    config = record.get("config")
    return config if isinstance(config, dict) else {}


def load_recent_runs(
    log_path: Path,
    limit: int,
    experiment_name: str | None,
) -> list[dict[str, Any]]:
    """조건에 맞는 최근 record만 메모리에 유지하고 최신순으로 반환한다."""
    recent_records: deque[dict[str, Any]] = deque(maxlen=limit)

    with log_path.open(encoding="utf-8") as log_file:
        for line_number, line in enumerate(log_file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                # 일부 line이 손상돼도 나머지 운영 기록은 조회할 수 있게 건너뛴다.
                print(
                    f"경고: {line_number}번째 JSONL record를 읽지 못해 건너뜁니다: {error}",
                    file=sys.stderr,
                )
                continue

            if not isinstance(record, dict):
                print(
                    f"경고: {line_number}번째 JSONL 값이 객체가 아니어서 건너뜁니다.",
                    file=sys.stderr,
                )
                continue
            if (
                experiment_name is not None
                and get_experiment_name(record) != experiment_name
            ):
                continue

            recent_records.append(record)

    return list(reversed(recent_records))


def display_value(value: Any) -> str:
    """값이 없는 과거·실패 record를 동일한 표시로 구분한다."""
    return "-" if value is None else str(value)


def record_to_row(record: dict[str, Any]) -> tuple[str, ...]:
    """중첩된 run record를 비교용 한 줄로 변환한다."""
    metrics = record.get("metrics")
    accuracy = metrics.get("accuracy") if isinstance(metrics, dict) else None
    parameters = get_parameters(record)

    return tuple(
        display_value(value)
        for value in (
            record.get("started_at"),
            get_experiment_name(record),
            record.get("status"),
            accuracy,
            parameters.get("test_size"),
            parameters.get("random_state"),
            parameters.get("max_iterations"),
            record.get("run_id"),
            record.get("artifact_path"),
        )
    )


def print_runs(records: list[dict[str, Any]]) -> None:
    """shell에서 복사하거나 비교하기 쉬운 tab 구분 표를 출력한다."""
    print("\t".join(HEADERS))
    for record in records:
        print("\t".join(record_to_row(record)))


def main() -> int:
    """최근 run을 읽어 출력하고 로그 접근 실패를 process 상태로 알린다."""
    args = parse_args()

    try:
        records = load_recent_runs(RUN_LOG_PATH, args.limit, args.experiment)
    except OSError as error:
        print(f"run log를 읽을 수 없습니다: {error}", file=sys.stderr)
        return 1

    print_runs(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
