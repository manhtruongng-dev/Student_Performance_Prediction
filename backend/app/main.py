import csv
from contextlib import asynccontextmanager
from io import StringIO

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from .config import FINAL_MODEL_FEATURES, MODEL_METRICS, RAW_INPUT_FIELDS
from .history import get_history, initialize_database, save_prediction
from .model_service import load_model_package, predict
from .schemas import HistoryItem, ModelInfoResponse, PredictionRequest, PredictionResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    load_model_package()
    yield


app = FastAPI(
    title="Student Performance Prediction API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    load_model_package()
    return {"status": "ok", "model": "loaded"}


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    metadata = load_model_package().get("metadata", {})
    return ModelInfoResponse(
        model_name=metadata.get("model_name", "RandomForest_Tuned"),
        raw_input_fields=RAW_INPUT_FIELDS,
        final_model_features=FINAL_MODEL_FEATURES,
        metrics=MODEL_METRICS,
        best_params=metadata.get("best_params", {"n_estimators": 100, "max_depth": 5}),
        date_created=metadata.get("date_created"),
        description=metadata.get("description"),
    )


@app.post("/predict", response_model=PredictionResponse)
def single_prediction(request: PredictionRequest) -> PredictionResponse:
    predicted_g3 = predict(request)
    prediction_id = save_prediction(request, predicted_g3)
    return PredictionResponse(prediction_id=prediction_id, predicted_g3=predicted_g3)


@app.get("/history", response_model=list[HistoryItem])
def prediction_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[HistoryItem]:
    return get_history(limit=limit, offset=offset)


@app.post("/predict/batch")
async def batch_prediction(file: UploadFile = File(...)) -> StreamingResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A CSV file is required.")

    try:
        dataframe = pd.read_csv(file.file)
    except Exception as error:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid CSV.") from error

    missing_fields = [field for field in RAW_INPUT_FIELDS if field not in dataframe.columns]
    unexpected_fields = [field for field in dataframe.columns if field not in RAW_INPUT_FIELDS]
    if missing_fields or unexpected_fields:
        raise HTTPException(
            status_code=400,
            detail={"missing_fields": missing_fields, "unexpected_fields": unexpected_fields},
        )

    requests: list[PredictionRequest] = []
    for index, row in dataframe.iterrows():
        try:
            requests.append(PredictionRequest.model_validate(row.to_dict()))
        except ValidationError as error:
            raise HTTPException(status_code=422, detail={"row": int(index) + 2, "errors": error.errors()}) from error

    predictions = [predict(request) for request in requests]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=[*RAW_INPUT_FIELDS, "predicted_g3"])
    writer.writeheader()
    for request, predicted_g3 in zip(requests, predictions):
        writer.writerow({**request.model_dump(), "predicted_g3": predicted_g3})

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=predictions.csv"},
    )
