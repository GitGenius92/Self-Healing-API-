# ============================================================
#  API HEALER — FASTAPI BACKEND
#  Run in Thonny terminal:
#    pip install fastapi uvicorn torch joblib python-multipart pyyaml
#    python main.py
#  Server starts at: http://localhost:8000
# ============================================================

import os, sys, json, re, pickle, time, yaml, traceback
from pathlib import Path
from typing import List, Optional

import torch
import torch.nn as nn
import numpy as np
import joblib

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ── Paths ────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).parent / "models"
# Place your .pth and .save files in a 'models/' folder next to main.py

# ════════════════════════════════════════════════════════════
#  ML MODEL DEFINITIONS (must match kaggle_train.py)
# ════════════════════════════════════════════════════════════

class SimpleTokenizer:
    def __init__(self, max_vocab=5000, max_len=50):
        self.max_vocab = max_vocab
        self.max_len = max_len
        self.word2idx = {"<PAD>": 0, "<UNK>": 1}

    def encode(self, text):
        tokens = [self.word2idx.get(w.lower(), 1) for w in text.split()]
        tokens = tokens[:self.max_len]
        tokens += [0] * (self.max_len - len(tokens))
        return tokens


class VulnClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, num_layers=2, dropout=0.0):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers=num_layers,
                            batch_first=True, bidirectional=True, dropout=dropout)
        self.attention = nn.Linear(hidden_dim * 2, 1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128), nn.ReLU(), nn.Dropout(dropout), nn.Linear(128, num_classes)
        )

    def forward(self, x):
        emb = self.embedding(x)
        out, _ = self.lstm(emb)
        attn_w = torch.softmax(self.attention(out), dim=1)
        ctx = (attn_w * out).sum(dim=1)
        return self.classifier(ctx)


class HealingSuggester(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, num_classes, dropout=0.0):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.gru = nn.GRU(embed_dim, hidden_dim, num_layers=3,
                          batch_first=True, bidirectional=True, dropout=dropout)
        self.attn_q = nn.Linear(hidden_dim * 2, hidden_dim)
        self.attn_k = nn.Linear(hidden_dim * 2, hidden_dim)
        self.attn_v = nn.Linear(hidden_dim * 2, hidden_dim)
        self.out = nn.Sequential(
            nn.Linear(hidden_dim, 256), nn.GELU(), nn.Dropout(dropout), nn.Linear(256, num_classes)
        )

    def forward(self, x):
        emb = self.embedding(x)
        h, _ = self.gru(emb)
        Q, K, V = self.attn_q(h), self.attn_k(h), self.attn_v(h)
        scores = torch.bmm(Q, K.transpose(1, 2)) / (Q.size(-1) ** 0.5)
        ctx = torch.bmm(torch.softmax(scores, -1), V).mean(dim=1)
        return self.out(ctx)


# ════════════════════════════════════════════════════════════
#  HEAL CODE TEMPLATES
# ════════════════════════════════════════════════════════════

