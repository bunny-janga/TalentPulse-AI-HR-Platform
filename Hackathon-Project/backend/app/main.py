from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
from app.core.config import settings
from app.routers import (
    auth,
    departments,
    employees,
    leave,
    reviews,
    policies,
    surveys,
    onboarding,
    attrition,
    ai_performance,
    chat,
    admin,
    notifications,
    db_viewer
)
from app.db.session import engine, Base

# Ensure all database tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## TalentPulse AI — Employee Attrition Prediction & GenAI HR Helpdesk
    Enterprise IT Workforce Intelligence and HR Automation Platform for Visakhapatnam IT Center.
    
    ### Key Features:
    * **Role-Based Access Control**: Server-side enforced authorization for Admin, HR, Manager, and Employee.
    * **Workforce Operations**: Employee directory, department hierarchy, leave management, and performance reviews.
    * **AI 1 - Attrition Prediction**: Scikit-Learn machine learning pipeline identifying attrition risk factors and bands (Low/Medium/High).
    * **AI 2 - Performance Trend Flagging**: Automated detection of employees experiencing consecutive review declines.
    * **GenAI 1 - HR Policy Helpdesk (RAG)**: Instant semantic Q&A over company policy documents with grounded citations.
    * **GenAI 2 - AI Review Drafting**: Generative expansion of manager bullet notes into structured performance evaluations.
    """,
    openapi_tags=[
        {"name": "Authentication", "description": "Login, registration, JWT tokens, and user profile endpoints."},
        {"name": "Employees & Org", "description": "Employee directory, manager hierarchy, and department management."},
        {"name": "Leave Management", "description": "Leave application, approval, and balance workflows."},
        {"name": "Performance Reviews", "description": "Review cycles, evaluation submission, and AI-assisted drafting."},
        {"name": "Policy Helpdesk", "description": "Policy document management, PDF ingestion, and RAG Q&A."},
        {"name": "Engagement Surveys", "description": "Pulse surveys, response tracking, and sentiment feedback."},
        {"name": "Onboarding", "description": "New-hire checklist management and completion tracking."},
        {"name": "Attrition Intelligence", "description": "AI predictive risk scoring, factor explanations, and batch scoring."},
        {"name": "Admin Metrics", "description": "Aggregated workforce health metrics and attrition analytics."}
    ]
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=False,  # bearer tokens only, no cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.on_event("startup")
def harden_on_startup():
    """Retire plaintext passwords and make sure the documented demo logins work (demo mode only)."""
    from sqlalchemy import text
    from app.db.session import SessionLocal
    from app.core.security import get_password_hash, verify_password
    from app.models.user import User
    db = SessionLocal()
    try:
        try:
            db.execute(text("UPDATE users SET initial_password = NULL WHERE initial_password IS NOT NULL"))
            db.commit()
        except Exception:
            db.rollback()
        if settings.DEMO_MODE:
            demo = {
                "superadmin@talentpulse.local": "super123!", "admin@talentpulse.local": "Admin123!",
                "hr@talentpulse.local": "Hr123!", "manager@talentpulse.local": "Manager123!",
                "employee@talentpulse.local": "Employee123!",
            }
            for email, pw in demo.items():
                u = db.query(User).filter(User.email == email).first()
                if u and not verify_password(pw, u.hashed_password):
                    u.hashed_password = get_password_hash(pw)
            db.commit()
    finally:
        db.close()

# Register Phase 1 & Phase 2 Routers
app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(leave.router)
app.include_router(reviews.router)
app.include_router(policies.router)
app.include_router(surveys.router)
app.include_router(onboarding.router)
app.include_router(attrition.router)
app.include_router(ai_performance.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(db_viewer.router)

# Mount Static Assets and Web UI
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/ui", tags=["System"], response_class=HTMLResponse)
@app.get("/app", tags=["System"], response_class=HTMLResponse)
def serve_ui():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>TalentPulse UI</h1><p>Static index.html not found.</p>"

@app.get("/", tags=["System"])
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return serve_ui()
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "web_ui": "/ui"
    }

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}
