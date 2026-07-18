from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    G1: int = Field(ge=3, le=19)
    G2: int = Field(ge=0, le=19)
    failures: int = Field(ge=0, le=3)
    age: int = Field(ge=15, le=22)
    traveltime: int = Field(ge=1, le=4)
    goout: int = Field(ge=1, le=5)
    studytime: int = Field(ge=1, le=4)
    Medu: int = Field(ge=0, le=4)
    Fedu: int = Field(ge=0, le=4)
    absences: int = Field(ge=0, le=75)


class PredictionResponse(BaseModel):
    prediction_id: int
    predicted_g3: float


class ModelInfoResponse(BaseModel):
    model_name: str
    target: str = "G3"
    task_type: str = "regression"
    raw_input_fields: list[str]
    final_model_features: list[str]
    metrics: dict[str, float]
    best_params: dict[str, int]
    date_created: str | None = None
    description: str | None = None


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    inputs: PredictionRequest
    predicted_g3: float
