"""학습 실행을 식별하고 artifact 저장 경로를 관리한다."""

import pickle
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


ARTIFACT_ROOT = Path("artifacts")


def generate_run_id() -> str:
    """UTC 생성 시각과 임의 suffix를 조합해 고유한 run ID를 반환한다."""
    created_at = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    random_suffix = uuid4().hex[:8]

    # 시각은 실행 시점을 보여주고 UUID suffix는 같은 시각의 충돌 가능성을 낮춘다.
    return f"{created_at}-{random_suffix}"


def save_model(model: object, run_id: str, artifact_root: Path = ARTIFACT_ROOT) -> Path:
    """학습된 model을 실행별 디렉터리에 저장하고 artifact 경로를 반환한다."""
    if not run_id or Path(run_id).name != run_id:
        raise ValueError("run_id는 경로 구분자가 없는 단일 이름이어야 합니다.")

    run_directory = artifact_root / run_id
    # 같은 run ID의 결과를 실수로 덮어쓰지 않도록 기존 디렉터리는 허용하지 않는다.
    run_directory.mkdir(parents=True, exist_ok=False)

    artifact_path = run_directory / "model.pkl"
    with artifact_path.open("wb") as artifact_file:
        # pickle은 Python 객체를 그대로 저장하므로 이후에는 신뢰하는 파일만 불러와야 한다.
        pickle.dump(model, artifact_file)

    return artifact_path
