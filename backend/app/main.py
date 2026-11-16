"""
FastAPI backend for TalentPulse AI: authentication, role-based access control,
attrition prediction, and HR policy retrieval.
Licensed under the MIT License.
"""

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from ml_engine.attrition_pipeline import DATASET_PATH, predict_employee_risk, train_and_save_model

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "talentpulse.db")
FRONTEND_INDEX = os.path.abspath(os.path.join(BASE_DIR, "../../frontend/index.html"))
JWT_SECRET = os.getenv("JWT_SECRET", "talentpulse-gg13-local-signing-key")

app = FastAPI(
    title="TalentPulse AI API",
    description="Role-based HR operations, attrition risk scoring, and policy Q&A service.",
    version="1.0.0",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def encode_token(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    data = {**payload, "exp": (datetime.utcnow() + timedelta(hours=12)).isoformat()}
    body = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    signature = hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")
    parts = authorization.split(" ")[1].split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Malformed access token.")
    padded = parts[1] + "=" * (-len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(padded).decode())


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def seed_database():
    if not os.path.exists(DATASET_PATH):
        train_and_save_model()

    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_code TEXT UNIQUE,
        full_name TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        department TEXT,
        job_role TEXT,
        tenure_months INTEGER DEFAULT 12,
        monthly_hours REAL DEFAULT 176,
        last_hike_months INTEGER DEFAULT 8,
        engagement_score REAL DEFAULT 4.0,
        perf_rating REAL DEFAULT 4.2,
        commute_km REAL DEFAULT 10.0,
        wfh_days INTEGER DEFAULT 2,
        promotions_3yr INTEGER DEFAULT 0,
        risk_probability REAL DEFAULT 18.0,
        risk_tier TEXT DEFAULT 'STABLE'
    );

    CREATE TABLE IF NOT EXISTS policies (
        policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        content TEXT
    );
    """)

    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        demo_users = [
            ("TPZ-EMP1", "Ananya Rao", "employee@talentpulse.ai", hash_password("Emp@123"), "Employee", "Cloud Engineering", "Senior Engineer", 24, 174, 9, 4.3, 4.6, 11.0, 2, 1, 16.4, "STABLE"),
            ("TPZ-MGR1", "Vikramaditya Varma", "manager@talentpulse.ai", hash_password("Mgr@123"), "Manager", "Cloud Engineering", "Engineering Manager", 46, 182, 7, 4.4, 4.7, 9.0, 2, 1, 12.1, "STABLE"),
            ("TPZ-HR01", "Meera Nair", "hr@talentpulse.ai", hash_password("Hr@123"), "HR Executive", "HR & Operations", "Lead HRBP", 38, 175, 6, 4.5, 4.8, 8.0, 2, 1, 10.5, "STABLE"),
            ("TPZ-ADM1", "Kranthi Kumar", "admin@talentpulse.ai", hash_password("Admin@123"), "Admin", "IT Governance", "System Admin", 52, 172, 5, 4.7, 4.9, 6.0, 3, 2, 8.2, "STABLE"),
            ("TPZ-1001", "Rohan Kulkarni", "rohan@talentpulse.ai", hash_password("Emp@123"), "Employee", "Cloud Engineering", "Senior Engineer", 22, 212, 21, 2.5, 4.1, 24.0, 1, 0, 84.2, "CRITICAL"),
            ("TPZ-1002", "Divya Reddy", "divya@talentpulse.ai", hash_password("Emp@123"), "Employee", "QA Automation", "Software Engineer", 16, 198, 17, 2.8, 4.3, 21.0, 0, 0, 76.5, "CRITICAL"),
        ]
        cur.executemany("""
            INSERT INTO users (
                emp_code, full_name, email, password_hash, role, department, job_role,
                tenure_months, monthly_hours, last_hike_months, engagement_score,
                perf_rating, commute_km, wfh_days, promotions_3yr, risk_probability, risk_tier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, demo_users)

    if cur.execute("SELECT COUNT(*) FROM policies").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO policies (title, category, content) VALUES (?, ?, ?)",
            [
                ("Leave & Holiday Policy 2026", "Leave", "12 Casual Leaves, 10 Sick Leaves, and 15 Earned Leaves/year. Earned leaves carry forward up to 30 days."),
                ("Visakhapatnam Hybrid Work Policy", "Workplace", "3 days in-office (Tue–Thu) and 2 days WFH. Staff commuting >20 km qualify for 4-day WFH."),
                ("Group Medical & Wellness Cover", "Benefits", "₹5,00,000 cashless family floater + ₹1,00,000 OPD & mental wellness wallet."),
                ("Bi-Annual Appraisal Guidelines", "Performance", "April & October cycles (70% OKRs, 30% 360-feedback). 4.5+ ratings unlock 14–18% hikes."),
            ],
        )

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    seed_database()