HEAL_CODE = {
    "rate_limit": {
        "title": "Add rate limiting middleware",
        "description": "ML detected missing rate limit. Add Redis-backed limiter: 5 req/min per IP.",
        "code": """# FastAPI + slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/login")
@limiter.limit("5/minute")
async def login(request: Request): ...
""",
        "severity_fixed": "High",
    },
    "encrypt": {
        "title": "Hash passwords with bcrypt",
        "description": "Never store or transmit plaintext passwords. Use bcrypt with cost=12.",
        "code": """import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
""",
        "severity_fixed": "Critical",
    },
    "auth_check": {
        "title": "Add ownership verification (IDOR fix)",
        "description": "Always verify the requesting user owns the resource.",
        "code": """async def get_user_resource(id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    resource = db.query(Resource).filter(Resource.id == id).first()
    if not resource:
        raise HTTPException(404, "Not found")
    if resource.owner_id != current_user.id:
        raise HTTPException(403, "Forbidden")
    return resource
""",
        "severity_fixed": "Critical",
    },
    "parameterize": {
        "title": "Use parameterized SQL queries",
        "description": "Never concatenate user input into queries. Use parameterized statements.",
        "code": """# VULNERABLE — NEVER DO THIS:
# query = f"SELECT * FROM users WHERE id = {user_id}"

# HEALED — parameterized:
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))

# With SQLAlchemy ORM (recommended):
user = db.query(User).filter(User.id == user_id).first()
""",
        "severity_fixed": "Critical",
    },
    "add_jwt": {
        "title": "Add JWT Bearer authentication",
        "description": "Protect endpoint with JWT middleware. Validate on every request.",
        "code": """from fastapi.security import HTTPBearer
from jose import jwt, JWTError

security = HTTPBearer()
SECRET = os.environ["JWT_SECRET"]

async def get_current_user(token=Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET, algorithms=["HS256"])
        return payload["sub"]
    except JWTError:
        raise HTTPException(401, "Invalid token")

@router.get("/admin", dependencies=[Depends(get_current_user)])
async def admin_route(): ...
""",
        "severity_fixed": "Critical",
    },
    "csrf_token": {
        "title": "Add CSRF token validation",
        "description": "Generate per-session CSRF token. Validate X-CSRF-Token on mutations.",
        "code": """import secrets

def generate_csrf_token() -> str:
    return secrets.token_hex(32)

async def verify_csrf(request: Request):
    token = request.headers.get("X-CSRF-Token")
    session_token = request.session.get("csrf_token")
    if not token or token != session_token:
        raise HTTPException(403, "CSRF validation failed")
""",
        "severity_fixed": "High",
    },
    "sanitize_input": {
        "title": "Sanitize user inputs to prevent XSS",
        "description": "Escape HTML entities. Strip dangerous tags with bleach.",
        "code": """import bleach

ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong']

def sanitize(text: str) -> str:
    return bleach.clean(text, tags=ALLOWED_TAGS, strip=True)

# In your endpoint:
safe_query = sanitize(request.query_param)
""",
        "severity_fixed": "High",
    },
    "validate_filetype": {
        "title": "Validate uploaded file types",
        "description": "Whitelist extensions and check MIME type to prevent malicious uploads.",
        "code": """import magic

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf'}
ALLOWED_MIMES = {'image/jpeg', 'image/png', 'image/gif', 'application/pdf'}

async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "File type not allowed")
    content = await file.read(2048)
    mime = magic.from_buffer(content, mime=True)
    if mime not in ALLOWED_MIMES:
        raise HTTPException(400, "Invalid file content")
""",
        "severity_fixed": "High",
    },
    "mask_errors": {
        "title": "Mask verbose error messages",
        "description": "Return generic error to client. Log full trace server-side only.",
        "code": """import logging, traceback

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "request_id": str(uuid.uuid4())}
    )
""",
        "severity_fixed": "Medium",
    },
    "enforce_https": {
        "title": "Enforce HTTPS with HSTS header",
        "description": "Add Strict-Transport-Security header. Redirect HTTP to HTTPS.",
        "code": """from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)

@app.middleware("http")
async def add_hsts(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )
    return response
""",
        "severity_fixed": "High",
    },
    "strong_secret": {
        "title": "Generate strong JWT secret",
        "description": "Replace weak secret with cryptographically strong one. Store in env.",
        "code": """import secrets, os

# Run once to generate — then store in .env:
# NEW_SECRET = secrets.token_hex(32)
# print(f"JWT_SECRET={NEW_SECRET}")

# Load in app:
SECRET_KEY = os.environ.get("JWT_SECRET")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET must be set and >= 32 chars")
""",
        "severity_fixed": "Critical",
    },
    "field_filter": {
        "title": "Filter response fields with Pydantic",
        "description": "Use explicit response models to whitelist returned fields only.",
        "code": """from pydantic import BaseModel

class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    # NOTE: password_hash, internal_flags, etc. NOT included

@router.get("/users/me", response_model=UserPublic)
async def get_me(current_user=Depends(get_current_user)):
    return current_user
""",
        "severity_fixed": "Medium",
    },
    "add_pagination": {
        "title": "Add pagination to list endpoints",
        "description": "Cap page size at 100. Add limit/offset to prevent full DB dumps.",
        "code": """from fastapi import Query

@router.get("/orders")
async def list_orders(
    limit: int = Query(default=20, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    db=Depends(get_db)
):
    total = db.query(Order).count()
    items = db.query(Order).offset(offset).limit(limit).all()
    return {"total": total, "items": items, "limit": limit, "offset": offset}
""",
        "severity_fixed": "Medium",
    },
    "verify_signature": {
        "title": "Verify webhook HMAC signature",
        "description": "Compute HMAC-SHA256. Reject requests with invalid or missing signature.",
        "code": """import hmac, hashlib

WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"].encode()

async def verify_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("X-Signature-256", "")
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(401, "Invalid webhook signature")
""",
        "severity_fixed": "High",
    },
    "disable_introspection": {
        "title": "Disable GraphQL introspection in production",
        "description": "Introspection exposes your full schema. Disable it in prod.",
        "code": """# Strawberry GraphQL
import strawberry
from strawberry.extensions import DisableIntrospection

schema = strawberry.Schema(
    query=Query,
    extensions=[DisableIntrospection] if os.getenv("ENV") == "production" else []
)
""",
        "severity_fixed": "Medium",
    },
    "restrict_cors": {
        "title": "Restrict CORS to trusted origins",
        "description": "Replace wildcard with explicit allowed origins list.",
        "code": """from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "https://yourdomain.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
""",
        "severity_fixed": "Medium",
    },
    "expire_token": {
        "title": "Add password reset token expiry",
        "description": "Reset tokens must expire after 15 minutes. Invalidate on single use.",
        "code": """from datetime import datetime, timedelta
import redis

r = redis.Redis()
TOKEN_TTL = 15 * 60  # 15 minutes

def store_reset_token(user_id: int, token: str):
    r.setex(f"reset:{token}", TOKEN_TTL, str(user_id))

def consume_reset_token(token: str) -> Optional[int]:
    uid = r.getdel(f"reset:{token}")  # atomic get + delete
    return int(uid) if uid else None
""",
        "severity_fixed": "High",
    },
    "none": {
        "title": "No fix needed",
        "description": "Endpoint appears safe. No healing action required.",
        "code": "# This endpoint passed all security checks.",
        "severity_fixed": "Safe",
    },
}

