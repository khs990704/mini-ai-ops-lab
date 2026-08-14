"""공통 Tool allowlist를 안전하게 읽고 실행 전에 구조를 검증한다."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import TypedDict

import yaml


DEFAULT_TOOL_CONFIG_PATH = Path("configs/tools.yaml")
TOOL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_DEFINITION_KEYS = {"description", "input_type", "access", "resources"}
ALLOWED_INPUT_TYPES = {"none", "text"}
ALLOWED_ACCESS_LEVELS = {"none", "read", "write"}


class ToolDefinition(TypedDict):
    """검증을 통과한 도구 하나의 입력과 접근 범위를 나타낸다."""

    description: str
    input_type: str
    access: str
    resources: list[str]


class ToolConfig(TypedDict):
    """모든 Agent 요청에 공통으로 적용할 allowlist 구조다."""

    tools: dict[str, ToolDefinition]


def validate_resource(resource: object, tool_name: str) -> str:
    """Resource가 project root 밖을 가리키는 위험한 경로인지 확인한다."""
    if not isinstance(resource, str) or not resource.strip():
        raise ValueError(f"{tool_name}.resources에는 비어 있지 않은 문자열만 허용됩니다.")

    normalized_resource = resource.strip()
    resource_path = Path(normalized_resource)
    if resource_path.is_absolute() or ".." in resource_path.parts:
        raise ValueError(
            f"{tool_name}.resources에는 project 내부 상대 경로만 허용됩니다: "
            f"{normalized_resource}"
        )
    return normalized_resource


def validate_tool_definition(tool_name: str, raw_definition: object) -> ToolDefinition:
    """도구의 설명, 입력 형태와 최소 접근 범위를 검증한다."""
    if not isinstance(raw_definition, dict):
        raise ValueError(f"{tool_name} 정의는 YAML 객체여야 합니다.")
    if not all(isinstance(key, str) for key in raw_definition):
        raise ValueError(f"{tool_name} 정의의 key는 문자열이어야 합니다.")

    definition_keys = set(raw_definition)
    missing_keys = REQUIRED_DEFINITION_KEYS - definition_keys
    unexpected_keys = definition_keys - REQUIRED_DEFINITION_KEYS
    if missing_keys:
        raise ValueError(
            f"{tool_name}에 필수 설정이 없습니다: {', '.join(sorted(missing_keys))}"
        )
    if unexpected_keys:
        raise ValueError(
            f"{tool_name}에 지원하지 않는 설정이 있습니다: "
            f"{', '.join(sorted(unexpected_keys))}"
        )

    description = raw_definition["description"]
    input_type = raw_definition["input_type"]
    access = raw_definition["access"]
    resources = raw_definition["resources"]

    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"{tool_name}.description은 비어 있지 않은 문자열이어야 합니다.")
    if input_type not in ALLOWED_INPUT_TYPES:
        raise ValueError(
            f"{tool_name}.input_type은 다음 중 하나여야 합니다: "
            f"{', '.join(sorted(ALLOWED_INPUT_TYPES))}"
        )
    if access not in ALLOWED_ACCESS_LEVELS:
        raise ValueError(
            f"{tool_name}.access는 다음 중 하나여야 합니다: "
            f"{', '.join(sorted(ALLOWED_ACCESS_LEVELS))}"
        )
    if not isinstance(resources, list):
        raise ValueError(f"{tool_name}.resources는 목록이어야 합니다.")

    validated_resources = [
        validate_resource(resource, tool_name) for resource in resources
    ]
    if access == "none" and validated_resources:
        raise ValueError(f"{tool_name}은 access가 none이므로 resources가 없어야 합니다.")
    if access in {"read", "write"} and not validated_resources:
        raise ValueError(
            f"{tool_name}은 access가 {access}이므로 resources가 하나 이상 필요합니다."
        )

    return {
        "description": description.strip(),
        "input_type": input_type,
        "access": access,
        "resources": validated_resources,
    }


def load_tool_config(config_path: str | Path) -> ToolConfig:
    """YAML allowlist를 읽고 검증된 도구 정의만 반환한다."""
    path = Path(config_path)

    try:
        with path.open(encoding="utf-8") as config_file:
            raw_config = yaml.safe_load(config_file)
    except yaml.YAMLError as error:
        raise ValueError(f"YAML 형식이 올바르지 않습니다: {path}") from error

    if not isinstance(raw_config, dict) or set(raw_config) != {"tools"}:
        raise ValueError("Tool 설정의 최상위에는 tools 객체 하나만 있어야 합니다.")

    raw_tools = raw_config["tools"]
    if not isinstance(raw_tools, dict) or not raw_tools:
        raise ValueError("tools는 하나 이상의 도구를 포함한 YAML 객체여야 합니다.")

    validated_tools: dict[str, ToolDefinition] = {}
    for tool_name, raw_definition in raw_tools.items():
        if not isinstance(tool_name, str) or not TOOL_NAME_PATTERN.fullmatch(tool_name):
            raise ValueError(
                "도구 이름은 영문 소문자로 시작하고 소문자, 숫자, 밑줄만 "
                f"사용해야 합니다: {tool_name}"
            )
        validated_tools[tool_name] = validate_tool_definition(
            tool_name, raw_definition
        )

    return {"tools": validated_tools}


def parse_args() -> argparse.Namespace:
    """검증할 Tool allowlist 경로를 명령줄에서 읽는다."""
    parser = argparse.ArgumentParser(description="Tool allowlist를 검증합니다.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_TOOL_CONFIG_PATH,
        help=f"Tool 설정 YAML 경로 (기본값: {DEFAULT_TOOL_CONFIG_PATH})",
    )
    return parser.parse_args()


def main() -> int:
    """검증된 allowlist를 출력하고 오류를 process 상태로 알린다."""
    args = parse_args()
    try:
        config = load_tool_config(args.config)
    except (OSError, ValueError) as error:
        print(f"Tool 설정을 읽을 수 없습니다: {error}", file=sys.stderr)
        return 1

    print(json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
