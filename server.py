import os
import sqlite3
import secrets
import csv
import io
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "talentpulse-production-key-2026")
CORS(app)

DB_PATH = os.getenv("DB_PATH", "talentpulse.db")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

try:
    import joblib
    if os.path.exists("attrition_model.joblib"):
        ml_model = joblib.load("attrition_model.joblib")
    else:
        ml_model = None
except Exception:
    ml_model = None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Predictions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            satisfaction REAL,
            tenure REAL,
            avg_hours REAL,
            last_evaluation REAL,
            salary_level TEXT,
            overtime TEXT,
            risk_percentage REAL,
            risk_level TEXT,
            primary_factors TEXT,
            retention_plan TEXT
        )
    """)

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT
        )
    """)

    # Employee Feedback Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            username TEXT NOT NULL,
            full_name TEXT NOT NULL,
            department TEXT NOT NULL,
            work_life_rating REAL NOT NULL,
            workload_pacing TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Company Requirements Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            target_metric TEXT,
            mandatory_level TEXT DEFAULT 'Required'
        )
    """)

    # Invites Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'employee',
            department TEXT DEFAULT 'Engineering',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_used INTEGER DEFAULT 0
        )
    """)

    # Password Reset Tokens Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Seed Default Accounts if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        demo_users = [
            ("admin", generate_password_hash("admin123"), "admin", "System Administrator", "Executive", "admin@talentpulse.ai"),
            ("hr_manager", generate_password_hash("hr123"), "hr", "Sarah Jenkins", "People Operations", "sarah@talentpulse.ai"),
            ("employee_john", generate_password_hash("emp123"), "employee", "John Doe", "Engineering", "john@talentpulse.ai")
        ]
        cursor.executemany("""
            INSERT INTO users (username, password_hash, role, full_name, department, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, demo_users)
        print(" Seeded default accounts: admin, hr_manager, employee_john")

    # Seed Company Requirements if empty
    cursor.execute("SELECT COUNT(*) FROM company_requirements")
    if cursor.fetchone()[0] == 0:
        reqs = [
            ("Core Working Policy", "Standard Working Hours & Availability", "Maintain core collaboration availability between 10:00 AM and 4:00 PM. Overtime should not exceed 8 hrs/month without prior team notification.", "38-42 hrs / week", "Mandatory"),
            ("Performance & Delivery", "Sprint Milestone Completion", "Complete sprint deliverables with high test coverage and review pull requests within 24 business hours.", ">= 90% sprint velocity", "Standard"),
            ("Continuous Growth", "Professional Development & Training", "Utilize at least 4 hours monthly dedicated to technical upskilling, certifications, and architecture seminars.", "4 hrs / month", "Recommended"),
            ("Employee Well-Being", "Mandatory Disconnect Policy", "Team members must utilize at least 15 days of annual paid leave and refrain from work channels during scheduled PTO.", "100% PTO usage", "Mandatory"),
            ("Feedback & Transparency", "Bi-Weekly Sentiment Check-ins", "Participate in bi-weekly sentiment pulses and 1-on-1 career progression check-ins with department leads.", "1 pulse / month", "Mandatory")
        ]
        cursor.executemany("""
            INSERT INTO company_requirements (category, title, description, target_metric, mandatory_level)
            VALUES (?, ?, ?, ?, ?)
        """, reqs)

    # Seed Sample Predictions if empty
    cursor.execute("SELECT COUNT(*) FROM predictions")
    if cursor.fetchone()[0] == 0:
        sample_preds = [
            ("Alex Mercer", "Engineering", 2.2, 3.5, 230, 4.2, "Medium", "Yes", 78.5, "High", "Heavy Overtime, Low Satisfaction", "Retention plan generated"),
            ("Elena Rostova", "Engineering", 1.9, 4.0, 245, 4.5, "Low", "Yes", 88.0, "High", "Compensation Gap, High Hours", "Urgent compensation review required"),
            ("David Kim", "Sales", 3.1, 2.0, 195, 3.8, "Medium", "No", 42.0, "Moderate", "Commission pacing", "Standard progression review"),
            ("Maya Patel", "Sales", 2.4, 3.0, 215, 3.9, "Low", "Yes", 69.5, "High", "Territory reassignment", "1-on-1 check-in recommended"),
            ("Liam Scott", "Product", 4.2, 2.5, 175, 4.0, "High", "No", 12.0, "Low", "Stable Tenured Baseline", "High satisfaction maintained"),
            ("Chloe Bennett", "Product", 3.8, 1.8, 180, 3.9, "Medium", "No", 18.5, "Low", "Optimal flow", "Stable baseline"),
            ("Marcus Vance", "Operations", 3.2, 5.0, 190, 3.5, "Medium", "No", 34.0, "Low", "Career milestone pending", "Milestone review")
        ]
        cursor.executemany("""
            INSERT INTO predictions (name, department, satisfaction, tenure, avg_hours, last_evaluation, salary_level, overtime, risk_percentage, risk_level, primary_factors, retention_plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_preds)

    # Seed Sample Feedback if empty
    cursor.execute("SELECT COUNT(*) FROM employee_feedback")
    if cursor.fetchone()[0] == 0:
        sample_fb = [
            (3, "employee_john", "John Doe", "Engineering", 4.0, "Optimal Flow", "Sprint pacing is sustainable, would appreciate clearer promotion milestones."),
            (None, "elena_r", "Elena Rostova", "Engineering", 2.0, "High Overtime Strain (> 50 hrs/wk)", "Struggling with continuous production deployment support over weekends."),
            (None, "david_k", "David Kim", "Sales", 3.5, "Optimal Flow", "Quarterly quota is balanced, client response times are healthy.")
        ]
        cursor.executemany("""
            INSERT INTO employee_feedback (user_id, username, full_name, department, work_life_rating, workload_pacing, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_fb)

    conn.commit()
    conn.close()

init_db()

# --- Auth Routes ---

@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login.html")
    return send_from_directory("static", "index.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role, full_name, department, email FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        session["user"] = {
            "id": user[0],
            "username": user[1],
            "role": user[3],
            "full_name": user[4],
            "department": user[5],
            "email": user[6]
        }
        return jsonify({"success": True, "user": session["user"]})

    return jsonify({"success": False, "message": "Invalid username or password"}), 401

@app.route("/api/logout", methods=["GET", "POST"])
def api_logout():
    session.pop("user", None)
    return redirect("/login.html")

@app.route("/api/user-status")
def user_status():
    if "user" in session:
        return jsonify({"authenticated": True, "user": session["user"]})
    return jsonify({"authenticated": False}), 401

# --- Attrition Risk Engine & Retention Blueprint ---

def calculate_attrition_risk(emp: dict) -> dict:
    satisfaction = float(emp.get("satisfaction", 3.0))
    tenure = float(emp.get("tenure", 2.0))
    overtime = str(emp.get("overtime", "Yes")).strip().lower() in ["yes", "y", "true", "1"]
    hours = float(emp.get("avg_hours", 190))
    salary = str(emp.get("salary_level", "Medium")).strip().capitalize()
    eval_score = float(emp.get("last_evaluation", 3.5))

    base_risk = 0.20
    if satisfaction <= 2.0:
        base_risk += 0.40
    elif satisfaction <= 3.2:
        base_risk += 0.20

    if overtime:
        base_risk += 0.18
    if hours > 215:
        base_risk += 0.15
    if salary == "Low":
        base_risk += 0.12
    elif salary == "High":
        base_risk -= 0.10

    if tenure >= 3.0 and tenure <= 5.0 and salary == "Low":
        base_risk += 0.12

    prob = max(0.04, min(0.96, base_risk))
    risk_level = "High" if prob >= 0.65 else ("Moderate" if prob >= 0.35 else "Low")

    factors = []
    if satisfaction <= 2.5:
        factors.append("Low Job & Team Satisfaction")
    if overtime or hours > 210:
        factors.append("Heavy Monthly Workload & Burnout Strain")
    if salary == "Low":
        factors.append("Below-Market Salary Tier Compensation")
    if eval_score >= 4.0 and salary == "Low":
        factors.append("High Performance / Compensation Disconnect")
    if not factors:
        factors.append("Stable Tenured Baseline")

    return {
        "risk_percentage": round(prob * 100, 1),
        "risk_level": risk_level,
        "primary_factors": factors
    }

def generate_retention_plan(emp: dict, risk_data: dict) -> str:
    name = emp.get("name", "Employee")
    dept = emp.get("department", "Engineering")
    prob = risk_data["risk_percentage"]
    factors = ", ".join(risk_data["primary_factors"])

    return f"""# 📋 TalentPulse Retention Blueprint: {name}

### Executive Diagnosis
- **Employee**: {name} ({dept})
- **Attrition Flight Risk**: **{prob}%** ({risk_data['risk_level']} Risk)
- **Primary Trigger Indicators**: {factors}

---

### 🎯 3 High-Impact Retention Actions
1. **Immediate Compensation & Recognition Adjustment**
   - Address compensation friction points. Implement a performance-aligned adjustment or formal advancement band within 14 business days.
2. **Workload & Overtime Rebalancing**
   - Immediate redistribution of pending deliverables to cap weekly hours below 42 hours, curbing burnout momentum.
3. **Structured 1-on-1 Dialogue**
   - Schedule a private 30-minute career progression check-in. Focus on ownership, team psychological safety, and growth roadmaps.

### 💬 Recommended Manager Talking Points
- *"We value your recent high-impact contributions and want to ensure our pacing is sustainable."*
- *"What is one operational bottleneck or friction point we can remove from your day immediately?"*
- *"Let's map out where you want to be over the next 12 months and align compensation and responsibility accordingly."*
"""

@app.route("/api/predict-attrition", methods=["POST"])
def predict():
    user = session.get("user")
    if not user or user.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "error": "Access restricted to HR and Admin roles."}), 403

    data = request.json or {}
    risk_info = calculate_attrition_risk(data)
    plan = generate_retention_plan(data, risk_info)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (
                name, department, satisfaction, tenure, avg_hours, 
                last_evaluation, salary_level, overtime, 
                risk_percentage, risk_level, primary_factors, retention_plan
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("name", "Unknown"),
            data.get("department", "General"),
            float(data.get("satisfaction", 0)),
            float(data.get("tenure", 0)),
            float(data.get("avg_hours", 0)),
            float(data.get("last_evaluation", 0)),
            data.get("salary_level", "Medium"),
            data.get("overtime", "No"),
            risk_info["risk_percentage"],
            risk_info["risk_level"],
            ", ".join(risk_info["primary_factors"]),
            plan
        ))
        conn.commit()
        conn.close()
    except Exception as err:
        print(f"Database error saving prediction: {err}")

    return jsonify({
        "success": True,
        "risk_percentage": risk_info["risk_percentage"],
        "risk_level": risk_info["risk_level"],
        "primary_factors": risk_info["primary_factors"],
        "retention_plan": plan
    })

# --- Workforce Directory & Bulk Import Routes ---

@app.route("/api/employees/directory", methods=["GET"])
def get_employee_directory():
    user = session.get("user")
    if not user or user.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, department, satisfaction, tenure, avg_hours, 
               last_evaluation, salary_level, overtime, risk_percentage, risk_level, timestamp
        FROM predictions
        ORDER BY id DESC
    """)
    employees = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({"success": True, "employees": employees})

@app.route("/api/employees/add", methods=["POST"])
def add_new_employee():
    user = session.get("user")
    if not user or user.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.json or {}
    name = data.get("name", "").strip()
    department = data.get("department", "Engineering").strip()
    satisfaction = float(data.get("satisfaction", 3.5))
    tenure = float(data.get("tenure", 1.0))
    avg_hours = float(data.get("avg_hours", 180))
    last_eval = float(data.get("last_evaluation", 3.8))
    salary_level = data.get("salary_level", "Medium").strip().capitalize()
    overtime = data.get("overtime", "No").strip().capitalize()

    if not name:
        return jsonify({"success": False, "error": "Employee name is required."}), 400

    risk_info = calculate_attrition_risk(data)
    plan = generate_retention_plan(data, risk_info)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (
                name, department, satisfaction, tenure, avg_hours, 
                last_evaluation, salary_level, overtime, 
                risk_percentage, risk_level, primary_factors, retention_plan
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, department, satisfaction, tenure, avg_hours,
            last_eval, salary_level, overtime,
            risk_info["risk_percentage"], risk_info["risk_level"],
            ", ".join(risk_info["primary_factors"]), plan
        ))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Employee {name} successfully added to directory!"})
    except Exception as err:
        return jsonify({"success": False, "error": str(err)}), 500

