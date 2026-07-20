# Student Performance Prediction
---

## Giới thiệu

Hệ thống dự đoán điểm môn Toán cuối kỳ (**G3**, thang điểm 0–20) của học sinh trung học, dựa trên dữ liệu học tập, gia đình và hành vi sinh hoạt — bộ dữ liệu **Student Performance Dataset** (UCI / Cortez & Silva, 2008).

Mục tiêu: xây dựng một công cụ **cảnh báo sớm**, giúp giáo viên và nhà trường nhận diện học sinh có nguy cơ sa sút học lực **trước khi** kỳ thi cuối kỳ diễn ra, thay vì chỉ biết sau khi có kết quả.

Đây không chỉ là một notebook thử nghiệm — dự án bao gồm đầy đủ: **phân tích dữ liệu → huấn luyện & tinh chỉnh mô hình có theo dõi thí nghiệm → REST API → giao diện web → cơ sở dữ liệu**.

## Thành viên nhóm 16

| Thành viên | MSSV |
|---|---|
| Nguyễn Mạnh Trường | 2351050193 |
| Trần Nguyên Khang | 2351010096 |
| Tô Nguyễn Sơn Nam | 2351050109 |
| Mai Thanh Hải | 2351010054 |

Giảng viên hướng dẫn: **Võ Việt Khoa** — TH1007-CS2401, HK3 năm học 2025–2026.

---

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Xử lý dữ liệu & Mô hình | Python, pandas, scikit-learn |
| Theo dõi thí nghiệm | Weights & Biases (W&B Sweeps) |
| Backend API | FastAPI, Pydantic, uvicorn |
| Frontend | React 18, Vite, react-router-dom, lucide-react |
| Cơ sở dữ liệu | SQLite |
| Trực quan hóa | matplotlib, seaborn |

---

## Cài đặt và chạy

### 1. Huấn luyện lại mô hình (tuỳ chọn — model đã có sẵn)

```bash
pip install -r notebooks/requirement.txt
# Chạy tuần tự: 01_eda → 02_feature_engineering → 03_modeling_and_wandb → 04_evaluation
```

### 2. Chạy Backend API

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```
→ Swagger UI tại `http://127.0.0.1:8000/docs`

### 3. Chạy Frontend

```bash
cd frontend
npm install
npm run dev
```
→ Giao diện tại `http://127.0.0.1:5173`

---
## Kết quả chính

| Độ đo | Giá trị | Ý nghĩa |
|---|---|---|
| **R²** | **0.8611** | Mô hình giải thích được 86,1% sự biến thiên của điểm số |
| **RMSE** | 1.6876 | điểm (thang 0–20) |
| **MAE** | **1.0848** | trung bình mỗi dự đoán lệch ~1,08 điểm |
| **MAPE** | 9.54% | (đã hiệu chỉnh lỗi chia-cho-0 khi G3 = 0) |

Mô hình tốt nhất: **Random Forest Regressor** (`max_depth=5`, `n_estimators=100`), chọn ra từ 9 lần chạy Grid Search qua **W&B Sweeps**, so sánh với Linear Regression và Gradient Boosting.

> 📈 Xem toàn bộ log thí nghiệm công khai tại: [W&B Project](https://wandb.ai/maiithanhai-open-university-ho-chi-minh-city/student-performance/overview)

---


## Kiến trúc hệ thống

```
Người dùng → Frontend (React + Vite, :5173) → REST API (FastAPI, :8000) → Model (.joblib) + SQLite
```

- **Model artifact** (`best_model_package.joblib`) được load một lần khi khởi động API, tái sử dụng cho mọi request.
- Mỗi lượt gọi `/predict` được **tự động lưu vào SQLite** để xem lại ở màn hình Lịch sử.
- Frontend và Backend tách biệt hoàn toàn, giao tiếp qua REST API (CORS đã bật sẵn).

## Quy trình Machine Learning

```
Dữ liệu thô (395 học sinh, 32 đặc trưng)
        │
        ▼  EDA — phát hiện: ngoại lai ở "absences", mất cân bằng ở 17 cột phân loại,
        │        G2/G1 tương quan mạnh nhất với G3, ~9.6% học sinh có G3 = 0 bất thường
        ▼  Feature Engineering — giữ 9 đặc trưng số cốt lõi + tạo 2 đặc trưng mới
        │        (study_per_absence, failure_impact) → cải thiện R² tới +12 điểm %
        ▼  Huấn luyện — so sánh Linear Regression / Random Forest / Gradient Boosting
        ▼  Tinh chỉnh siêu tham số — W&B Sweeps, Grid Search 3×3 = 9 lần chạy
        ▼  Đánh giá — MAE/RMSE/R²/MAPE, phân tích lỗi, Feature Importance, ROC/AUC
        ▼
   best_model_package.joblib  ──▶  FastAPI  ──▶  React UI
```

**11 đặc trưng đầu vào của mô hình cuối cùng:**
`G1, G2, failures, age, traveltime, goout, studytime, Medu, Fedu, study_per_absence, failure_impact`

---

## Cài đặt và chạy

### 1. Huấn luyện lại mô hình (tuỳ chọn — model đã có sẵn)

```bash
pip install -r notebooks/requirement.txt
# Chạy tuần tự: 01_eda → 02_feature_engineering → 03_modeling_and_wandb → 04_evaluation
```

### 2. Chạy Backend API

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```
→ Swagger UI tại `http://127.0.0.1:8000/docs`

### 3. Chạy Frontend

```bash
cd frontend
npm install
npm run dev
```
→ Giao diện tại `http://127.0.0.1:5173`

---

## REST API

| Method | Endpoint | Chức năng |
|---|---|---|
| `POST` | `/predict` | Dự đoán điểm G3 cho 1 học sinh |
| `POST` | `/predict/batch` | Dự đoán hàng loạt từ file CSV |
| `GET` | `/health` | Kiểm tra dịch vụ còn sống |
| `GET` | `/model-info` | Thông tin mô hình & độ đo |
| `GET` | `/history` | Lịch sử các lần dự đoán |

Input cho `/predict` và `/predict/batch` cần đúng 10 cột theo thứ tự:
```
G1, G2, failures, age, traveltime, goout, studytime, Medu, Fedu, absences
```

---

## Tài liệu tham khảo

- Cortez, P., & Silva, A. (2008). *Using Data Mining to Predict Secondary School Student Performance*.
- Cortez, P. (2014). [Student Performance Data Set](https://archive.ics.uci.edu/dataset/320/student+performance). UCI ML Repository.
- Pedregosa, F. và cộng sự (2011). *Scikit-learn: Machine Learning in Python*. JMLR 12.

---


