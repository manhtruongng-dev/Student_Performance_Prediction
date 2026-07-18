import os
import sqlite3
from datetime import datetime

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ============================================================
# 1. Khởi tạo ứng dụng FastAPI
# ============================================================
app = FastAPI(
    title="Student Performance Prediction API",
    description="Hệ thống AI dự đoán điểm số học sinh (G3) - Bài tập lớn Trí tuệ nhân tạo",
    version="1.0.0",
)

# ============================================================
# 2. Cấu hình CORS (cho phép frontend HTML/JS thuần gọi API)
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 3. Cấu hình cơ sở dữ liệu SQLite
# ============================================================
DB_PATH = os.path.join(os.path.dirname(__file__), "predictions.db")


def init_db():
    """Khởi tạo bảng lưu lịch sử dự đoán nếu chưa tồn tại"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            G1 REAL,
            G2 REAL,
            failures INTEGER,
            age INTEGER,
            traveltime INTEGER,
            goout INTEGER,
            studytime INTEGER,
            Medu INTEGER,
            Fedu INTEGER,
            predicted_score REAL,
            prediction_text TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


init_db()

# ============================================================
# 4. Cấu hình & nạp Model AI
# ============================================================
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "models", "best_model_package.joblib"
)

_model_cache = None


def load_ai_model():
    """Tải model từ file .joblib (cache lại sau lần load đầu tiên)"""
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    if os.path.exists(MODEL_PATH):
        try:
            package = joblib.load(MODEL_PATH)
            _model_cache = package["pipeline"]
            return _model_cache
        except Exception as e:
            print(f"Lỗi khi load model: {e}")
            return None
    return None


# ============================================================
# 5. Schema dữ liệu đầu vào (khớp đúng preprocessing.py của nhóm)
# ============================================================
class StudentInput(BaseModel):
    G1: float = Field(..., ge=0, le=20, description="Điểm kiểm tra kỳ 1 (0-20)")
    G2: float = Field(..., ge=0, le=20, description="Điểm kiểm tra kỳ 2 (0-20)")
    failures: int = Field(..., ge=0, le=4, description="Số lần từng rớt môn (0-4)")
    age: int = Field(..., ge=15, le=22, description="Tuổi học sinh")
    traveltime: int = Field(..., ge=1, le=4, description="Thời gian di chuyển đến trường (1-4)")
    goout: int = Field(..., ge=1, le=5, description="Mức độ đi chơi cùng bạn bè (1-5)")
    studytime: int = Field(..., ge=1, le=4, description="Thời gian tự học mỗi tuần (1-4)")
    Medu: int = Field(..., ge=0, le=4, description="Trình độ học vấn của mẹ (0-4)")
    Fedu: int = Field(..., ge=0, le=4, description="Trình độ học vấn của cha (0-4)")
    absences: int = Field(0, ge=0, le=93, description="Số buổi vắng học (dùng để tính study_per_absence, failure_impact)")


# ============================================================
# 6. Các endpoint API
# ============================================================
@app.get("/")
def health_check():
    """Kiểm tra trạng thái hệ thống"""
    model_exists = os.path.exists(MODEL_PATH)
    return {
        "status": "Online",
        "model_status": "Ready" if model_exists else f"Model file not found at {MODEL_PATH}",
        "database": "Connected",
    }


@app.post("/predict")
async def predict(data: StudentInput):
    """Tiếp nhận dữ liệu, dự đoán điểm G3 và lưu vào lịch sử"""
    ai_model = load_ai_model()

    if ai_model is None:
        raise HTTPException(
            status_code=500,
            detail=f"Chưa tìm thấy file model tại {MODEL_PATH}. Vui lòng kiểm tra lại.",
        )

    try:
        # Bước 1: Feature engineering giống hệt notebooks/preprocessing.py
        study_per_absence = data.studytime / (data.absences + 1)
        failure_impact = data.failures * data.absences

        input_dict = {
            "G1": [data.G1],
            "G2": [data.G2],
            "failures": [data.failures],
            "age": [data.age],
            "traveltime": [data.traveltime],
            "goout": [data.goout],
            "studytime": [data.studytime],
            "Medu": [data.Medu],
            "Fedu": [data.Fedu],
            "study_per_absence": [study_per_absence],
            "failure_impact": [failure_impact],
        }

        df = pd.DataFrame(input_dict)

        # Bước 2: Dự đoán
        prediction_result = ai_model.predict(df)[0]
        final_score = round(float(prediction_result), 2)
        final_score = max(0.0, min(20.0, final_score))

        result_text = "PASS" if final_score >= 10 else "FAIL"

        if final_score >= 16:
            advice = "Kết quả xuất sắc! Hãy tiếp tục duy trì phong độ này."
        elif final_score >= 10:
            advice = "Bạn đã vượt qua! Hãy cố gắng cải thiện điểm số ở các kỳ tới."
        else:
            advice = "Cảnh báo: Bạn có nguy cơ không đạt. Hãy tập trung học tập và giảm bớt thời gian đi chơi."

        # Bước 3: Lưu vào database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO prediction_history
            (G1, G2, failures, age, traveltime, goout, studytime, Medu, Fedu, predicted_score, prediction_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.G1,
                data.G2,
                data.failures,
                data.age,
                data.traveltime,
                data.goout,
                data.studytime,
                data.Medu,
                data.Fedu,
                final_score,
                result_text,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        conn.close()

        return {
            "prediction": result_text,
            "score": final_score,
            "advice": advice,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý model AI: {str(e)}")


@app.get("/history")
def get_history():
    """Lấy danh sách 10 lần dự đoán gần nhất"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prediction_history ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()

        history_list = []
        for r in rows:
            history_list.append(
                {
                    "id": r[0],
                    "G1": r[1],
                    "G2": r[2],
                    "failures": r[3],
                    "age": r[4],
                    "traveltime": r[5],
                    "goout": r[6],
                    "studytime": r[7],
                    "Medu": r[8],
                    "Fedu": r[9],
                    "score": r[10],
                    "result": r[11],
                    "date": r[12],
                }
            )
        return history_list
    except Exception as e:
        return {"error": f"Lỗi truy vấn lịch sử: {str(e)}"}
