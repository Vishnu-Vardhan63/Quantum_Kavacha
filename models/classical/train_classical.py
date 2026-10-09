import os
import sys

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Attempt imports for gradient boosted models & SHAP
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import catboost as cb
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

from backend.app.utils.preprocessing import DatasetAdapter
from backend.app.utils.metrics import compute_eval_metrics, save_metrics_json

def train_and_eval_classical_models(data_path: str = None) -> Dict[str, Any]:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if data_path is None:
        data_path = os.path.join(project_root, "data", "sample", "demo_transactions.csv")
        
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data path {data_path} does not exist. Run scripts/generate_demo_data.py first.")

    df = pd.read_csv(data_path)
    adapter = DatasetAdapter(df)
    splits = adapter.get_splits(test_size=0.2, val_size=0.1, random_state=42)
    
    X_train, y_train = splits["X_train_scaled"], splits["y_train"]
    X_val, y_val = splits["X_val_scaled"], splits["y_val"]
    X_test, y_test = splits["X_test_scaled"], splits["y_test"]
    feature_names = splits["feature_names"]

    artifacts_dir = os.path.join(project_root, "model_artifacts", "classical")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Save scaler
    joblib.dump(splits["scaler"], os.path.join(artifacts_dir, "scaler.joblib"))
    
    all_metrics = {}
    
    # 1. Logistic Regression
    lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    t0 = time.time()
    lr_probs = lr.predict_proba(X_test)[:, 1]
    inference_time = (time.time() - t0) / len(X_test) * 1000.0
    all_metrics["Logistic Regression"] = compute_eval_metrics(y_test, lr_probs, inference_time)
    joblib.dump(lr, os.path.join(artifacts_dir, "logistic_regression.joblib"))

    # 2. Random Forest
    rf = RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42)
    rf.fit(X_train, y_train)
    t0 = time.time()
    rf_probs = rf.predict_proba(X_test)[:, 1]
    inference_time = (time.time() - t0) / len(X_test) * 1000.0
    all_metrics["Random Forest"] = compute_eval_metrics(y_test, rf_probs, inference_time)
    joblib.dump(rf, os.path.join(artifacts_dir, "random_forest.joblib"))

    # 3. XGBoost
    if HAS_XGBOOST:
        scale_pos = (len(y_train) - sum(y_train)) / max(1, sum(y_train))
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            scale_pos_weight=scale_pos,
            random_state=42,
            eval_metric="logloss"
        )
        xgb_model.fit(X_train, y_train)
        t0 = time.time()
        xgb_probs = xgb_model.predict_proba(X_test)[:, 1]
        inference_time = (time.time() - t0) / len(X_test) * 1000.0
        all_metrics["XGBoost"] = compute_eval_metrics(y_test, xgb_probs, inference_time)
        joblib.dump(xgb_model, os.path.join(artifacts_dir, "xgboost.joblib"))

    # 4. LightGBM
    if HAS_LIGHTGBM:
        lgb_model = lgb.LGBMClassifier(
            n_estimators=100,
            is_unbalance=True,
            random_state=42,
            verbose=-1
        )
        lgb_model.fit(X_train, y_train)
        t0 = time.time()
        lgb_probs = lgb_model.predict_proba(X_test)[:, 1]
        inference_time = (time.time() - t0) / len(X_test) * 1000.0
        all_metrics["LightGBM"] = compute_eval_metrics(y_test, lgb_probs, inference_time)
        joblib.dump(lgb_model, os.path.join(artifacts_dir, "lightgbm.joblib"))

    # 5. CatBoost
    if HAS_CATBOOST:
        cb_model = cb.CatBoostClassifier(
            iterations=100,
            auto_class_weights="Balanced",
            random_seed=42,
            verbose=0
        )
        cb_model.fit(X_train, y_train)
        t0 = time.time()
        cb_probs = cb_model.predict_proba(X_test)[:, 1]
        inference_time = (time.time() - t0) / len(X_test) * 1000.0
        all_metrics["CatBoost"] = compute_eval_metrics(y_test, cb_probs, inference_time)
        joblib.dump(cb_model, os.path.join(artifacts_dir, "catboost.joblib"))

    # SHAP Explainer (fit on Random Forest or XGBoost)
    if HAS_SHAP:
        try:
            target_explainer_model = rf
            explainer = shap.TreeExplainer(target_explainer_model)
            joblib.dump(explainer, os.path.join(artifacts_dir, "shap_explainer.joblib"))
        except Exception as e:
            print(f"Warning: SHAP explainer creation failed: {e}")

    # Save metrics JSON
    metrics_path = os.path.join(artifacts_dir, "metrics.json")
    save_metrics_json(all_metrics, metrics_path)
    print(f"Classical models trained successfully. Metrics saved to {metrics_path}")
    return all_metrics

if __name__ == "__main__":
    train_and_eval_classical_models()
