import os
import json
import joblib
import pandas as pd
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.review import PerformanceReview
from app.models.survey import SurveyResponse
from app.models.attrition import AttritionScore
from app.services.ai.train_attrition import FEATURE_NAMES, train_and_evaluate_model

_model = None

def get_attrition_model():
    """Lazily loads the trained ML model from disk or trains it if missing."""
    global _model
    if _model is not None:
        return _model

    model_path = Path(settings.MODEL_DIR) / "attrition_model.joblib"
    if not model_path.exists():
        train_and_evaluate_model()

    try:
        _model = joblib.load(model_path)
    except Exception:
        # Pickle from another scikit-learn version (or corrupted): retrain once and reload.
        train_and_evaluate_model()
        _model = joblib.load(model_path)
    return _model

def extract_employee_features(employee: Employee, db: Session) -> Dict[str, Any]:
    """
    Extracts all 8 predictive features for an employee directly from the database:
    tenure, salary band, overtime, rating, review trend, leave frequency, survey sentiment, promotion gap.
    """
    today = date.today()

    # 1. Tenure
    tenure = float(employee.years_at_company)

    # 2. Salary Level (1: Low, 2: Medium, 3: High)
    band_lower = employee.salary_band.lower() if employee.salary_band else "medium"
    if "low" in band_lower:
        salary_level = 1
    elif "high" in band_lower:
        salary_level = 3
    else:
        salary_level = 2

    # 3. Overtime
    overtime = 1 if employee.overtime_status else 0

    # 4. Performance Rating
    perf_rating = float(employee.performance_rating)

    # 5. Performance Trend (latest rating - previous rating & consecutive drops)
    reviews = db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == employee.id,
        PerformanceReview.status == "COMPLETED"
    ).order_by(PerformanceReview.created_at.desc()).all()

    consecutive_drops = 0
    has_consecutive_decline = False
    if len(reviews) >= 2:
        perf_trend = float(reviews[0].rating - reviews[1].rating)
    else:
        perf_trend = 0.0

    if len(reviews) >= 3:
        chronological = sorted(reviews, key=lambda r: r.created_at)
        ratings = [r.rating for r in chronological]
        for i in range(len(ratings) - 1, 0, -1):
            if ratings[i] < ratings[i - 1]:
                consecutive_drops += 1
            else:
                break
        if consecutive_drops >= 2:
            has_consecutive_decline = True

    # 6. Leave Frequency (Leaves applied in past 365 days)
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    leave_count = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee.id,
        LeaveRequest.created_at >= one_year_ago
    ).count()

    # 7. Survey Sentiment
    survey_responses = db.query(SurveyResponse).filter(
        SurveyResponse.employee_id == employee.id
    ).all()
    if survey_responses:
        valid_sentiments = [r.sentiment_score for r in survey_responses if r.sentiment_score is not None]
        avg_sentiment = round(sum(valid_sentiments) / len(valid_sentiments), 2) if valid_sentiments else 0.0
    else:
        avg_sentiment = 0.0

    # 8. Promotion Gap (years since last promotion)
    promo_date = employee.last_promotion_date or employee.hire_date
    if promo_date:
        promotion_gap = round((today - promo_date).days / 365.25, 2)
    else:
        promotion_gap = 1.0

    return {
        "tenure": tenure,
        "salary_level": salary_level,
        "overtime": overtime,
        "performance_rating": perf_rating,
        "performance_trend": perf_trend,
        "leave_frequency": leave_count,
        "survey_sentiment": avg_sentiment,
        "promotion_gap": promotion_gap,
        "has_consecutive_decline": has_consecutive_decline,
        "consecutive_drops": consecutive_drops
    }

# "Healthy" reference values: how far the predicted risk falls when ONE input is moved to this value
# is that input's contribution to this person's score (a one-feature counterfactual explanation).
def _reference_value(name: str, f: Dict[str, Any]):
    return {
        "overtime": 0,
        "promotion_gap": min(f["promotion_gap"], 1.0),
        "survey_sentiment": max(f["survey_sentiment"], 0.3),
        "performance_trend": max(f["performance_trend"], 0.0),
        "leave_frequency": min(f["leave_frequency"], 2),
        "salary_level": max(f["salary_level"], 2),
        "performance_rating": max(f["performance_rating"], 3.5),
        "tenure": f["tenure"],
    }[name]


def _factor_text(name: str, f: Dict[str, Any]) -> str:
    if name == "overtime":
        return "Frequent overtime and on-call load"
    if name == "promotion_gap":
        return f"No promotion for {f['promotion_gap']:.1f} years"
    if name == "survey_sentiment":
        if f["survey_sentiment"] < 0:
            return f"Negative engagement sentiment in pulse surveys ({f['survey_sentiment']:+.2f})"
        return f"Lukewarm engagement sentiment in pulse surveys ({f['survey_sentiment']:+.2f})"
    if name == "performance_trend":
        if f.get("has_consecutive_decline"):
            return f"Performance alert: {f.get('consecutive_drops', 2)}+ declining ratings in a row"
        return f"Falling review rating ({f['performance_trend']:+.1f} vs last cycle)"
    if name == "salary_level":
        return "Pay sits in the entry salary band"
    if name == "leave_frequency":
        return f"High leave frequency ({int(f['leave_frequency'])} requests in 12 months)"
    if name == "performance_rating":
        return f"Low latest performance rating ({f['performance_rating']:.1f}/5)"
    return f"Long tenure plateau ({f['tenure']:.1f} years)"


