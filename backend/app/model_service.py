import sys
from functools import lru_cache
from typing import Any

import joblib
import pandas as pd

from .config import FINAL_MODEL_FEATURES, MODEL_PATH, NOTEBOOKS_DIR, RAW_INPUT_FIELDS
from .schemas import PredictionRequest

if str(NOTEBOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(NOTEBOOKS_DIR))

from preprocessing import add_engineer, clean  # noqa: E402


@lru_cache(maxsize=1)
def load_model_package() -> dict[str, Any]:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Model artifact was not found: {MODEL_PATH}")

    package = joblib.load(MODEL_PATH)
    if not isinstance(package, dict) or "pipeline" not in package:
        raise ValueError("Model artifact must contain a 'pipeline' entry.")

    artifact_features = getattr(package["pipeline"], "feature_names_in_", None)
    if artifact_features is not None and list(artifact_features) != FINAL_MODEL_FEATURES:
        raise ValueError(
            "Model artifact feature order does not match the backend feature contract."
        )
    return package


def build_model_frame(payload: PredictionRequest | dict[str, int]) -> pd.DataFrame:
    raw_values = payload.model_dump() if isinstance(payload, PredictionRequest) else payload
    raw_frame = pd.DataFrame([{field: raw_values[field] for field in RAW_INPUT_FIELDS}])
    engineered_frame = add_engineer(clean(raw_frame))
    return engineered_frame[FINAL_MODEL_FEATURES]


def predict(payload: PredictionRequest | dict[str, int]) -> float:
    package = load_model_package()
    result = package["pipeline"].predict(build_model_frame(payload))
    return float(result[0])
