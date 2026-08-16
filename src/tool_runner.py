"""Allowlist에 등록된 Tool 요청만 미리 구현된 handler로 실행한다."""

import argparse
import json
import sys
from collections.abc import Callable
from math import isfinite
from multiprocessing import get_context
from multiprocessing.connection import Connection
from pathlib import Path
from time import perf_counter
from typing import Any, TypedDict

# 파일 직접 실행과 module import 모두에서 같은 Tool 설정 loader를 사용한다.
if __package__:
    from .audit_logger import append_audit_log, create_audit_record, utc_now_iso
    from .list_runs import RUN_LOG_PATH, get_experiment_name, load_recent_runs
    from .run_job import run_training_job
    from .storage import ARTIFACT_ROOT
    from .tool_config_loader import (
        DEFAULT_TOOL_CONFIG_PATH,
        ToolDefinition,
        load_tool_config,
    )
else:
    from audit_logger import append_audit_log, create_audit_record, utc_now_iso
    from list_runs import RUN_LOG_PATH, get_experiment_name, load_recent_runs
    from run_job import run_training_job
    from storage import ARTIFACT_ROOT
    from tool_config_loader import (
        DEFAULT_TOOL_CONFIG_PATH,
        ToolDefinition,
        load_tool_config,
    )


class ToolResult(TypedDict):
    """Agent가 성공과 실패를 같은 구조로 처리할 수 있는 실행 결과다."""

    tool_name: str
    status: str
    result: Any
    error_type: str | None
    error_message: str | None


class ToolNotAllowedError(ValueError):
    """Allowlist에 없는 Tool 요청임을 구분한다."""


class ToolHandlerNotImplementedError(ValueError):
    """등록됐지만 아직 안전한 handler가 없는 Tool 요청임을 구분한다."""


class ToolTimeoutError(TimeoutError):
    """Tool handler가 허용된 실행 시간을 넘겼음을 구분한다."""


class ToolHandlerExecutionError(RuntimeError):
    """별도 process에서 발생한 handler 오류의 원래 정보를 전달한다."""

    def __init__(self, error_type: str, error_message: str) -> None:
        super().__init__(error_message)
        self.error_type = error_type
        self.error_message = error_message


DEFAULT_TIMEOUT_SECONDS = 30.0


def handle_echo(tool_input: str | None) -> str:
    """파일이나 외부 명령에 접근하지 않고 입력 문자열을 그대로 반환한다."""
    # input_type 검증을 먼저 수행하므로 echo handler에는 항상 문자열이 전달된다.
    assert tool_input is not None
    return tool_input


def handle_list_artifacts(tool_input: str | None) -> dict[str, Any]:
    """Project가 생성한 model artifact 경로와 run ID를 조회한다."""
    del tool_input
    artifact_paths = sorted(ARTIFACT_ROOT.glob("*/model.pkl"))
    artifacts = [
        {
            "run_id": artifact_path.parent.name,
            "artifact_path": str(artifact_path),
        }
        for artifact_path in artifact_paths
        if artifact_path.is_file()
    ]
    return {
        "count": len(artifacts),
        "artifacts": artifacts,
    }


def handle_read_log_summary(tool_input: str | None) -> dict[str, Any]:
    """최근 학습 run의 운영 판단에 필요한 field만 요약한다."""
    del tool_input
    recent_records = load_recent_runs(RUN_LOG_PATH, limit=5, experiment_name=None)
    summaries = []
    for record in recent_records:
        metrics = record.get("metrics")
        accuracy = metrics.get("accuracy") if isinstance(metrics, dict) else None
        summaries.append(
            {
                "run_id": record.get("run_id"),
                "experiment_name": get_experiment_name(record),
                "status": record.get("status"),
                "started_at": record.get("started_at"),
                "accuracy": accuracy,
                "artifact_path": record.get("artifact_path"),
                "error_type": record.get("error_type"),
                "error_message": record.get("error_message"),
            }
        )

    return {
        "count": len(summaries),
        "runs": summaries,
    }


