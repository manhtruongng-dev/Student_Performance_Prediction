# Frontend Phase 2

React + Vite frontend kết nối FastAPI thật tại `http://127.0.0.1:8000`.

## Chạy
```powershell
cd frontend
npm install
npm run dev
```

Mở: http://localhost:5173

Backend cần chạy song song:
```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

## 5 màn hình
- Dashboard
- Dự đoán G3 (10 raw inputs)
- Thông tin model
- Lịch sử SQLite
- Dự đoán hàng loạt CSV + tải kết quả

Không dùng mock prediction. Frontend không sửa notebook, data hay model artifact.