SEVERITY_SCORE = {"Critical": 0, "High": 1, "Medium": 2, "Info": 3, "Safe": 4}

# ════════════════════════════════════════════════════════════
#  LOAD MODELS
# ════════════════════════════════════════════════════════════

DEVICE = torch.device("cpu")
clf_model = None
heal_model = None
tokenizer = None
label_enc = None
fix_enc = None
MODELS_LOADED = False


def load_models():
    global clf_model, heal_model, tokenizer, label_enc, fix_enc, MODELS_LOADED
    try:
        tok_path = MODEL_DIR / "tokenizer.save"
        le_path  = MODEL_DIR / "label_encoder.save"
        fe_path  = MODEL_DIR / "fix_encoder.save"
        clf_path = MODEL_DIR / "vulnerability_classifier.pth"
        heal_path= MODEL_DIR / "healing_suggester.pth"

        missing = [p for p in [tok_path, le_path, fe_path, clf_path, heal_path] if not p.exists()]
        if missing:
            print(f"[WARN] Missing model files: {[str(m) for m in missing]}")
            print("[INFO] Running in DEMO mode with rule-based fallback.")
            MODELS_LOADED = False
            return

        with open(tok_path, "rb") as f:
            tokenizer = pickle.load(f)
        label_enc = joblib.load(le_path)
        fix_enc   = joblib.load(fe_path)

        clf_ckpt  = torch.load(clf_path, map_location=DEVICE)
        clf_model = VulnClassifier(
            vocab_size=clf_ckpt["vocab_size"], embed_dim=clf_ckpt["embed_dim"],
            hidden_dim=clf_ckpt["hidden_dim"], num_classes=clf_ckpt["num_classes"]
        )
        clf_model.load_state_dict(clf_ckpt["model_state"])
        clf_model.eval()

        heal_ckpt  = torch.load(heal_path, map_location=DEVICE)
        heal_model = HealingSuggester(
            vocab_size=heal_ckpt["vocab_size"], embed_dim=heal_ckpt["embed_dim"],
            hidden_dim=heal_ckpt["hidden_dim"], num_classes=heal_ckpt["num_classes"]
        )
        heal_model.load_state_dict(heal_ckpt["model_state"])
        heal_model.eval()

        MODELS_LOADED = True
        print("[OK] All ML models loaded successfully.")
    except Exception as e:
        print(f"[ERROR] Model loading failed: {e}")
        MODELS_LOADED = False


