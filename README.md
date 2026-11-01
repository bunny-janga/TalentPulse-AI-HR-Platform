<div align="center">

# 🚀 TalentPulse AI
### Enterprise Workforce Intelligence & Predictive Attrition Diagnostic Platform

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Flask%203.x-black?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn%20%7C%20Random%20Forest-orange?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/database-SQLite3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Frontend Telemetry](https://img.shields.io/badge/telemetry-Chart.js-FF6384?logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Deployment Ready](https://img.shields.io/badge/deployment-Docker%20%7C%20Render%20%7C%20Gunicorn-success?logo=docker&logoColor=white)](#-cloud-deployment)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

<p align="center">
  <b>A full-stack, enterprise HR telemetry suite built to identify employee burnout, predict flight risk, and auto-generate actionable retention blueprints with zero data lock-in.</b>
</p>

[Key Features](#-key-features) •
[System Architecture](#-system-architecture) •
[Quickstart](#-quickstart-guide) •
[Demo Credentials](#-role-based-access--credentials) •
[ML Engine](#-machine-learning-engine) •
[API Reference](#-api-reference) •
[Deployment](#-cloud-deployment)

---

</div>

## 📌 Executive Summary

Modern People Operations teams often rely on retrospective exit interviews to identify workplace attrition. **TalentPulse AI** transforms attrition management from reactive diagnostics to proactive mitigation. 

By unifying workforce satisfaction metrics, overtime velocity, tenure brackets, and evaluation differentials into a trained **Random Forest Classification Pipeline**, TalentPulse calculates continuous attrition probabilities, isolates leading organizational stress vectors, and generates managerial retention blueprints.

---

## ✨ Key Features

- **🧠 Predictive ML Flight-Risk Scoring**: Incorporates a production-trained Scikit-learn Random Forest classifier pipeline (`attrition_model.joblib`) with automated feature scaling, one-hot encoding, and fallback rule heuristics.
- **🛡️ Strict Multi-Tier RBAC**: Three isolated user tiers with role-enforced client rendering and server-side route guards:
  - **Administrator**: Complete governance, user role modification, credential reset, and audit logs.
  - **HR Manager**: Diagnostic prediction suite, workforce directory, bulk CSV ingest, and telemetry dashboards.
  - **Employee**: Confidential sentiment pulse check-ins and organizational standards directory (administrative switchers automatically hidden).
- **📊 Real-Time Interactive Telemetry**: Native Chart.js dashboards rendering risk distributions, departmental benchmarks, and satisfaction-versus-workload burnout scatter plots.
- **📁 Enterprise Bulk CSV Ingestion**: Stream-based batch employee parsing with real-time model scoring and automated directory indexing.
- **🔐 Enterprise Authentication Suite**: PBKDF2-SHA256 password hashing, tokenized cryptographic invite generation, self-service forgot-password flows, and secure session management.
- **⚡ Turnkey Local & Cloud Execution**: Zero external database dependencies required out of the box using built-in SQLite persistence and automated schema migration.

---

## 🏛️ System Architecture

```text
                               +------------------------------------+
                               |     Client Browser Interface       |
                               |  (HTML5 / CSS3 / Vanilla JS ES6+)  |
                               +-----------------+------------------+
                                                 |
                                         HTTPS / JSON REST
                                                 |
                               +-----------------v------------------+
                               |     Flask Application Gateway      |
                               |    (server.py / WSGI Gunicorn)     |
                               +--------+------------------+--------+
                                        |                  |
                    +-------------------+                  +-------------------+
                    |                                                          |
        +-----------v-----------+                                  +-----------v-----------+
        |  Role & Auth Engine   |                                  |   ML Predictive Core  |
        |  - Session Management |                                  |  - Scikit-Learn Model |
        |  - PBKDF2 Hashing     |                                  |  - ColumnTransformer  |
        |  - RBAC Route Guards  |                                  |  - Retention Planner  |
        +-----------+-----------+                                  +-----------+-----------+
                    |                                                          |
                    +-------------------+                  +-------------------+
                                        |                  |
                               +--------v------------------v--------+
                               |    Local Relational Data Store     |
                               |         (talentpulse.db)           |
                               |  - Users    - Predictions          |
                               |  - Feedback - Requirements         |
                               +------------------------------------+
```

---

## 📂 Repository Structure

```text
talentpulse-ai/
├── .env.example              # Environment variable template
├── .gitignore                # Production ignore rules (caches, secrets, logs)
├── Dockerfile                # Production container specification
├── docker-compose.yml        # Multi-service local orchestration
├── Procfile                  # Dyno web process binding for PaaS
├── render.yaml               # Render Cloud Blueprint infrastructure-as-code
├── requirements.txt          # Production dependency pin-list
├── README.md                 # Project technical documentation
├── server.py                 # Core Flask backend application & REST API
├── train_model.py            # Standalone ML training & validation pipeline
├── talentpulse.db            # SQLite relational database (pre-seeded)
├── attrition_model.joblib    # Serialized Random Forest classification pipeline
├── training_data_sample.csv  # Benchmark workforce training dataset
└── static/                   # Production frontend assets
    ├── index.html            # Main workforce operations dashboard
    ├── login.html            # Role-separated authentication gateway
    ├── register.html         # Invite-only employee registration portal
    ├── forgot-password.html  # Self-service account recovery request
    ├── reset-password.html   # Cryptographic token verification & reset
    ├── app.js                # Frontend controllers, Chart.js graphs, & DOM RBAC
    └── style.css             # Glassmorphic design system and styling
```

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python**: Version `3.10` or higher
- **Package Manager**: `pip`
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/talentpulse-ai.git
cd talentpulse-ai
```

### 2. Set Up a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database (Optional if using pre-bundled DB)
The project comes pre-seeded with sample employees, company policies, and role-based test accounts. If you wish to rebuild the database from scratch:
```bash
python -c "import server; server.init_db(); print('Database schema built and seeded successfully!')"
```

### 5. Launch the Platform
```bash
python server.py
```

The application will be live at:
👉 **`http://localhost:5000`** *(or `http://127.0.0.1:5000`)*

---

## 👥 Role-Based Access & Credentials

The platform includes three out-of-the-box demonstration accounts configured to test the RBAC interface boundaries:

| Role | Username | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **🛡️ Administrator** | `admin` | `admin123` | Full console, user administration, role switches, and sentiment audits. |
| **📊 HR Manager** | `hr_manager` | `hr123` | Diagnostic engine, bulk CSV ingestion, workforce directory, visual charts. |
| **👤 Employee** | `employee_john` | `emp123` | Policy benchmarks, personal pulse check-in (management switchers hidden). |

*(You can also click the quick-login role selectors on the right side of the login portal to auto-fill these credentials).*

---

## 🤖 Machine Learning Engine

The attrition diagnostic model operates on a custom **Scikit-learn** pipeline trained on workforce metrics with balanced class weights to address natural attrition class imbalances.

### Feature Pipeline
The model processes 7 key organizational parameters:
1. **Satisfaction Score** (`0.0 - 5.0` float)
2. **Tenure at Organization** (Years float)
3. **Average Monthly Hours** (Integer hours)
4. **Last Performance Evaluation** (`0.0 - 5.0` float)
5. **Department** (Categorical: `Engineering`, `Sales`, `Marketing`, `Product`, `Operations`, `HR`)
6. **Salary Tier** (Categorical: `Low`, `Medium`, `High`)
7. **Overtime Status** (Binary: `Yes` or `No`)

### Retraining the Model
You can retrain the model on the bundled reference data or supply your own historical workforce attrition CSV:

```bash
# Retrain using built-in 3,500 sample workforce dataset:
python train_model.py

# Retrain using custom company historical dataset:
python train_model.py path/to/my_company_attrition.csv
```

The training script automatically evaluates the test partition, displays precision/recall/F1 metrics, and writes the output pipeline directly to `attrition_model.joblib`.

---

## 📡 API Reference

### Authentication & Identity
| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/login` | Public | Authenticates user credentials and provisions session cookie. |
| `GET` | `/api/logout` | Session | Clears session cookie and redirects to `/login.html`. |
| `GET` | `/api/user-status` | Session | Returns current authenticated user metadata and active role. |
| `POST` | `/api/profile/change-password` | Session | In-profile credential modification. |

### Workforce Operations (HR / Admin)
| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/predict-attrition` | HR / Admin | Computes risk percentage and generates retention blueprint. |
| `GET` | `/api/employees/directory` | HR / Admin | Retrieves all indexed employees and historical diagnostic scores. |
| `POST` | `/api/employees/add` | HR / Admin | Evaluates and appends a single employee to the directory. |
| `POST` | `/api/employees/bulk-import` | HR / Admin | Processes multi-row employee CSV file with batch scoring. |
| `GET` | `/api/analytics/charts` | HR / Admin | Returns aggregated telemetry for Chart.js rendering. |
| `GET` | `/api/feedback-list` | HR / Admin | Fetches submitted confidential employee sentiment feedback. |

### Administrator Governance
| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/users` | Admin Only | Lists all registered accounts and assigned role privileges. |
| `POST` | `/api/admin/users/<id>/role` | Admin Only | Updates a target user's role (`admin`, `hr`, `employee`). |
| `POST` | `/api/admin/users/<id>/reset-password` | Admin Only | Overwrites user password with new administrative hash. |
| `DELETE`| `/api/admin/users/<id>` | Admin Only | Permanently removes a user account from the system. |

---

## ☁️ Cloud Deployment

### Deploy to Render (Blueprint)
The repository includes a production `render.yaml` specification for immediate deployment:
1. Fork or push this repository to your GitHub account.
2. Navigate to [dashboard.render.com](https://dashboard.render.com) $\rightarrow$ select **New +** $\rightarrow$ **Blueprint**.
3. Connect your repository. Render will automatically parse `render.yaml`, configure the Python 3 runtime, execute build dependencies, and start `gunicorn server:app`.

### Deploy with Docker & Docker Compose
To run TalentPulse AI inside an isolated container:

```bash
# Build and run containerized service
docker-compose up --build -d

# Check runtime logs
docker-compose logs -f
```

The containerized service exposes port `5000` mapped directly to `http://localhost:5000`.

---

## 🔒 Security Best Practices

- **Zero Plaintext Credentials**: All passwords stored using salted PBKDF2 iterations via Werkzeug security primitives.
- **Session Protections**: Server-enforced cookie sessions with backend privilege validation on every administrative REST call.
- **Injection Mitigation**: Parameterized SQL queries utilized across all database interactions to prevent SQL injection vulnerabilities.
- **Environment Isolation**: Production secrets and external API configurations separated into uncommitted `.env` variables.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for further details.