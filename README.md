<div align="center">

# ⚡ TalentPulse Enterprise Unified
### Intelligent People Operations, Predictive Retention & AI Workforce Co-pilot

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18%20%2B%20Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Random%20Forest-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![SQLAlchemy](https://img.shields.io/badge/Database-SQLAlchemy%20%26%20Alembic-CA4245?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker Ready](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](#-docker-quickstart)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<p align="center">
  <b>A unified, production-ready workforce intelligence platform that connects day-to-day HR operations with machine learning retention diagnostics and grounded GenAI co-pilots.</b>
</p>

[Overview](#-overview) •
[Core Capabilities](#-core-capabilities) •
[System Design](#-system-design) •
[Project Tree](#-project-tree) •
[Getting Started](#-getting-started) •
[Docker Quickstart](#-docker-quickstart) •
[Demo Accounts](#-test-accounts--rbac) •
[AI & ML Workflows](#-ai--machine-learning-workflows) •
[API Overview](#-api-overview) •
[Test Verification](#-test-verification)

---

</div>

## 📌 Overview

Most HR tools only sound the alarm when it's already too late—during the exit interview.

**TalentPulse Enterprise Unified** changes that dynamic. It links continuous employee telemetry (workload hours, review cycles, satisfaction sentiment, promotion cadence) directly to a trained **Scikit-learn Random Forest model** and an enterprise **RAG (Retrieval-Augmented Generation) co-pilot**.

Instead of digging through scattered spreadsheets, PeopleOps teams can spot flight risk early, generate calibrated performance reviews in seconds, query verified internal policies, and structure targeted retention plans from one dashboard.

---

## ✨ Core Capabilities

* **Flight Risk Forecasting**: Uses a pre-trained Random Forest pipeline (`attrition_model.joblib`) to estimate individual flight risk percentages, isolate primary workplace stressors, and suggest concrete retention steps.
* **Internal Policy Assistant (RAG)**: An AI chat assistant that scans internal handbooks and company policies to give direct, verified answers without corporate jargon.
* **Performance Review Co-pilot**: Summarizes project outcomes, historical feedback, and performance tags into well-balanced review drafts that managers can polish and submit.
* **Early Warning Burnout Flags**: Automatic detection triggers when overtime hours spike, performance scores drop sharply, or sentiment trends downward.
* **Incentive Planning Tool**: Calculates bonus and salary adjustments by cross-referencing retention risk with departmental compensation benchmarks.
* **Dual-Interface Flexibility**:
  * **React 18 + Vite Suite**: Full single-page dashboard featuring responsive data tables, metrics cards, and smooth CSS-token animations.
  * **Unified Portal View**: Standalone employee portal (`portal_dashboard.html` / `portal.html`) built for simple check-ins and quick policy lookups.
* **Multi-Role Security**: Token-based authentication (JWT) with strict backend permission checks across **Admins**, **HR Leaders**, and **Employees**.
* **Zero-Setup Database Migrations**: SQLAlchemy schema management powered by pre-configured Alembic migrations and built-in database seed data.

---

## 🏛️ System Design

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                              Frontends                                 │
 │   React 18 + Vite Application          Unified Lightweight Portal      │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTPS / JWT Auth
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      FastAPI Gateway (Async ASGI)                      │
 └──────┬────────────────────────────┬─────────────────────────────┬──────┘
        │                            │                             │
 ┌──────▼─────────────┐   ┌──────────▼───────────────┐   ┌─────────▼──────────────┐
 │ Identity & Auth    │   │ ML Inference Engine      │   │ GenAI & RAG Service    │
 │ - JWT tokens       │   │ - Random Forest Pipeline │   │ - Policy RAG search    │
 │ - RBAC guards      │   │ - Scalers & Encoders     │   │ - Review drafting      │
 │ - SQLAlchemy ORM   │   │ - Rule-based risk flags  │   │ - Incentive planner    │
 └──────┬─────────────┘   └──────────┬───────────────┘   └─────────┬──────────────┘
        │                            │                             │
 ┌──────▼────────────────────────────▼─────────────────────────────▼──────┐
 │                            Storage Layer                               │
 │   SQLite3 (talentpulse.db) / PostgreSQL  │  Model Binaries & Datasets  │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Tree

```plaintext
TalentPulse-Enterprise-Unified/
├── backend/
│   ├── alembic/                         # Database migrations
│   ├── app/
│   │   ├── core/                        # Config settings, JWT handling, security rules
│   │   ├── db/                          # Database connection, schemas, seed records
│   │   ├── models/                      # SQLAlchemy database models
│   │   ├── routers/                     # API endpoints (auth, employees, attrition, AI)
│   │   ├── schemas/                     # Pydantic data schemas
│   │   └── services/
│   │       ├── ai/                      # Attrition training scripts & scoring logic
│   │       └── genai/                   # Policy search, prompts, and review tools
│   ├── data/
│   │   ├── models/                      # Trained model files (.joblib) & accuracy logs (.json)
│   │   ├── ibm_hr_attrition.csv         # Baseline training dataset
│   │   └── talentpulse.db               # Local development database
│   ├── static/                          # Static dashboard distribution
│   ├── tests/                           # Integration test suite (Phases 1-8)
│   ├── requirements.txt                 # Backend Python dependencies
│   └── server.py                        # Backend bootstrap script
├── frontend/
│   ├── src/
│   │   ├── api/                         # Backend request client & auth session handling
│   │   ├── app/                         # App shell, routing table, global state
│   │   ├── components/ui/               # Reusable UI elements (dialogs, cards, tables, inputs)
│   │   ├── features/                    # Core modules (Attrition, Reviews, Leave, Directory)
│   │   └── styles/                      # Design tokens, resets, motion variables
│   ├── package.json
│   └── vite.config.js
├── Dockerfile                           # Production container build
├── docker-compose.yml                   # Container stack configuration
├── run.bat / start.sh                   # Native launch scripts
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
* **Python**: `3.10` or newer
* **Node.js**: `v18+` or `v20+` LTS
* **Package Managers**: `pip` and `npm`

---

### Step 1: Set Up Backend

1. **Move into backend directory and set up your virtual environment:**
   ```bash
   cd backend

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install Python packages:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure your environment:**
   ```bash
   cp .env.example .env
   ```

4. **Initialize database schema and load seed data:**
   ```bash
   alembic upgrade head
   python -m app.db.seed
   ```

5. **Start backend API server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

* API Docs (Swagger UI): `http://localhost:8000/docs`
* API Docs (ReDoc): `http://localhost:8000/redoc`

---

### Step 2: Set Up Frontend

1. **In a second terminal window, move to the frontend folder:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the local Vite dev server:**
   ```bash
   npm run dev
   ```

* Frontend UI: `http://localhost:5173`

---

## 🐳 Docker Quickstart

To run the whole application stack without setting up local runtimes:

```bash
docker-compose up --build -d
```

Check the logs anytime with:
```bash
docker-compose logs -f
```

The web dashboard will be live at `http://localhost:8000`.

---

## 👥 Test Accounts & RBAC

The seeded database comes with pre-configured accounts to test each role's interface:

| Role | Email | Password | Access Details |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@talentpulse.io` | `AdminPass123!` | Complete access, user control, system metrics, audit logs. |
| **HR Manager** | `hr@talentpulse.io` | `HRPass123!` | Attrition analytics, CSV employee imports, reviews, bonus suggestions. |
| **Employee** | `employee@talentpulse.io` | `EmpPass123!` | Personal dashboard, leave tracking, sentiment surveys, policy chat. |

---

## 🤖 AI & Machine Learning Workflows

### Attrition Scoring Engine
The predictive pipeline combines categorical and numerical employee data into an offline-trained **Random Forest Classifier**:

```text
Input Features:
- Years at Company
- Monthly Overtime Records
- Last Review Score
- Job Satisfaction Rating
- Department Assignment
- Current Compensation Level
             │
             ▼
   [ Data Preprocessing ]
   - StandardScaler for continuous features
   - OneHotEncoder for job roles & departments
             │
             ▼
   [ Random Forest Classifier ]
             │
             ▼
   Output: Risk Percentage (0-100%) + Top 3 Contributing Factors
```

To retrain the model on updated team data:
```bash
python -m app.services.ai.train_attrition
```
* The updated pipeline is saved to `backend/data/models/attrition_model.joblib`.
* Validation scores (Precision, Recall, ROC-AUC) update in `backend/data/models/model_metrics.json`.

---

## 📡 API Overview

### Authentication (`/api/auth`)
* `POST /api/auth/login` - Validates user credentials and returns a JWT access token.
* `POST /api/auth/refresh` - Refreshes an active session token.
* `GET  /api/auth/me` - Returns profile details and permissions for the signed-in user.

### Employees (`/api/employees`)
* `GET  /api/employees/` - Returns the employee directory with department and role filters.
* `POST /api/employees/` - Adds a new employee record.
* `POST /api/employees/bulk-upload` - Uploads and processes a roster via CSV.

### Retention & Attrition (`/api/attrition`)
* `POST /api/attrition/predict/{employee_id}` - Runs attrition scoring for an employee.
* `GET  /api/attrition/department-summary` - Returns team-by-team flight risk statistics.

### GenAI Tools (`/api/genai`)
* `POST /api/genai/rag/query` - Searches company policy documents to answer employee questions.
* `POST /api/genai/review/draft` - Builds a drafted performance review from employee metrics.
* `POST /api/genai/bonus/recommend` - Suggests calibrated retention incentives.

---

## 🧪 Test Verification

TalentPulse includes eight test suites covering every layer from security to AI:

```bash
cd backend
pytest tests/ -v
```

* `test_phase1_auth.py` - Verifies password hashing, token generation, and expired session safety.
* `test_phase2_core_workflows.py` - Checks employee creation, profile edits, and team reassignment.
* `test_phase3_attrition.py` - Confirms model loading and prediction accuracy.
* `test_phase4_performance_flags.py` - Tests automated logic flags for workload burnout.
* `test_phase5_genai.py` - Verifies policy document search and prompt template outputs.
* `test_phase6_admin_metrics.py` - Tests company-wide analytics and calculation queries.
* `test_phase7_bonus.py` - Checks retention incentive math and safety limits.
* `test_phase8_security.py` - Validates route protections, role limits, and query parameter safety.

---

## 📄 License

This repository is distributed under the **MIT License**. Check the [LICENSE](LICENSE) file for more information.