@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_INDEX)


class LoginRequest(BaseModel):
    email: str
    password: str
    role: str


class ResetPasswordRequest(BaseModel):
    email: str
    role: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class OnboardRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str
    department: str
    job_role: str


class PredictRequest(BaseModel):
    tenure_months: int = 22
    monthly_hours: float = 205
    last_hike_months: int = 18
    engagement_score: float = 2.8
    perf_rating: float = 4.2
    commute_km: float = 18.0
    wfh_days: int = 1
    promotions_3yr: int = 0


class PolicyQueryRequest(BaseModel):
    question: str


@app.post("/api/auth/login")
def login(body: LoginRequest):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE LOWER(email)=LOWER(?) AND role=?",
        (body.email, body.role),
    ).fetchone()
    conn.close()

    if not user or user["password_hash"] != hash_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid email, password, or role.")

    token = encode_token({
        "email": user["email"],
        "role": user["role"],
        "name": user["full_name"],
        "emp_code": user["emp_code"],
    })
    return {
        "access_token": token,
        "role": user["role"],
        "name": user["full_name"],
        "emp_code": user["emp_code"],
        "department": user["department"],
    }


@app.post("/api/auth/forgot-password")
def forgot_password(body: ResetPasswordRequest):
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE LOWER(email)=LOWER(?) AND role=?",
        (body.email, body.role),
    ).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="No account matches that email and role.")

    conn.execute(
        "UPDATE users SET password_hash=? WHERE user_id=?",
        (hash_password(body.new_password), user["user_id"]),
    )
    conn.commit()
    conn.close()
    return {"status": "reset_complete", "email": body.email}


@app.post("/api/auth/change-password")
def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email=?", (current_user["email"],)).fetchone()
    if not row or row["password_hash"] != hash_password(body.old_password):
        conn.close()
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    conn.execute(
        "UPDATE users SET password_hash=? WHERE user_id=?",
        (hash_password(body.new_password), row["user_id"]),
    )
    conn.commit()
    conn.close()
    return {"status": "password_updated"}


@app.post("/api/users/onboard")
def onboard_employee(body: OnboardRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("Manager", "HR Executive", "Admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to onboard new users.")

    conn = get_connection()
    emp_code = f"TPZ-{1010 + conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]}"
    try:
        conn.execute(
            """
            INSERT INTO users (emp_code, full_name, email, password_hash, role, department, job_role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (emp_code, body.full_name, body.email, hash_password(body.password), body.role, body.department, body.job_role),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    conn.close()
    return {"status": "onboarded", "emp_code": emp_code, "full_name": body.full_name, "role": body.role}


@app.get("/api/employees")
def get_employees(current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    rows = [
        dict(r)
        for r in conn.execute(
            """
            SELECT emp_code, full_name, email, role, department, job_role,
                   tenure_months, monthly_hours, last_hike_months,
                   engagement_score, perf_rating, wfh_days, risk_probability, risk_tier
            FROM users
            """
        ).fetchall()
    ]
    conn.close()

    if current_user["role"] == "Employee":
        rows = [r for r in rows if r["email"] == current_user["email"]]
        for r in rows:
            r.pop("risk_probability", None)
            r.pop("risk_tier", None)

    return rows


@app.post("/api/ml/predict")
def predict_attrition(body: PredictRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "Employee":
        raise HTTPException(status_code=403, detail="Attrition predictions are restricted to leadership roles.")
    return predict_employee_risk(body.model_dump())


@app.post("/api/genai/rag-policy")
def answer_policy_question(body: PolicyQueryRequest):
    conn = get_connection()
    policies = [dict(r) for r in conn.execute("SELECT title, content FROM policies").fetchall()]
    conn.close()

    documents = [f"{p['title']}: {p['content']}" for p in policies]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents + [body.question])
    scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    best_match = int(scores.argmax())

    return {
        "answer": policies[best_match]["content"],
        "source_policy": policies[best_match]["title"],
        "confidence": round(float(scores[best_match]) * 100, 1),
    }
