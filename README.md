
# API Security Healer — Complete Project

## Project Structure
```
api_healer/
├── ml_training/
│   ├── kaggle_train.py       ← Run on Kaggle GPU
│   └── requirements.txt
├── backend/
│   ├── main.py               ← FastAPI server (run in Thonny)
│   ├── models/               ← Paste .pth and .save files here
│   └── requirements.txt
└── frontend/
    ├── app.py                ← Streamlit UI (run in Thonny)
    └── requirements.txt
```

---

## STEP 1 — Train ML Models on Kaggle

1. Go to https://kaggle.com → New Notebook
2. Upload `ml_training/kaggle_train.py` — paste contents into a cell
3. Enable GPU: Settings → Accelerator → GPU T4
4. Run all cells
5. Download these files from `/kaggle/working/`:
   - `vulnerability_classifier.pth`
   - `healing_suggester.pth`
   - `label_encoder.save`
   - `fix_encoder.save`
   - `tfidf_vectorizer.save`
   - `tokenizer.save`

---

## STEP 2 — Setup Backend (Thonny)

1. Open Thonny → Tools → Manage Packages
   Install: `fastapi uvicorn torch joblib python-multipart pyyaml`

2. Create folder: `backend/models/`
3. Paste all 6 model files into `backend/models/`

4. Open `backend/main.py` in Thonny → Run
   Server starts at: http://localhost:8000
   Swagger docs at: http://localhost:8000/docs

---

## STEP 3 — Run Frontend (Thonny)

1. Open new Thonny terminal
   Install: `streamlit requests plotly pyyaml`

2. In terminal:
   ```
   cd path/to/frontend
   streamlit run app.py
   ```
3. Opens at: http://localhost:8501

---

## What It Does

| Input | Output |
|---|---|
| OpenAPI .json / .yaml | Security score + vulnerability list |
| Postman collection .json | OWASP category + severity per endpoint |
| Paste raw JSON/YAML | ML confidence score |
| Manual endpoint list | Self-healing Python code per issue |

## ML Models

| Model | Architecture | Task |
|---|---|---|
| VulnClassifier | BiLSTM + Attention | Severity: Critical/High/Medium/Safe |
| HealingSuggester | BiGRU + Self-Attention | Fix type: rate_limit / add_jwt / parameterize / etc |

---

## Notes
- Backend runs even WITHOUT model files (falls back to OWASP rule engine)
- Models load automatically from `backend/models/` on startup
- All healing code is production-ready Python (FastAPI)
