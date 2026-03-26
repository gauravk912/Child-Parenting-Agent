import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib

from app.core.config import settings


def _model_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    return project_root / settings.local_prediction_model_file


def _feature_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    return project_root / settings.local_prediction_feature_file


def prediction_model_available() -> bool:
    return _model_path().exists() and _feature_path().exists()


def predict_with_saved_model(feature_dict: Dict[str, float]) -> Tuple[Optional[float], str]:
    if not prediction_model_available():
        return None, "rule_fallback"

    model = joblib.load(_model_path())
    feature_names = json.loads(_feature_path().read_text(encoding="utf-8"))

    row = [[float(feature_dict.get(name, 0.0)) for name in feature_names]]
    probability = float(model.predict_proba(row)[0][1])

    return probability, "ml_model"