import os
import json
import warnings
import numpy as np
import pandas as pd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.svm import OneClassSVM
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings("ignore")

app = FastAPI(title="Q-FraudShield API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE = {
    "scaler": None,
    "pca": None,
    "ocsvm": None,
    "rf": None,
    "qkernel": None,
    "q_train": None,
    "q_mean": None,
    "q_std": None,
    "feature_names": None,
    "metrics": {},
    "trained": False,
    "quantum_available": False,
}

class Transaction(BaseModel):
    amount: float
    time: float
    frequency: float
    location_score: float
    device_score: float
    velocity: float
    merchant_risk: float
    account_age_days: float = 365.0

def demo_dataset(n=700, seed=42):
    rng = np.random.default_rng(seed)
    fraud_n = max(35, n // 15)
    normal_n = n - fraud_n

    normal = np.column_stack([
        rng.lognormal(6.0, 0.65, normal_n),
        rng.uniform(0, 24, normal_n),
        rng.poisson(2.2, normal_n),
        rng.normal(0.15, 0.08, normal_n).clip(0, 1),
        rng.normal(0.15, 0.08, normal_n).clip(0, 1),
        rng.gamma(2.0, 1.0, normal_n),
        rng.normal(0.18, 0.10, normal_n).clip(0, 1),
        rng.integers(30, 2500, normal_n)
    ])
    fraud = np.column_stack([
        rng.lognormal(8.3, 0.8, fraud_n),
        rng.uniform(0, 24, fraud_n),
        rng.poisson(9, fraud_n) + 2,
        rng.normal(0.75, 0.18, fraud_n).clip(0, 1),
        rng.normal(0.78, 0.16, fraud_n).clip(0, 1),
        rng.gamma(5.0, 1.5, fraud_n) + 3,
        rng.normal(0.78, 0.16, fraud_n).clip(0, 1),
        rng.integers(1, 300, fraud_n)
    ])
    X = np.vstack([normal, fraud])
    y = np.r_[np.zeros(normal_n), np.ones(fraud_n)]
    idx = rng.permutation(len(y))
    cols = ["amount","time","frequency","location_score","device_score",
            "velocity","merchant_risk","account_age_days"]
    return pd.DataFrame(X[idx], columns=cols), y[idx].astype(int)

def load_data():
    path = os.path.join(os.path.dirname(__file__), "data", "creditcard.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        if "Class" not in df.columns:
            raise ValueError("CSV found, but it does not contain a 'Class' column.")
        y = df["Class"].astype(int).values
        X = df.drop(columns=["Class"]).select_dtypes(include=[np.number])
        # Remove common ID-like columns and keep a manageable feature set.
        X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
        # Use variance to select informative numeric columns, capped for the demo.
        variances = X.var().sort_values(ascending=False)
        cols = list(variances.head(min(12, len(variances))).index)
        X = X[cols]
        # Cap sample size for a fast hackathon demo.
        if len(X) > 2500:
            rng = np.random.default_rng(7)
            normal_idx = np.where(y == 0)[0]
            fraud_idx = np.where(y == 1)[0]
            keep_normal = rng.choice(normal_idx, size=min(2200, len(normal_idx)), replace=False)
            keep = np.r_[keep_normal, fraud_idx[:min(300, len(fraud_idx))]]
            X, y = X.iloc[keep], y[keep]
        return X.reset_index(drop=True), y
    return demo_dataset()

def quantum_kernel(X1, X2):
    from qiskit.circuit.library import ZZFeatureMap
    from qiskit_machine_learning.kernels import FidelityQuantumKernel
    feature_map = ZZFeatureMap(feature_dimension=X1.shape[1], reps=2, entanglement="linear")
    kernel = FidelityQuantumKernel(feature_map=feature_map)
    return kernel.evaluate(x_vec=X1, y_vec=X2)

def train_models():
    X, y = load_data()
    X = X.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).fillna(0)
    if len(X.columns) > 8:
        X = X.iloc[:, :8]

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    pca = PCA(n_components=min(4, Xs.shape[1]))
    Xp = pca.fit_transform(Xs)

    # OCSVM learns the normal transaction boundary.
    normal = Xp[y == 0]
    ocsvm = OneClassSVM(kernel="rbf", gamma="scale", nu=0.05)
    ocsvm.fit(normal)

    # Classical baseline.
    Xtr, Xte, ytr, yte = train_test_split(
        Xp, y, test_size=0.25, stratify=y, random_state=42
    )
    rf = RandomForestClassifier(
        n_estimators=180, random_state=42, class_weight="balanced", n_jobs=-1
    )
    rf.fit(Xtr, ytr)
    pred = rf.predict(Xte)
    prob = rf.predict_proba(Xte)[:, 1]

    metrics = {
        "classical_accuracy": round(float(accuracy_score(yte, pred)), 4),
        "classical_precision": round(float(precision_score(yte, pred, zero_division=0)), 4),
        "classical_recall": round(float(recall_score(yte, pred, zero_division=0)), 4),
        "classical_f1": round(float(f1_score(yte, pred, zero_division=0)), 4),
        "classical_auc": round(float(roc_auc_score(yte, prob)), 4),
        "samples": int(len(X)),
        "features_before_pca": int(X.shape[1]),
        "quantum_features": int(Xp.shape[1]),
    }

    q_available = False
    qkernel = None
    q_train = None
    q_mean = q_std = None

    try:
        # Quantum simulation is intentionally limited to a compact subset.
        rng = np.random.default_rng(42)
        normal_idx = np.where(y == 0)[0]
        fraud_idx = np.where(y == 1)[0]
        n0 = min(80, len(normal_idx))
        n1 = min(30, len(fraud_idx))
        qi = np.r_[rng.choice(normal_idx, n0, replace=False),
                   rng.choice(fraud_idx, n1, replace=False)]
        qX = Xp[qi]
        qy = y[qi]
        # Fidelity kernel.
        from qiskit.circuit.library import ZZFeatureMap
        from qiskit_machine_learning.kernels import FidelityQuantumKernel
        feature_map = ZZFeatureMap(feature_dimension=qX.shape[1], reps=2, entanglement="linear")
        qkernel = FidelityQuantumKernel(feature_map=feature_map)
        K = qkernel.evaluate(x_vec=qX)
        # Normal similarity profile: fraud tends to deviate from normal kernel similarity.
        normal_rows = np.where(qy == 0)[0]
        normal_profile = K[:, normal_rows].mean(axis=1)
        q_mean = float(normal_profile[qy == 0].mean())
        q_std = float(normal_profile[qy == 0].std() + 1e-6)
        q_train = qX
        q_available = True

        qscore = (q_mean - normal_profile) / q_std
        qpred = (qscore > 2.0).astype(int)
        if len(np.unique(qpred)) > 1 and len(np.unique(qy)) > 1:
            metrics.update({
                "quantum_precision": round(float(precision_score(qy, qpred, zero_division=0)), 4),
                "quantum_recall": round(float(recall_score(qy, qpred, zero_division=0)), 4),
                "quantum_f1": round(float(f1_score(qy, qpred, zero_division=0)), 4),
            })
        else:
            metrics.update({"quantum_precision": 0.0, "quantum_recall": 0.0, "quantum_f1": 0.0})
    except Exception as exc:
        metrics["quantum_error"] = str(exc)[:240]

    STATE.update({
        "scaler": scaler, "pca": pca, "ocsvm": ocsvm, "rf": rf,
        "qkernel": qkernel, "q_train": q_train,
        "q_mean": q_mean, "q_std": q_std,
        "feature_names": list(X.columns),
        "metrics": metrics, "trained": True,
        "quantum_available": q_available
    })
    return metrics

def ensure_trained():
    if not STATE["trained"]:
        train_models()

@app.get("/")
def root():
    return {"name": "Q-FraudShield", "status": "online"}

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "trained": STATE["trained"],
        "quantum_available": STATE["quantum_available"]
    }

