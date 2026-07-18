# Backend API

Run from the repository root:

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

API documentation is available at `http://127.0.0.1:8000/docs`.

The prediction request and batch CSV both require these columns, in this order:

```text
G1,G2,failures,age,traveltime,goout,studytime,Medu,Fedu,absences
```