@app.route("/api/employees/bulk-import", methods=["POST"])
def bulk_import_employees():
    user = session.get("user")
    if not user or user.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded."}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "" or not uploaded_file.filename.endswith(".csv"):
        return jsonify({"success": False, "error": "Please upload a valid .csv file."}), 400

    try:
        stream = io.StringIO(uploaded_file.stream.read().decode("utf-8-sig"), newline=None)
        reader = csv.DictReader(stream)
        reader.fieldnames = [name.strip().lower() for name in reader.fieldnames or []]

        required_columns = {"name", "department", "satisfaction", "tenure", "avg_hours", "last_evaluation", "salary_level", "overtime"}
        if not required_columns.issubset(set(reader.fieldnames)):
            missing = required_columns - set(reader.fieldnames)
            return jsonify({"success": False, "error": f"CSV missing required headers: {', '.join(missing)}"}), 400

        inserted_records = []
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue

            emp_data = {
                "name": name,
                "department": (row.get("department") or "General").strip(),
                "satisfaction": float(row.get("satisfaction") or 3.0),
                "tenure": float(row.get("tenure") or 1.0),
                "avg_hours": float(row.get("avg_hours") or 180),
                "last_evaluation": float(row.get("last_evaluation") or 3.5),
                "salary_level": (row.get("salary_level") or "Medium").strip().capitalize(),
                "overtime": "Yes" if (row.get("overtime") or "").strip().lower() in ["yes", "y", "true", "1"] else "No"
            }

            risk_info = calculate_attrition_risk(emp_data)
            plan = generate_retention_plan(emp_data, risk_info)

            inserted_records.append((
                emp_data["name"],
                emp_data["department"],
                emp_data["satisfaction"],
                emp_data["tenure"],
                emp_data["avg_hours"],
                emp_data["last_evaluation"],
                emp_data["salary_level"],
                emp_data["overtime"],
                risk_info["risk_percentage"],
                risk_info["risk_level"],
                ", ".join(risk_info["primary_factors"]),
                plan
            ))

        if not inserted_records:
            return jsonify({"success": False, "error": "No valid employee rows found in the CSV file."}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO predictions (
                name, department, satisfaction, tenure, avg_hours, 
                last_evaluation, salary_level, overtime, 
                risk_percentage, risk_level, primary_factors, retention_plan
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, inserted_records)
        conn.commit()
        conn.close()

        return jsonify({
            "success": True, 
            "message": f"Successfully imported {len(inserted_records)} employees into the directory!"
        })

    except Exception as err:
        return jsonify({"success": False, "error": f"Failed to process CSV: {str(err)}"}), 500

# --- Company Requirements Routes ---

@app.route("/api/company-requirements", methods=["GET"])
def get_company_requirements():
    if "user" not in session:
        return jsonify({"success": False, "error": "Please log in"}), 401

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_requirements ORDER BY id ASC")
    reqs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({"success": True, "requirements": reqs})

# --- Employee Feedback Routes ---

@app.route("/api/submit-feedback", methods=["POST"])
def submit_feedback():
    if "user" not in session:
        return jsonify({"success": False, "error": "Unauthorized."}), 401

    user = session["user"]
    data = request.json or {}

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employee_feedback (user_id, username, full_name, department, work_life_rating, workload_pacing, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user.get("id"),
            user.get("username"),
            user.get("full_name"),
            user.get("department"),
            float(data.get("rating", 4.0)),
            data.get("pacing", "Optimal"),
            data.get("notes", "")
        ))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Feedback submitted successfully."})
    except Exception as err:
        return jsonify({"success": False, "error": str(err)}), 500

