import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib

def generate_mock_hr_dataset(n_samples=3500):
    """Generates realistic enterprise HR workforce attrition training data."""
    np.random.seed(42)
    departments = ["Engineering", "Sales", "Product", "Operations"]
    salary_levels = ["Low", "Medium", "High"]
    overtime_opts = ["Yes", "No"]

    dept = np.random.choice(departments, size=n_samples, p=[0.38, 0.32, 0.15, 0.15])
    satisfaction = np.random.uniform(1.0, 5.0, size=n_samples)
    tenure = np.random.uniform(0.5, 12.0, size=n_samples)
    avg_hours = np.random.normal(loc=195, scale=28, size=n_samples).clip(120, 310)
    last_eval = np.random.uniform(1.0, 5.0, size=n_samples)
    salary = np.random.choice(salary_levels, size=n_samples, p=[0.35, 0.45, 0.20])
    overtime = np.random.choice(overtime_opts, size=n_samples, p=[0.35, 0.65])

    # Calibrated risk odds based on organizational behavior studies
    log_odds = (
        -1.2
        - 1.15 * (satisfaction - 3.0)
        + 0.016 * (avg_hours - 180)
        + 0.75 * (overtime == "Yes")
        + 0.55 * (salary == "Low")
        - 0.45 * (salary == "High")
        + 0.25 * ((tenure >= 3.0) & (salary == "Low"))
    )
    prob = 1 / (1 + np.exp(-log_odds))
    attrition = (np.random.rand(n_samples) < prob).astype(int)

    return pd.DataFrame({
        "department": dept,
        "satisfaction": np.round(satisfaction, 2),
        "tenure": np.round(tenure, 1),
        "avg_hours": np.round(avg_hours, 1),
        "last_evaluation": np.round(last_eval, 2),
        "salary_level": salary,
        "overtime": overtime,
        "attrition": attrition
    })

def train_and_export(csv_path=None):
    if csv_path and os.path.exists(csv_path):
        print(f"📦 Ingesting custom training dataset from: {csv_path}")
        df = pd.read_csv(csv_path)
    else:
        print("📦 Synthesizing calibrated enterprise HR dataset (3,500 samples)...")
        df = generate_mock_hr_dataset(3500)
        df.to_csv("training_data_sample.csv", index=False)
        print("💾 Saved reference dataset copy to: training_data_sample.csv")

    target_col = "attrition"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in training dataset.")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    numeric_features = ["satisfaction", "tenure", "avg_hours", "last_evaluation"]
    categorical_features = ["department", "salary_level", "overtime"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ]
    )

    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=180,
            max_depth=8,
            min_samples_split=6,
            random_state=42,
            class_weight="balanced"
        ))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("🚀 Training Random Forest Attrition Classifier Pipeline...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print("\n================ MODEL PERFORMANCE ================")
    print(classification_report(y_test, y_pred, digits=4))
    roc_score = roc_auc_score(y_test, y_proba)
    print(f"ROC-AUC Score: {roc_score:.4f}")
    print("====================================================")

    output_model = "attrition_model.joblib"
    joblib.dump(pipeline, output_model)
    print(f"\n✅ Trained pipeline serialized to: {output_model}")
    print("ℹ️ server.py will automatically load this artifact upon startup.")

if __name__ == "__main__":
    custom_csv = sys.argv[1] if len(sys.argv) > 1 else None
    train_and_export(custom_csv)
