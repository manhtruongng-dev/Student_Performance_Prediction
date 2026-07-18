import json
import sqlite3
from datetime import datetime, timezone

from .config import DATABASE_PATH
from .schemas import HistoryItem, PredictionRequest


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                input_payload TEXT NOT NULL,
                predicted_g3 REAL NOT NULL
            )
            """
        )


def save_prediction(request: PredictionRequest, predicted_g3: float) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(request.model_dump())
    with _connection() as connection:
        cursor = connection.execute(
            "INSERT INTO predictions (created_at, input_payload, predicted_g3) VALUES (?, ?, ?)",
            (created_at, payload, predicted_g3),
        )
        return int(cursor.lastrowid)


def get_history(limit: int, offset: int) -> list[HistoryItem]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, input_payload, predicted_g3
            FROM predictions
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    return [
        HistoryItem(
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            inputs=PredictionRequest.model_validate(json.loads(row["input_payload"])),
            predicted_g3=row["predicted_g3"],
        )
        for row in rows
    ]