def handle_run_train_job(tool_input: str | None) -> dict[str, Any]:
    """기본 학습 설정으로 새 run을 실행하고 핵심 결과를 반환한다."""
    del tool_input
    record = run_training_job()
    return {
        # Tool 실행 상태와 내부 학습 상태를 구분해 Agent가 결과를 판단하게 한다.
        "run_id": record["run_id"],
        "training_status": record["status"],
        "metrics": record["metrics"],
        "artifact_path": record["artifact_path"],
        "error_type": record["error_type"],
        "error_message": record["error_message"],
    }


# 설정의 이름을 shell 명령으로 해석하지 않고 검토된 Python 함수에만 연결한다.
TOOL_HANDLERS: dict[str, Callable[[str | None], Any]] = {
    "echo": handle_echo,
    "list_artifacts": handle_list_artifacts,
    "read_log_summary": handle_read_log_summary,
    "run_train_job": handle_run_train_job,
}


def run_handler_in_child(
    handler: Callable[[str | None], Any],
    tool_input: str | None,
    connection: Connection,
) -> None:
    """Handler 결과나 오류를 부모 process에 전달하고 실행을 격리한다."""
    try:
        result = handler(tool_input)
        connection.send(
            {
                "succeeded": True,
                "result": result,
                "error_type": None,
                "error_message": None,
            }
        )
    except Exception as error:
        connection.send(
            {
                "succeeded": False,
                "result": None,
                "error_type": type(error).__name__,
                "error_message": str(error),
            }
        )
    finally:
        connection.close()


def execute_handler_with_timeout(
    tool_name: str,
    handler: Callable[[str | None], Any],
    tool_input: str | None,
    timeout_seconds: float,
) -> Any:
    """별도 process의 결과를 제한 시간만 기다리고 초과 시 종료한다."""
    if not isfinite(timeout_seconds) or timeout_seconds < 0:
        raise ValueError("timeout은 0 이상의 유한한 숫자여야 합니다.")

    context = get_context("fork")
    receive_connection, send_connection = context.Pipe(duplex=False)
    process = context.Process(
        target=run_handler_in_child,
        args=(handler, tool_input, send_connection),
    )
    process.start()
    # 부모는 결과를 읽기만 하므로 불필요한 송신 endpoint를 즉시 닫는다.
    send_connection.close()

    try:
        if not receive_connection.poll(timeout_seconds):
            process.terminate()
            process.join(timeout=1)
            if process.is_alive():
                # terminate 신호에도 끝나지 않는 process까지 남기지 않는다.
                process.kill()
                process.join()
            raise ToolTimeoutError(
                f"{tool_name} Tool이 제한 시간 {timeout_seconds}초를 초과했습니다."
            )

        try:
            payload = receive_connection.recv()
        except EOFError as error:
            raise ToolHandlerExecutionError(
                "ChildProcessError",
                f"{tool_name} Tool process가 결과 없이 종료됐습니다.",
            ) from error
    finally:
        receive_connection.close()

    process.join()
    if not payload["succeeded"]:
        raise ToolHandlerExecutionError(
            payload["error_type"],
            payload["error_message"],
        )
    return payload["result"]


def validate_tool_input(
    tool_name: str,
    definition: ToolDefinition,
    tool_input: str | None,
) -> None:
    """Tool 설정에 선언한 입력 형태와 실제 요청이 일치하는지 확인한다."""
    input_type = definition["input_type"]
    if input_type == "text" and tool_input is None:
        raise ValueError(f"{tool_name} Tool에는 --input 문자열이 필요합니다.")
    if input_type == "none" and tool_input is not None:
        raise ValueError(f"{tool_name} Tool은 --input을 받지 않습니다.")