# ════════════════════════════════════════════════════════════
#  RULE-BASED FALLBACK (when models not loaded)
# ════════════════════════════════════════════════════════════

RULES = [
    (r"login|auth|signin",         r"rate.limit|slow",      "High",     "Brute Force",   "rate_limit"),
    (r"admin|delete|destroy",      r"auth|jwt|bearer",      "Critical", "Broken Auth",   "add_jwt"),
    (r"\{id\}|\{user",             r"owner|permission",     "Critical", "IDOR",          "auth_check"),
    (r"upload|file|attachment",    r"type|mime|extension",  "High",     "File Upload",   "validate_filetype"),
    (r"password|passwd|secret",    r"hash|bcrypt|encrypt",  "Critical", "Exposure",      "encrypt"),
    (r"search|query|\?q=",         r"sanitize|escape|clean","High",     "XSS",           "sanitize_input"),
    (r"webhook|callback|event",    r"signature|hmac|verify","High",     "Spoofing",      "verify_signature"),
    (r"",                          r"",                      "Info",     "Review",        "none"),
]

def rule_based_analysis(method: str, path: str) -> dict:
    text = f"{method} {path}".lower()
    for path_pat, missing_pat, sev, cat, fix in RULES:
        if re.search(path_pat, text):
            if not re.search(missing_pat, text):
                return {"severity": sev, "category": cat, "fix_type": fix,
                        "confidence": 0.75, "mode": "rule"}
    return {"severity": "Safe", "category": "None", "fix_type": "none",
            "confidence": 0.90, "mode": "rule"}


def ml_analysis(method: str, path: str) -> dict:
    if not MODELS_LOADED:
        return rule_based_analysis(method, path)
    text = f"{method} {path}"
    tokens = torch.tensor([tokenizer.encode(text)], dtype=torch.long)
    with torch.no_grad():
        sev_logits  = clf_model(tokens)
        fix_logits  = heal_model(tokens)
        sev_probs   = torch.softmax(sev_logits, dim=1)[0]
        fix_probs   = torch.softmax(fix_logits, dim=1)[0]
        sev_idx     = sev_probs.argmax().item()
        fix_idx     = fix_probs.argmax().item()
    return {
        "severity":   label_enc.classes_[sev_idx],
        "category":   "ML Detected",
        "fix_type":   fix_enc.classes_[fix_idx],
        "confidence": round(float(sev_probs.max()), 3),
        "mode":       "ml",
    }


# ════════════════════════════════════════════════════════════
#  PARSE API SPEC
# ════════════════════════════════════════════════════════════

def parse_openapi(content: str) -> List[dict]:
    endpoints = []
    try:
        try:
            spec = json.loads(content)
        except json.JSONDecodeError:
            spec = yaml.safe_load(content)
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method in ["get", "post", "put", "delete", "patch", "options"]:
                if method in methods:
                    op = methods[method]
                    endpoints.append({
                        "method": method.upper(), "path": path,
                        "summary": op.get("summary", ""),
                        "tags": op.get("tags", []),
                        "params": [p.get("name", "") for p in op.get("parameters", [])],
                    })
    except Exception as e:
        print(f"[WARN] parse_openapi failed: {e}")
    return endpoints


def parse_postman(content: str) -> List[dict]:
    endpoints = []
    try:
        col = json.loads(content)
        items = col.get("item", [])
        def walk(items):
            for item in items:
                if "request" in item:
                    req = item["request"]
                    url = req.get("url", {})
                    raw = url.get("raw", "") if isinstance(url, dict) else str(url)
                    path = "/" + "/".join(url.get("path", [])) if isinstance(url, dict) else raw
                    endpoints.append({
                        "method": req.get("method", "GET"),
                        "path": path, "summary": item.get("name", ""),
                        "tags": [], "params": [],
                    })
                if "item" in item:
                    walk(item["item"])
        walk(items)
    except Exception as e:
        print(f"[WARN] parse_postman failed: {e}")
    return endpoints