@app.post("/api/train")
def train():
    return {"status": "trained", "metrics": train_models()}

@app.get("/api/metrics")
def metrics():
    ensure_trained()
    return STATE["metrics"]

@app.post("/api/predict")
def predict(tx: Transaction):
    ensure_trained()
    values = np.array([[
        tx.amount, tx.time, tx.frequency, tx.location_score,
        tx.device_score, tx.velocity, tx.merchant_risk, tx.account_age_days
    ]], dtype=float)

    # Map the demo input to the model's expected feature count.
    n = len(STATE["feature_names"])
    if values.shape[1] != n:
        values = values[:, :n] if n < values.shape[1] else np.pad(
            values, ((0,0),(0,n-values.shape[1])), constant_values=0
        )

    xp = STATE["pca"].transform(STATE["scaler"].transform(values))
    classical_prob = float(STATE["rf"].predict_proba(xp)[0, 1])
    oc = float(STATE["ocsvm"].decision_function(xp)[0])
    anomaly = float(np.clip(0.5 - oc / 2.0, 0, 1))

    quantum_score = None
    if STATE["quantum_available"]:
        try:
            K = STATE["qkernel"].evaluate(x_vec=xp, y_vec=STATE["q_train"])
            similarity = float(np.mean(K))
            quantum_score = float(np.clip((STATE["q_mean"] - similarity) /
                                          (3 * STATE["q_std"]) + 0.5, 0, 1))
        except Exception:
            quantum_score = None

    final = float(np.clip(
        0.45 * classical_prob + 0.35 * anomaly +
        0.20 * (quantum_score if quantum_score is not None else anomaly), 0, 1
    ))
    level = "HIGH" if final >= 0.70 else ("SUSPICIOUS" if final >= 0.40 else "NORMAL")

    factors = []
    if tx.amount > 50000: factors.append("Unusual transaction amount")
    if tx.frequency > 7: factors.append("High transaction frequency")
    if tx.location_score > 0.65: factors.append("Location deviation")
    if tx.device_score > 0.65: factors.append("New/untrusted device")
    if tx.velocity > 7: factors.append("High transaction velocity")
    if tx.merchant_risk > 0.65: factors.append("High-risk merchant pattern")
    if not factors: factors.append("No major behavioral anomaly detected")

    return {
        "risk_score": round(final * 100, 2),
        "risk_level": level,
        "classical_probability": round(classical_prob * 100, 2),
        "anomaly_score": round(anomaly * 100, 2),
        "quantum_score": None if quantum_score is None else round(quantum_score * 100, 2),
        "factors": factors,
        "decision": "POTENTIAL FRAUD" if level == "HIGH" else (
            "REVIEW TRANSACTION" if level == "SUSPICIOUS" else "NORMAL TRANSACTION"
        )
    }
