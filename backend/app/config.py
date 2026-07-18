from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
MODEL_PATH = PROJECT_ROOT / "models" / "best_model_package.joblib"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
DATABASE_PATH = BACKEND_DIR / "prediction_history.db"

FINAL_MODEL_FEATURES = [
    "G1",
    "G2",
    "failures",
    "age",
    "traveltime",
    "goout",
    "studytime",
    "Medu",
    "Fedu",
    "study_per_absence",
    "failure_impact",
]

RAW_INPUT_FIELDS = [
    "G1",
    "G2",
    "failures",
    "age",
    "traveltime",
    "goout",
    "studytime",
    "Medu",
    "Fedu",
    "absences",
]

MODEL_METRICS = {"r2": 0.8611, "mae": 1.0848, "rmse": 1.6876}
