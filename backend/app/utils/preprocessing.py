import os
import importlib
import importlib.util
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def probe_system_capabilities() -> Dict[str, Dict[str, Any]]:
    """
    Probes system packages for qiskit, torch, torch_geometric, lightgbm, catboost, shap.
    Returns capability status and version string or UNAVAILABLE error info.
    Guarantees no unhandled exceptions/crashes.
    """
    packages = {
        "qiskit": "qiskit",
        "qiskit_machine_learning": "qiskit_machine_learning",
        "torch": "torch",
        "torch_geometric": "torch_geometric",
        "lightgbm": "lightgbm",
        "catboost": "catboost",
        "shap": "shap",
    }
    
    capabilities = {}
    for key, mod_name in packages.items():
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec is not None:
                mod = importlib.import_module(mod_name)
                version = getattr(mod, "__version__", "installed")
                capabilities[key] = {
                    "status": "AVAILABLE",
                    "version": str(version),
                    "error": None
                }
            else:
                capabilities[key] = {
                    "status": "UNAVAILABLE",
                    "version": None,
                    "error": f"Module {mod_name} not found in environment."
                }
        except Exception as e:
            capabilities[key] = {
                "status": "UNAVAILABLE",
                "version": None,
                "error": str(e)
            }
    return capabilities


class DatasetAdapter:
    """
    Universal dataset adapter that accepts creditcard.csv, synthetic payments CSV, PaySim CSV, etc.
    Auto-detects target, amount, time, and entity columns.
    Extracts feature matrix X and label vector y with zero data leakage.
    Returns capability flags (has_graph, has_geo, has_device) for frontend panel toggling.
    """
    TARGET_CANDIDATES = ["Class", "is_fraud", "isFraud", "fraud", "label", "target"]
    AMOUNT_CANDIDATES = ["Amount", "amount", "transaction_amount"]
    TIME_CANDIDATES = ["Time", "time", "hour", "timestamp"]

    def __init__(self, df: pd.DataFrame):
        self.raw_df = df.copy()
        self.target_col = self._detect_column(self.TARGET_CANDIDATES, required=True)
        self.amount_col = self._detect_column(self.AMOUNT_CANDIDATES, required=False)
        self.time_col = self._detect_column(self.TIME_CANDIDATES, required=False)
        
        # Detect capability flags
        cols = set(df.columns)
        self.has_graph = bool(cols.intersection({"user_id", "account_id", "device_id", "ip", "merchant_id"}))
        self.has_geo = bool(cols.intersection({"lat", "lon", "location_score"}))
        self.has_device = bool(cols.intersection({"device_id", "device_score"}))

    def _detect_column(self, candidates: List[str], required: bool = False) -> Optional[str]:
        for col in candidates:
            if col in self.raw_df.columns:
                return col
        if required:
            raise ValueError(f"Could not auto-detect target column in dataset. Available columns: {list(self.raw_df.columns)}")
        return None

    def get_capability_flags(self) -> Dict[str, bool]:
        return {
            "has_graph": self.has_graph,
            "has_geo": self.has_geo,
            "has_device": self.has_device,
        }

    def prepare_features(self, drop_cols: Optional[List[str]] = None) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Extracts feature columns X and label y.
        Drops ID/string columns like txn_id, user_id, account_id, device_id, ip, merchant_id
        while retaining numerical risk scores and amounts.
        """
        y = self.raw_df[self.target_col].astype(int)
        
        # Ignore string metadata columns for numeric ML modeling
        metadata_cols = {"txn_id", "user_id", "account_id", "device_id", "ip", "merchant_id"}
        if drop_cols:
            metadata_cols.update(drop_cols)
        metadata_cols.add(self.target_col)
        
        feature_cols = [c for c in self.raw_df.columns if c not in metadata_cols]
        X = self.raw_df[feature_cols].copy()
        
        # Handle non-numeric columns if any exist
        X = X.select_dtypes(include=[np.number]).fillna(0.0)
        return X, y

    def get_splits(self, test_size: float = 0.2, val_size: float = 0.1, random_state: int = 42) -> Dict[str, Any]:
        """
        Splits data cleanly into train, val, and test.
        If continuous 'Time' column exists (e.g. creditcard.csv), uses time-ordered split.
        Otherwise, uses stratified random split.
        Strictly zero data leakage: Scaler is fit ONLY on train set.
        """
        X, y = self.prepare_features()
        
        is_time_ordered = (self.time_col == "Time") and ("V1" in X.columns)
        
        if is_time_ordered:
            # Sort by time for time-ordered split
            sort_idx = self.raw_df[self.time_col].argsort()
            X = X.iloc[sort_idx].reset_index(drop=True)
            y = y.iloc[sort_idx].reset_index(drop=True)
            
            n = len(X)
            test_n = int(n * test_size)
            val_n = int(n * val_size)
            train_n = n - test_n - val_n
            
            X_train, y_train = X.iloc[:train_n], y.iloc[:train_n]
            X_val, y_val = X.iloc[train_n:train_n+val_n], y.iloc[train_n:train_n+val_n]
            X_test, y_test = X.iloc[train_n+val_n:], y.iloc[train_n+val_n:]
        else:
            # Stratified split for synthetic or general payment data
            X_temp, X_test, y_temp, y_test = train_test_split(
                X, y, test_size=test_size, stratify=y, random_state=random_state
            )
            val_ratio = val_size / (1.0 - test_size)
            X_train, X_val, y_train, y_val = train_test_split(
                X_temp, y_temp, test_size=val_ratio, stratify=y_temp, random_state=random_state
            )

        # Scaler fit on TRAIN ONLY
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        X_test_scaled = scaler.transform(X_test)
        
        return {
            "X_train": X_train,
            "y_train": y_train,
            "X_val": X_val,
            "y_val": y_val,
            "X_test": X_test,
            "y_test": y_test,
            "X_train_scaled": X_train_scaled,
            "X_val_scaled": X_val_scaled,
            "X_test_scaled": X_test_scaled,
            "scaler": scaler,
            "is_time_ordered": is_time_ordered,
            "feature_names": list(X.columns),
            "capabilities": self.get_capability_flags()
        }