@app.route("/api/feedback-list")
def feedback_list():
    user = session.get("user")
    if not user or user.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "error": "Unauthorized."}), 403

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employee_feedback ORDER BY timestamp DESC LIMIT 50")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "data": rows})

# --- Visual Analytics Endpoint (Chart.js) ---

@app.route("/api/analytics/charts", methods=["GET"])
def get_chart_analytics():
    user = session.get("user")
    if not user or user.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT department, ROUND(AVG(risk_percentage), 1) as avg_risk, COUNT(*) as total_evals
        FROM predictions
        GROUP BY department
    """)
    dept_stats = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT risk_level, COUNT(*) as count
        FROM predictions
        GROUP BY risk_level
    """)
    risk_dist = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT name, satisfaction, avg_hours, risk_percentage, risk_level
        FROM predictions
        ORDER BY id DESC LIMIT 40
    """)
    scatter_data = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify({
        "success": True,
        "department_risks": dept_stats,
        "risk_distribution": risk_dist,
        "scatter_metrics": scatter_data
    })

# --- In-Profile Change Password ---

@app.route("/api/profile/change-password", methods=["POST"])
def change_password():
    if "user" not in session:
        return jsonify({"success": False, "error": "Not authenticated."}), 401

    user_id = session["user"]["id"]
    data = request.json or {}
    current_pw = data.get("current_password", "").strip()
    new_pw = data.get("new_password", "").strip()

    if len(new_pw) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters long."}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if not row or not check_password_hash(row[0], current_pw):
        conn.close()
        return jsonify({"success": False, "error": "Current password is incorrect."}), 400

    new_hash = generate_password_hash(new_pw)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Password updated successfully!"})

# --- Self-Service Forgot Password ---

@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json or {}
    identifier = data.get("identifier", "").strip()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE username = ? OR email = ?", (identifier, identifier))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"success": True, "message": "If an account exists, a recovery link has been generated."})

    user_id = user[0]
    token = secrets.token_urlsafe(24)
    cursor.execute("INSERT INTO password_resets (token, user_id) VALUES (?, ?)", (token, user_id))
    conn.commit()
    conn.close()

    reset_url = f"{request.host_url}reset-password.html?token={token}"
    return jsonify({
        "success": True,
        "message": "Recovery token generated successfully.",
        "reset_url": reset_url
    })

@app.route("/api/reset-password", methods=["POST"])
def execute_password_reset():
    data = request.json or {}
    token = data.get("token", "").strip()
    new_pw = data.get("new_password", "").strip()

    if len(new_pw) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, is_used FROM password_resets WHERE token = ?", (token,))
    record = cursor.fetchone()

    if not record or record[2] == 1:
        conn.close()
        return jsonify({"success": False, "error": "Invalid or expired reset token."}), 400

    reset_id, user_id, _ = record
    new_hash = generate_password_hash(new_pw)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    cursor.execute("UPDATE password_resets SET is_used = 1 WHERE id = ?", (reset_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Password reset successful! You can now log in."})

# --- Invite & Registration Routes ---

@app.route("/api/create-invite", methods=["POST"])
def create_invite():
    user = session.get("user")
    if not user or user.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.json or {}
    email = data.get("email", "").strip()
    role = data.get("role", "employee").strip()
    department = data.get("department", "Engineering").strip()

    token = secrets.token_urlsafe(16)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invites (token, email, role, department)
        VALUES (?, ?, ?, ?)
    """, (token, email, role, department))
    conn.commit()
    conn.close()

    invite_url = f"{request.host_url}register.html?token={token}"
    return jsonify({"success": True, "invite_url": invite_url})

