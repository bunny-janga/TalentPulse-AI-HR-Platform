# TalentPulse AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Three.js](https://img.shields.io/badge/Three.js-WebGL-black?logo=three.js&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-RandomForest-F7931E?logo=scikit-learn&logoColor=white)

TalentPulse AI is a full-stack HR intelligence and employee retention platform built for mid-to-large IT delivery centers. Instead of forcing HR teams and engineering managers to dig through disconnected spreadsheets, it brings workforce health, leave approvals, policy Q&A, and attrition risk forecasting into a single responsive web application.

Built by **Team GG-13 (GenAI Guardians)** using a 3D WebGL frontend, a FastAPI backend with strict role-based access control, a scikit-learn attrition model, and grounded GenAI helpers.

---

## Why We Built This

IT delivery hubs regularly deal with ~20–22% annual turnover—often driven by sustained sprint overtime, delayed compensation reviews, and long commutes. By the time an employee submits a resignation letter, it is usually too late to intervene.

TalentPulse AI addresses this on two fronts:
1. **Early Risk Visibility for Leaders:** A RandomForest classifier trained on 1,200 synthetic workforce records highlights retention risks early while keeping sensitive risk scores completely hidden from non-managerial roles.
2. **Everyday Self-Service for Staff:** Employees get a clean portal to ask HR policy questions, check announcements, apply for time off, and share workplace feedback without unnecessary clutter.

---

## Tech Stack

- **Frontend:** HTML5, Tailwind CSS, Vanilla JavaScript, Three.js (WebGL)
- **Backend:** Python, FastAPI, Uvicorn, Pydantic
- **Authentication & Security:** HMAC-SHA256 JWT tokens, SHA-256 password hashing, Role-Based Access Control (RBAC)
- **Database:** SQLite (zero-config local persistence) + PostgreSQL-ready DDL (`database/schema.sql`)
- **Machine Learning & NLP:** `scikit-learn` (`RandomForestClassifier`, `TfidfVectorizer`, cosine similarity), `pandas`, `NumPy`, `joblib`

---

## Role-Based Workspaces

Every user logs in with their corporate email, password, and assigned role. The interface and API endpoints adapt strictly to what each role is permitted to see and do:

| Feature / Workspace | Employee | Manager | HR Executive | Admin |
| :--- | :---: | :---: | :---: | :---: |
| Ask HR Policy Questions (RAG Helpdesk) | Yes | — | Yes | Yes |
| Company Updates & Pulse Feedback | Yes | — | Yes | Yes |
| Apply for Leave & View Own Records | Yes | — | — | — |
| Approve Team Leaves & Conduct Reviews | — | Yes | — | Yes |
| Team Attrition Risk Radar (ML) | Hidden | Pod Only | Org-Wide | Org-Wide |
| Retention Playbook & Stay-Interview GenAI | — | Yes | — | Yes |
| Policy Publisher, Surveys & Exit Summarizer | — | — | Yes | Yes |
| Onboard New Joiners (`+ Add Employee`) | — | Yes | Yes | Yes |
| Department Hierarchy & System Settings | — | — | — | Yes |
| Forgot Password, Change Password & Terms | Yes | Yes | Yes | Yes |

---

## Project Layout

```text
talentpulse-ai/
├── LICENSE                        # MIT License
├── README.md                      # Project documentation
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container build file
├── .gitignore                     # Git ignore rules
├── database/
│   └── schema.sql                 # Relational SQL schema
├── ml_engine/
│   └── attrition_pipeline.py      # Synthetic dataset & RandomForest model trainer
├── backend/
│   └── app/
│       └── main.py                # FastAPI routes, JWT auth, SQLite setup & RAG logic
└── frontend/
    └── index.html                 # 3D WebGL UI & role-based workspaces
```

---

## Getting Started

### 1. Clone and create a virtual environment

```powershell
git clone https://github.com/<your-username>/talentpulse-ai.git
cd talentpulse-ai
python -m venv venv
.env\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Train the attrition model

```powershell
python ml_engine/attrition_pipeline.py
```

### 4. Start the server (Desktop & Mobile access)

Binding to `0.0.0.0` lets you open the app on your laptop as well as any phone or tablet on the same Wi-Fi network:

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

- **Local PC:** `http://127.0.0.1:8000`
- **Mobile / Other Devices:** `http://<your-pc-ipv4-address>:8000`
- **Interactive API Docs (Swagger):** `http://127.0.0.1:8000/docs`

---

## Demo Accounts

These accounts are seeded automatically when the server starts for the first time:

| Role | Email | Password |
| :--- | :--- | :--- |
| **Employee** | `employee@talentpulse.ai` | `Emp@123` |
| **Manager** | `manager@talentpulse.ai` | `Mgr@123` |
| **HR Executive** | `hr@talentpulse.ai` | `Hr@123` |
| **Admin** | `admin@talentpulse.ai` | `Admin@123` |

---

## License

Released under the [MIT License](LICENSE).