# Keyword -> suggested retention action. Matched against the factor text above.
_ACTIONS = [
    ("overtime", "Rebalance the on-call rota and offer comp-off or an on-call allowance."),
    ("promotion", "Hold a career-path conversation and put them forward in the next promotion cycle."),
    ("engagement sentiment", "Run a private stay-interview to find out what is frustrating them."),
    ("performance alert", "Schedule a supportive 1-on-1 on recent ratings and agree a development plan."),
    ("falling review", "Schedule a supportive 1-on-1 on recent ratings and agree a development plan."),
    ("entry salary", "Ask HR to benchmark pay against the market and review the band."),
    ("leave frequency", "Check in on workload and wellbeing before it turns into burnout."),
    ("low latest performance", "Pair them with a mentor and set two or three clear goals for next cycle."),
    ("tenure plateau", "Offer a stretch project, mentoring role or lateral move."),
]


def actions_for_factors(factors: List[str]) -> List[str]:
    out: List[str] = []
    for text in factors:
        low = text.lower()
        for key, action in _ACTIONS:
            if key in low and action not in out:
                out.append(action)
                break
    return out


def explain_with_model(clf, features: Dict[str, Any], prob: float) -> List[str]:
    """Top-3 drivers from the model itself: reset each input to a healthy value, see how much the risk drops."""
    base = {k: features[k] for k in FEATURE_NAMES}
    rows = [base]
    for name in FEATURE_NAMES:
        alt = dict(base)
        alt[name] = _reference_value(name, features)
        rows.append(alt)
    probs = clf.predict_proba(pd.DataFrame(rows)[FEATURE_NAMES])[:, 1]
    deltas = [(float(probs[0] - probs[i + 1]), name) for i, name in enumerate(FEATURE_NAMES)]
    deltas = [d for d in deltas if d[0] >= 0.01]
    deltas.sort(reverse=True)
    if not deltas:
        return ["No single factor stands out; risk is spread thinly across inputs"] if prob >= 0.25 else ["No notable risk drivers"]
    return [_factor_text(name, features) for _, name in deltas[:3]]


def explain_factors(features: Dict[str, Any], risk_score: float) -> List[str]:
    """Back-compat wrapper that uses the loaded model."""
    return explain_with_model(get_attrition_model(), features, risk_score)


def predict_employee_attrition(employee: Employee, db: Session) -> Dict[str, Any]:
    """Extracts features, runs the ML model, and returns risk_score, risk_band, top factors and actions."""
    clf = get_attrition_model()
    features = extract_employee_features(employee, db)

    df_features = pd.DataFrame([features])[FEATURE_NAMES]
    prob = float(clf.predict_proba(df_features)[0][1])
    risk_score = round(prob, 2)

    if risk_score >= 0.50:
        risk_band = "HIGH"
    elif risk_score >= 0.25:
        risk_band = "MEDIUM"
    else:
        risk_band = "LOW"

    factors = explain_with_model(clf, features, prob)

    return {
        "risk_score": risk_score,
        "risk_band": risk_band,
        "top_factors": factors,
        "suggested_actions": actions_for_factors(factors) if risk_band != "LOW" else [],
        "features": features
    }

def batch_score_all_employees(db: Session) -> Dict[str, Any]:
    """
    Batch scoring: calculates and persists attrition scores for all active employees.
    """
    employees = db.query(Employee).all()
    updated_count = 0
    band_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for emp in employees:
        pred = predict_employee_attrition(emp, db)
        band_counts[pred["risk_band"]] += 1

        # Upsert into attrition_scores table
        score_record = db.query(AttritionScore).filter(AttritionScore.employee_id == emp.id).first()
        if not score_record:
            score_record = AttritionScore(
                employee_id=emp.id,
                risk_score=pred["risk_score"],
                risk_band=pred["risk_band"],
                top_factors=json.dumps(pred["top_factors"]),
                computed_at=datetime.utcnow()
            )
            db.add(score_record)
        else:
            score_record.risk_score = pred["risk_score"]
            score_record.risk_band = pred["risk_band"]
            score_record.top_factors = json.dumps(pred["top_factors"])
            score_record.computed_at = datetime.utcnow()

        updated_count += 1

    db.commit()
    return {
        "total_scored": updated_count,
        "risk_distribution": band_counts,
        "computed_at": datetime.utcnow().isoformat()
    }
