"""Iris 분류 모델을 학습하고 검증 metrics를 JSON으로 출력한다."""

import json

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


TEST_SIZE = 0.2
RANDOM_STATE = 42
MAX_ITERATIONS = 200


def load_and_split_data():
    """Iris 데이터를 불러와 학습용 80%, 검증용 20%로 나눠 반환한다."""
    dataset = load_iris()

    return train_test_split(
        dataset.data,
        dataset.target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        # 세 품종의 비율이 학습·검증 데이터에서 비슷하게 유지되도록 한다.
        stratify=dataset.target,
    )


def train_model():
    """분류 모델을 학습하고 검증 accuracy와 sample 수를 반환한다."""
    x_train, x_test, y_train, y_test = load_and_split_data()

    model = LogisticRegression(max_iter=MAX_ITERATIONS)
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
    """명령줄에서 학습 작업을 실행하고 metrics를 JSON 한 줄로 출력한다."""
    _, metrics = train_model()
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    # 이 파일을 직접 실행했을 때만 학습 작업을 시작한다.
    main()
