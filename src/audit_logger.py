"""Agent Tool 요청의 실행 결과와 시간을 JSONL 감사 기록으로 보존한다."""

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, TypedDict


AUDIT_LOG_PATH = Path("logs/audit.jsonl")


class AuditRecord(TypedDict):
    """Tool 요청 하나를 나중에 추적하는 데 필요한 감사 field다."""

    tool_name: str
    status: str
    started_at: str
    ended_at: str
    duration_seconds: float
    input_provided: bool
    timeout_seconds: float | None
    error_type: str | None
    error_message: str | None


def utc_now_iso() -> str:
    """환경과 관계없이 비교할 수 있는 UTC ISO 8601 시각을 반환한다."""
    return datetime.now(UTC).isoformat()


def create_audit_record(
    *,
    tool_name: str,
    status: str,
    started_at: str,
    started_counter: float,
    input_provided: bool,
    error_type: str | None,
    error_message: str | None,
    timeout_seconds: float | None = None,
) -> AuditRecord:
    """요청의 종료 시각과 경과 시간을 더해 일관된 감사 record를 만든다."""
    return {
        "tool_name": tool_name,
        "status": status,
        "started_at": started_at,
        "ended_at": utc_now_iso(),
        # 시스템 시각이 조정돼도 duration이 역행하지 않도록 단조 시계를 사용한다.
        "duration_seconds": round(perf_counter() - started_counter, 6),
        # 원문 입력 대신 제공 여부만 남겨 불필요한 민감정보 기록을 줄인다.
        "input_provided": input_provided,
        "timeout_seconds": timeout_seconds,
        "error_type": error_type,
        "error_message": error_message,
    }


def append_audit_log(
    record: Mapping[str, Any],
    log_path: Path = AUDIT_LOG_PATH,
) -> None:
    """기존 감사 이력을 보존하면서 Tool 요청 한 건을 파일 끝에 추가한다."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    serialized_record = json.dumps(record, ensure_ascii=False, sort_keys=True)
    with log_path.open("a", encoding="utf-8") as log_file:
        # 요청 하나를 한 줄에 저장해 전체 파일을 다시 쓰지 않고 계속 누적한다.
        log_file.write(f"{serialized_record}\n")