def execute_tool(
    tool_name: str,
    tool_input: str | None = None,
    config_path: str | Path = DEFAULT_TOOL_CONFIG_PATH,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> ToolResult:
    """요청을 allowlist와 비교한 뒤 고정된 handler만 실행한다."""
    config = load_tool_config(config_path)
    definition = config["tools"].get(tool_name)
    if definition is None:
        # 등록되지 않은 이름은 handler 조회 전에 거부해 기본 차단 정책을 적용한다.
        raise ToolNotAllowedError(
            f"Allowlist에 등록되지 않은 Tool입니다: {tool_name}"
        )

    validate_tool_input(tool_name, definition, tool_input)

    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        # YAML 등록만으로 임의 기능이 실행되지 않도록 실제 구현도 별도로 확인한다.
        raise ToolHandlerNotImplementedError(
            f"안전한 handler가 아직 구현되지 않은 Tool입니다: {tool_name}"
        )

    return {
        "tool_name": tool_name,
        "status": "success",
        "result": execute_handler_with_timeout(
            tool_name,
            handler,
            tool_input,
            timeout_seconds,
        ),
        "error_type": None,
        "error_message": None,
    }


def build_failed_result(
    tool_name: str,
    error: Exception,
    status: str = "failed",
) -> ToolResult:
    """거부 또는 실행 실패를 Agent가 해석할 수 있는 구조로 변환한다."""
    if isinstance(error, ToolHandlerExecutionError):
        error_type = error.error_type
        error_message = error.error_message
    else:
        error_type = type(error).__name__
        error_message = str(error)

    return {
        "tool_name": tool_name,
        "status": status,
        "result": None,
        "error_type": error_type,
        "error_message": error_message,
    }


def run_tool_request(
    tool_name: str,
    tool_input: str | None = None,
    config_path: str | Path = DEFAULT_TOOL_CONFIG_PATH,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> ToolResult:
    """Tool 요청을 실행하고 성공·거부·실패 결과를 빠짐없이 감사 기록한다."""
    started_at = utc_now_iso()
    started_counter = perf_counter()

    try:
        result = execute_tool(
            tool_name,
            tool_input,
            config_path,
            timeout_seconds,
        )
    except ToolTimeoutError as error:
        result = build_failed_result(tool_name, error, status="timeout")
    except Exception as error:
        # 예상하지 못한 handler 오류도 같은 결과 구조와 audit field로 추적한다.
        result = build_failed_result(tool_name, error)

    audit_record = create_audit_record(
        tool_name=tool_name,
        status=result["status"],
        started_at=started_at,
        started_counter=started_counter,
        input_provided=tool_input is not None,
        error_type=result["error_type"],
        error_message=result["error_message"],
        timeout_seconds=timeout_seconds,
    )
    # Tool 결과만 출력하고 이력을 잃는 상황을 막기 위해 반환 전에 기록한다.
    append_audit_log(audit_record)
    return result


def non_negative_float(value: str) -> float:
    """Timeout 값이 0 이상의 유한한 숫자인지 CLI 단계에서 검증한다."""
    parsed_value = float(value)
    if not isfinite(parsed_value) or parsed_value < 0:
        raise argparse.ArgumentTypeError(
            "timeout은 0 이상의 유한한 숫자여야 합니다."
        )
    return parsed_value


def parse_args() -> argparse.Namespace:
    """Tool 이름, 선택 입력과 allowlist 경로를 명령줄에서 읽는다."""
    parser = argparse.ArgumentParser(
        description="Allowlist에 등록된 Agent Tool을 실행합니다."
    )
    parser.add_argument("--tool", required=True, help="실행할 Tool 이름")
    parser.add_argument("--input", help="text 입력을 받는 Tool에 전달할 문자열")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_TOOL_CONFIG_PATH,
        help=f"Tool 설정 YAML 경로 (기본값: {DEFAULT_TOOL_CONFIG_PATH})",
    )
    parser.add_argument(
        "--timeout",
        type=non_negative_float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Tool 실행 제한 시간(초) (기본값: {DEFAULT_TIMEOUT_SECONDS})",
    )
    return parser.parse_args()


def main() -> int:
    """구조화된 결과를 출력하고 성공 여부를 process exit code로 알린다."""
    args = parse_args()
    try:
        result = run_tool_request(
            args.tool,
            args.input,
            args.config,
            args.timeout,
        )
    except OSError as error:
        # Audit log를 남기지 못한 실행은 운영상 완료로 간주하지 않는다.
        result = build_failed_result(args.tool, error)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1

    output_stream = sys.stdout if result["status"] == "success" else sys.stderr
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=output_stream)
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
