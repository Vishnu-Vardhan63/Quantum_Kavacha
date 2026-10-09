import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import json
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import pandas as pd
from typing import Dict, Any

from backend.app.utils.preprocessing import DatasetAdapter
from backend.app.utils.metrics import compute_eval_metrics, save_metrics_json
from models.deep_learning.autoencoder import TabularAutoencoder, DenseFraudNN
from models.deep_learning.vae import TabularVAE
from models.deep_learning.transformer import TabularTransformerFraudNet

def train_and_eval_deep_models(data_path: str = None) -> Dict[str, Any]:
    if data_path is None:
        data_path = os.path.join(project_root, "data", "sample", "demo_transactions.csv")
        
    df = pd.read_csv(data_path)
    adapter = DatasetAdapter(df)
    splits = adapter.get_splits(test_size=0.2, val_size=0.1, random_state=42)
    
    X_train_scaled = splits["X_train_scaled"]
    y_train = splits["y_train"].values
    X_test_scaled = splits["X_test_scaled"]
    y_test = splits["y_test"].values
    input_dim = X_train_scaled.shape[1]

    artifacts_dir = os.path.join(project_root, "model_artifacts", "deep_learning")
    os.makedirs(artifacts_dir, exist_ok=True)

    # 1. Train Autoencoder on LEGITIMATE DATA ONLY
    X_legit_train = X_train_scaled[y_train == 0]
    ae_dataset = TensorDataset(torch.tensor(X_legit_train, dtype=torch.float32))
    ae_loader = DataLoader(ae_dataset, batch_size=32, shuffle=True)
    
    autoencoder = TabularAutoencoder(input_dim=input_dim)
    optimizer = torch.optim.Adam(autoencoder.parameters(), lr=0.005)
    criterion = nn.MSELoss()
    
    autoencoder.train()
    for epoch in range(40):
        for (batch_x,) in ae_loader:
            optimizer.zero_grad()
            recon = autoencoder(batch_x)
            loss = criterion(recon, batch_x)
            loss.backward()
            optimizer.step()

    X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)
    t0 = time.time()
    test_mse = autoencoder.compute_reconstruction_error(X_test_tensor)
    ae_infer_time = (time.time() - t0) / len(X_test_scaled) * 1000.0
    
    max_threshold = np.percentile(test_mse, 99) if len(test_mse) > 0 else 1.0
    ae_anomaly_scores = np.clip(test_mse / max(1e-5, max_threshold), 0.0, 1.0)
    ae_metrics = compute_eval_metrics(y_test, ae_anomaly_scores, ae_infer_time)
    torch.save(autoencoder.state_dict(), os.path.join(artifacts_dir, "autoencoder.pt"))

    # 2. Train Variational Autoencoder (VAE) on LEGITIMATE DATA ONLY
    vae = TabularVAE(input_dim=input_dim)
    opt_vae = torch.optim.Adam(vae.parameters(), lr=0.005)
    
    vae.train()
    for epoch in range(40):
        for (batch_x,) in ae_loader:
            opt_vae.zero_grad()
            recon_x, mu, logvar = vae(batch_x)
            loss = vae.loss_function(recon_x, batch_x, mu, logvar)
            loss.backward()
            opt_vae.step()

    t0 = time.time()
    vae_anomaly_err = vae.compute_anomaly_score(X_test_tensor)
    vae_infer_time = (time.time() - t0) / len(X_test_scaled) * 1000.0
    vae_threshold = np.percentile(vae_anomaly_err, 99) if len(vae_anomaly_err) > 0 else 1.0
    vae_anomaly_scores = np.clip(vae_anomaly_err / max(1e-5, vae_threshold), 0.0, 1.0)
    vae_metrics = compute_eval_metrics(y_test, vae_anomaly_scores, vae_infer_time)
    torch.save(vae.state_dict(), os.path.join(artifacts_dir, "vae.pt"))

    # 3. Train Dense NN
    train_dataset = TensorDataset(
        torch.tensor(X_train_scaled, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    )
    dense_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    dense_nn = DenseFraudNN(input_dim=input_dim)
    opt_dense = torch.optim.Adam(dense_nn.parameters(), lr=0.005)
    crit_dense = nn.BCELoss()
    
    dense_nn.train()
    for epoch in range(30):
        for bx, by in dense_loader:
            opt_dense.zero_grad()
            out = dense_nn(bx)
            loss = crit_dense(out, by)
            loss.backward()
            opt_dense.step()

    t0 = time.time()
    with torch.no_grad():
        dense_probs = dense_nn(X_test_tensor).numpy().flatten()
    dense_infer_time = (time.time() - t0) / len(X_test_scaled) * 1000.0
    dense_metrics = compute_eval_metrics(y_test, dense_probs, dense_infer_time)
    torch.save(dense_nn.state_dict(), os.path.join(artifacts_dir, "dense_nn.pt"))

    # 4. Train Tabular Transformer
    transformer_net = TabularTransformerFraudNet(input_dim=input_dim)
    opt_trans = torch.optim.Adam(transformer_net.parameters(), lr=0.003)
    
    transformer_net.train()
    for epoch in range(30):
        for bx, by in dense_loader:
            opt_trans.zero_grad()
            out = transformer_net(bx)
            loss = crit_dense(out, by)
            loss.backward()
            opt_trans.step()

    transformer_net.eval()
    t0 = time.time()
    with torch.no_grad():
        trans_probs = transformer_net(X_test_tensor).numpy().flatten()
    trans_infer_time = (time.time() - t0) / len(X_test_scaled) * 1000.0
    trans_metrics = compute_eval_metrics(y_test, trans_probs, trans_infer_time)
    torch.save(transformer_net.state_dict(), os.path.join(artifacts_dir, "transformer.pt"))

    deep_results = {
        "Autoencoder (Anomaly)": ae_metrics,
        "Variational Autoencoder (VAE)": vae_metrics,
        "Dense NN": dense_metrics,
        "Tabular Transformer": trans_metrics
    }
    
    save_metrics_json(deep_results, os.path.join(artifacts_dir, "metrics.json"))
    print(f"Advanced Deep Learning models (AE, VAE, Dense, TabTransformer) trained successfully!")
    return deep_results

if __name__ == "__main__":
    train_and_eval_deep_models()