# ════════════════════════════════════════════════════════════
#  FASTAPI APP
# ════════════════════════════════════════════════════════════

app = FastAPI(
    title="API Security Healer",
    description="Upload your API spec — get security vulnerabilities + ML healing suggestions",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class EndpointInput(BaseModel):
    method: str
    path: str
    summary: Optional[str] = ""


class ManualInput(BaseModel):
    endpoints: List[EndpointInput]


@app.on_event("startup")
async def startup():
    load_models()


@app.get("/")
def root():
    return {
        "status": "running",
        "models_loaded": MODELS_LOADED,
        "version": "1.0.0",
        "endpoints": ["/analyze/file", "/analyze/manual", "/health"]
    }


@app.get("/health")
def health():
    return {"status": "ok", "models": MODELS_LOADED, "device": str(DEVICE)}


def analyze_endpoints(endpoints: List[dict]) -> dict:
    results = []
    for ep in endpoints:
        method = ep.get("method", "GET").upper()
        path   = ep.get("path", "/")
        t0 = time.time()
        analysis = ml_analysis(method, path)
        latency  = round((time.time() - t0) * 1000, 1)

        fix_info = HEAL_CODE.get(analysis["fix_type"], HEAL_CODE["none"])
        results.append({
            "method":      method,
            "path":        path,
            "summary":     ep.get("summary", ""),
            "severity":    analysis["severity"],
            "category":    analysis["category"],
            "confidence":  analysis["confidence"],
            "mode":        analysis["mode"],
            "fix_type":    analysis["fix_type"],
            "heal_title":  fix_info["title"],
            "heal_desc":   fix_info["description"],
            "heal_code":   fix_info["code"],
            "latency_ms":  latency,
        })

    results.sort(key=lambda x: SEVERITY_SCORE.get(x["severity"], 5))

    total   = len(results)
    vulns   = [r for r in results if r["severity"] != "Safe"]
    criticals = sum(1 for r in results if r["severity"] == "Critical")
    highs     = sum(1 for r in results if r["severity"] == "High")
    mediums   = sum(1 for r in results if r["severity"] == "Medium")
    score = max(0, 100 - criticals * 22 - highs * 12 - mediums * 5)

    return {
        "total_endpoints": total,
        "vulnerabilities": len(vulns),
        "critical": criticals,
        "high": highs,
        "medium": mediums,
        "security_score": score,
        "models_used": "ML (PyTorch)" if MODELS_LOADED else "Rule-based fallback",
        "results": results,
    }


@app.post("/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="ignore")
    fname = file.filename.lower()
    if "postman" in fname or (fname.endswith(".json") and '"item"' in content):
        endpoints = parse_postman(content)
    else:
        endpoints = parse_openapi(content)
    if not endpoints:
        raise HTTPException(422, "Could not parse any endpoints from the file.")
    return analyze_endpoints(endpoints)


@app.post("/analyze/manual")
async def analyze_manual(body: ManualInput):
    if not body.endpoints:
        raise HTTPException(422, "No endpoints provided.")
    eps = [{"method": e.method, "path": e.path, "summary": e.summary} for e in body.endpoints]
    return analyze_endpoints(eps)


@app.post("/analyze/text")
async def analyze_text(body: dict):
    content = body.get("content", "")
    endpoints = parse_openapi(content) or parse_postman(content)
    if not endpoints:
        lines = content.strip().split("\n")
        endpoints = []
        for line in lines:
            m = re.match(r"\s*(GET|POST|PUT|DELETE|PATCH)\s+(/\S+)", line, re.I)
            if m:
                endpoints.append({"method": m.group(1).upper(), "path": m.group(2), "summary": ""})
    if not endpoints:
        raise HTTPException(422, "No parseable endpoints found in text.")
    return analyze_endpoints(endpoints)


if __name__ == "__main__":
    print("=" * 50)
    print("  API SECURITY HEALER — Backend")
    print("  http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
