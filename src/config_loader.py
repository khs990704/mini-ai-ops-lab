"""학습 설정 파일을 안전하게 읽고 실행 전에 값의 유효성을 확인한다."""

from pathlib import Path
from typing import TypedDict

import yaml


DEFAULT_TRAIN_CONFIG_PATH = Path("configs/train.yaml")


class TrainConfig(TypedDict):
    """학습 코드가 사용하는 검증 완료 설정의 구조를 나타낸다."""

    experiment_name: str
    test_size: float
    random_state: int
    max_iterations: int


REQUIRED_KEYS = {
    "experiment_name",
    "test_size",
    "random_state",
    "max_iterations",
}


def load_train_config(config_path: str | Path) -> TrainConfig:
    """YAML 설정을 읽고 잘못된 실험 조건이 학습에 전달되지 않게 검증한다."""
    path = Path(config_path)

    try:
        with path.open(encoding="utf-8") as config_file:
            raw_config = yaml.safe_load(config_file)
    except yaml.YAMLError as error:
        raise ValueError(f"YAML 형식이 올바르지 않습니다: {path}") from error

    if not isinstance(raw_config, dict):
        raise ValueError("학습 설정은 키와 값으로 구성된 YAML 객체여야 합니다.")
    if not all(isinstance(key, str) for key in raw_config):
        raise ValueError("학습 설정의 키는 문자열이어야 합니다.")

    config_keys = set(raw_config)
    missing_keys = REQUIRED_KEYS - config_keys
    unexpected_keys = config_keys - REQUIRED_KEYS
    if missing_keys:
        raise ValueError(f"필수 설정이 없습니다: {', '.join(sorted(missing_keys))}")
    if unexpected_keys:
        raise ValueError(f"지원하지 않는 설정입니다: {', '.join(sorted(unexpected_keys))}")

    experiment_name = raw_config["experiment_name"]
    test_size = raw_config["test_size"]
    random_state = raw_config["random_state"]
    max_iterations = raw_config["max_iterations"]

    # 식별 가능한 이름을 강제해 이름 없는 run이 새로 쌓이지 않게 한다.
    if not isinstance(experiment_name, str) or not experiment_name.strip():
        raise ValueError("experiment_name은 비어 있지 않은 문자열이어야 합니다.")
    if len(experiment_name.strip()) > 100:
        raise ValueError("experiment_name은 100자 이하여야 합니다.")

    # bool은 Python에서 int의 하위 형식이므로 명시적으로 제외한다.
    if isinstance(test_size, bool) or not isinstance(test_size, (int, float)):
        raise ValueError("test_size는 0과 1 사이의 숫자여야 합니다.")
    if not 0 < test_size < 1:
        raise ValueError("test_size는 0보다 크고 1보다 작아야 합니다.")
    if isinstance(random_state, bool) or not isinstance(random_state, int):
        raise ValueError("random_state는 0 이상의 정수여야 합니다.")
    if not 0 <= random_state <= 2**32 - 1:
        raise ValueError("random_state는 0 이상 2^32 - 1 이하의 정수여야 합니다.")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
        raise ValueError("max_iterations는 양의 정수여야 합니다.")
    if max_iterations <= 0:
        raise ValueError("max_iterations는 0보다 커야 합니다.")

    return {
        "experiment_name": experiment_name.strip(),
        "test_size": float(test_size),
        "random_state": random_state,
        "max_iterations": max_iterations,
    }
