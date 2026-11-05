# TalentPulse AI - Unified Enterprise HR & Operations Platform

An enterprise-ready HRMS combining:
1. **Executive Portal & Dashboard (`portal_dashboard.html` / `/portal`):**
   - **Top-right Login button** that opens a Department & Role selector dropdown (**Admin**, **HR**, **Employee**).
   - **Right-side slide-over login drawer** with dedicated security badges, department pickers, and pre-configured demo credentials.
   - **Leave & Holidays Dashboard:** Annual leave remaining, Public holidays, Sick/Casual quotas, and department attendance metrics.
   - **Leave Entitlements Table:** Accrual rates, notice periods, and carry-forward rules for PL, CL, SL, Maternity/Paternity, and Bereavement.
   - **Company Holiday Calendar:** Highlighted upcoming national & company festival breaks.
   - **Comprehensive Terms & Conditions:** Interactive accordion covering leave submission protocols, holiday comp-off/overtime, carry-over caps, and remote attendance compliance.

2. **Advanced AI & Intelligence Layer:**
   - **AI 1 - Attrition Prediction:** Scikit-Learn machine learning pipeline with risk bands (Low/Medium/High) and top positive/negative drivers.
   - **AI 2 - Performance Trend Flagging:** Automated detection of 2+ consecutive declining appraisal review cycles.
   - **GenAI 1 - RAG HR Policy Helpdesk:** Semantic search and grounded Q&A over company policy documents with fallback to HR Operations.
   - **GenAI 2 - Appraisal Review Drafting:** Expands bullet points into Summary, Strengths, Growth Areas, and Goals.
   - **GenAI 3 - Exit & Survey Sentiment Analyzer:** Thematic clustering (burnout, compensation, career growth) with automated action recommendations.

3. **Full React/Vite Frontend:**
   - Production single-page application under `frontend/` with routing, UI components, and state management.

---

## How to Run in VS Code

### Quickest Way (Windows):
Double click or run `run.bat` in the terminal.

### Manual Launch (Terminal in VS Code):

#### Option A: FastAPI Enterprise Server (Recommended)
```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run backend
cd backend
python -c "import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000)"
```
- Open Web Portal: `http://localhost:8000/portal` or `http://localhost:8000/ui`
- Open API Docs: `http://localhost:8000/docs`

#### Option B: Standalone Flask Server
```bash
cd backend
python server.py
```
- Open in browser: `http://localhost:8000`

#### Option C: React Dev Server (Frontend)
```bash
cd frontend
npm install
npm run dev
```

---

## Pre-configured Demo Logins:
- **Admin:** `admin@talentpulse.local` / `Admin123!`
- **HR Operations:** `hr@talentpulse.local` / `Hr123!`
- **Employee:** `employee@talentpulse.local` / `Employee123!`
