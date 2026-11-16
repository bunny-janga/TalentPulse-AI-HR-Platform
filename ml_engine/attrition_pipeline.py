"""
Attrition risk model training and inference for TalentPulse AI.
Licensed under the MIT License.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "attrition_rf_model.joblib")
DATASET_PATH = os.path.join(BASE_DIR, "workforce_records_1200.csv")

DEPARTMENTS = [
    "Cloud Engineering",
    "QA Automation",
    "Data & AI",
    "Full-Stack Delivery",
    "DevOps & SRE",
    "HR & Operations",
]
ROLES = [
    "Junior Engineer",
    "Software Engineer",
    "Senior Engineer",
    "Tech Lead",
    "Delivery Manager",
]
FEATURE_COLS = [
    "tenure_months",
    "monthly_hours",
    "last_hike_months",
    "engagement_score",
    "perf_rating",
    "commute_km",
    "wfh_days",
    "promotions_3yr",
]


def build_synthetic_workforce(n_samples: int = 1200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    first_names = [
        "Aarav", "Ananya", "Rohan", "Divya", "Karthik", "Sneha",
        "Vikram", "Priya", "Siddharth", "Meera", "Nikhil", "Kavya",
    ]
    last_names = [
        "Rao", "Varma", "Reddy", "Nair", "Kulkarni",
        "Menon", "Sharma", "Iyer", "Naidu", "Murthy",
    ]

    rows = []
    for idx in range(1, n_samples + 1):
        full_name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
        dept = rng.choice(DEPARTMENTS, p=[0.26, 0.18, 0.20, 0.20, 0.10, 0.06])
        role = rng.choice(ROLES, p=[0.25, 0.35, 0.22, 0.12, 0.06])

        tenure_months = int(rng.integers(2, 72))
        monthly_hours = float(np.clip(rng.normal(178, 22), 140, 245))
        last_hike_months = int(rng.integers(1, 30))
        engagement_score = float(np.clip(rng.normal(3.6, 0.85), 1.0, 5.0))
        perf_rating = float(np.clip(rng.normal(3.8, 0.65), 2.0, 5.0))
        commute_km = float(np.clip(rng.normal(14, 7), 1.0, 42.0))
        wfh_days = int(rng.choice([0, 1, 2, 3], p=[0.15, 0.25, 0.45, 0.15]))
        promotions_3yr = int(rng.choice([0, 1, 2], p=[0.65, 0.28, 0.07]))

        logit = (
            -2.4
            + 0.038 * (monthly_hours - 175)
            + 0.065 * (last_hike_months - 12)
            - 0.85 * (engagement_score - 3.2)
            + 0.032 * (commute_km - 12)
            - 0.28 * wfh_days
            - 0.55 * promotions_3yr
        )
        attrition_prob = 1 / (1 + np.exp(-logit))

        rows.append({
            "emp_code": f"TPZ-{1000 + idx}",
            "full_name": full_name,
            "department": dept,
            "job_role": role,
            "tenure_months": tenure_months,
            "monthly_hours": round(monthly_hours, 1),
            "last_hike_months": last_hike_months,
            "engagement_score": round(engagement_score, 2),
            "perf_rating": round(perf_rating, 2),
            "commute_km": round(commute_km, 1),
            "wfh_days": wfh_days,
            "promotions_3yr": promotions_3yr,
            "attrition": int(rng.random() < attrition_prob),
        })

    df = pd.DataFrame(rows)
    df.to_csv(DATASET_PATH, index=False)
    return df


def train_and_save_model() -> dict:
    df = build_synthetic_workforce(1200)
    X_train, X_test, y_train, y_test = train_test_split(
        df[FEATURE_COLS],
        df["attrition"],
        test_size=0.2,
        random_state=42,
        stratify=df["attrition"],
    )

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    artifact = {
        "model": model,
        "features": FEATURE_COLS,
        "roc_auc": round(float(auc), 4),
    }
    joblib.dump(artifact, MODEL_PATH)
    return artifact


def predict_employee_risk(features: dict) -> dict:
    if not os.path.exists(MODEL_PATH):
        train_and_save_model()

    artifact = joblib.load(MODEL_PATH)
    sample = pd.DataFrame([{col: features.get(col, 0) for col in FEATURE_COLS}])
    prob = float(artifact["model"].predict_proba(sample)[0][1])

    if prob >= 0.72:
        tier = "CRITICAL"
    elif prob >= 0.45:
        tier = "ELEVATED"
    else:
        tier = "STABLE"

    return {
        "risk_probability": round(prob * 100, 1),
        "risk_tier": tier,
        "model_auc": artifact["roc_auc"],
    }


if __name__ == "__main__":
    result = train_and_save_model()
    print(f"Model trained successfully | Validation ROC-AUC: {result['roc_auc']}")