@app.route("/api/verify-invite", methods=["GET"])
def verify_invite():
    token = request.args.get("token", "").strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email, role, department, is_used FROM invites WHERE token = ?", (token,))
    invite = cursor.fetchone()
    conn.close()

    if not invite:
        return jsonify({"valid": False, "error": "Invalid or expired invite token."}), 404
    if invite[3] == 1:
        return jsonify({"valid": False, "error": "This invite link has already been used."}), 400

    return jsonify({"valid": True, "email": invite[0], "role": invite[1], "department": invite[2]})

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    token = data.get("token", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    full_name = data.get("full_name", "").strip()

    if not username or not password or not full_name:
        return jsonify({"success": False, "error": "All fields are required."}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, department, is_used, email FROM invites WHERE token = ?", (token,))
    invite = cursor.fetchone()

    if not invite or invite[3] == 1:
        conn.close()
        return jsonify({"success": False, "error": "Invalid or expired invite."}), 400

    invite_id, assigned_role, assigned_dept, _, email = invite
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "Username already exists."}), 400

    pw_hash = generate_password_hash(password)
    cursor.execute("""
        INSERT INTO users (username, password_hash, role, full_name, department, email)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, pw_hash, assigned_role, full_name, assigned_dept, email))

    cursor.execute("UPDATE invites SET is_used = 1 WHERE id = ?", (invite_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Account created! Please log in."})

# --- Administrator Governance Routes ---

def is_admin():
    user = session.get("user")
    return user and user.get("role") == "admin"

@app.route("/api/admin/users", methods=["GET"])
def admin_get_users():
    if not is_admin():
        return jsonify({"success": False, "error": "Admin privileges required."}), 403

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, full_name, department, email FROM users ORDER BY id ASC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "users": users})

@app.route("/api/admin/users/<int:user_id>/role", methods=["POST"])
def admin_update_role(user_id):
    if not is_admin():
        return jsonify({"success": False, "error": "Admin privileges required."}), 403

    data = request.json or {}
    new_role = data.get("role")
    if new_role not in ["admin", "hr", "employee"]:
        return jsonify({"success": False, "error": "Invalid role."}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Role updated to {new_role}."})

@app.route("/api/admin/users/<int:user_id>/reset-password", methods=["POST"])
def admin_reset_password(user_id):
    if not is_admin():
        return jsonify({"success": False, "error": "Admin privileges required."}), 403

    data = request.json or {}
    new_password = data.get("new_password", "").strip()

    if len(new_password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400

    new_hash = generate_password_hash(new_password)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Password reset successfully."})

@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    if not is_admin():
        return jsonify({"success": False, "error": "Admin privileges required."}), 403

    if session.get("user", {}).get("id") == user_id:
        return jsonify({"success": False, "error": "Cannot delete own active account."}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "User deleted."})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 TalentPulse AI Platform running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
