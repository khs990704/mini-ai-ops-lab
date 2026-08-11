"""설정 파일에 따라 Iris 분류 모델을 학습하고 결과를 JSON으로 출력한다."""

import argparse
import json
from pathlib import Path

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# 파일 직접 실행과 `src.train_job` module import에서 모두 storage를 찾도록 한다.
if __package__:
    from .config_loader import (
        DEFAULT_TRAIN_CONFIG_PATH,
        TrainConfig,
        load_train_config,
    )
    from .storage import generate_run_id, save_model
else:
    from config_loader import DEFAULT_TRAIN_CONFIG_PATH, TrainConfig, load_train_config
    from storage import generate_run_id, save_model


def parse_args() -> argparse.Namespace:
    """명령줄에서 사용할 학습 설정 파일 경로를 읽는다."""
    parser = argparse.ArgumentParser(description="Iris 분류 모델을 학습합니다.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_TRAIN_CONFIG_PATH,
        help=f"학습 설정 YAML 경로 (기본값: {DEFAULT_TRAIN_CONFIG_PATH})",
    )
    return parser.parse_args()


def load_and_split_data(config: TrainConfig):
    """설정된 비율과 난수값으로 Iris 데이터를 학습용과 검증용으로 나눈다."""
    dataset = load_iris()

    return train_test_split(
        dataset.data,
        dataset.target,
        test_size=config["test_size"],
        random_state=config["random_state"],
        # 세 품종의 비율이 학습·검증 데이터에서 비슷하게 유지되도록 한다.
        stratify=dataset.target,
    )


def train_model(config: TrainConfig | None = None):
    """분류 모델을 학습하고 검증 accuracy와 sample 수를 반환한다."""
    # 기존 호출 경로도 설정 기반으로 동작하도록 기본 설정을 불러온다.
    resolved_config = config or load_train_config(DEFAULT_TRAIN_CONFIG_PATH)
    x_train, x_test, y_train, y_test = load_and_split_data(resolved_config)

    model = LogisticRegression(max_iter=resolved_config["max_iterations"])
    model.fit(x_train, y_train)

    # 학습에 사용하지 않은 데이터로 평가해 새 데이터에 대한 성능을 확인한다.
    predictions = model.predict(x_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "train_samples": len(y_train),
        "test_samples": len(y_test),
    }

    # 다음 작업일에 같은 모델 객체를 artifact로 저장할 수 있도록 함께 반환한다.
    return model, metrics


def main():
    """학습 실행을 식별하고 model 저장 결과를 JSON 한 줄로 출력한다."""
    args = parse_args()
    config = load_train_config(args.config)
    run_id = generate_run_id()
    model, metrics = train_model(config)
    artifact_path = save_model(model, run_id)
    result = {
        "run_id": run_id,
        "metrics": metrics,
        "artifact_path": str(artifact_path),
        "config_path": str(args.config),
        "config": config,
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    # 이 파일을 직접 실행했을 때만 학습 작업을 시작한다.
    main()
