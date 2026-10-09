import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import json
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, Any

from backend.app.utils.metrics import compute_eval_metrics, save_metrics_json
from models.graph.graph_builder import build_transaction_graph, HAS_PYG
if HAS_PYG:
    from models.graph.graphsage import GraphSAGEFraudNet
    from models.graph.gat import GATFraudNet

def train_and_eval_gnn_model(data_path: str = None) -> Dict[str, Any]:
    artifacts_dir = os.path.join(project_root, "model_artifacts", "graph")
    os.makedirs(artifacts_dir, exist_ok=True)
    metrics_path = os.path.join(artifacts_dir, "metrics.json")

    if not HAS_PYG:
        unavail = {"GNN (GraphSAGE)": {"status": "UNAVAILABLE"}}
        save_metrics_json(unavail, metrics_path)
        return unavail

    if data_path is None:
        data_path = os.path.join(project_root, "data", "sample", "demo_transactions.csv")

    df = pd.read_csv(data_path)
    graph_data, metadata = build_transaction_graph(df)
    
    num_txns = graph_data.num_transactions
    num_train = int(num_txns * 0.7)
    
    train_mask = torch.zeros(graph_data.num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(graph_data.num_nodes, dtype=torch.bool)
    train_mask[:num_train] = True
    test_mask[num_train:num_txns] = True

    # 1. GraphSAGE
    model_sage = GraphSAGEFraudNet(in_channels=graph_data.x.shape[1], hidden_channels=32, out_channels=2)
    opt_sage = torch.optim.Adam(model_sage.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    model_sage.train()
    for epoch in range(50):
        opt_sage.zero_grad()
        out = model_sage(graph_data.x, graph_data.edge_index)
        loss = criterion(out[train_mask], graph_data.y[train_mask])
        loss.backward()
        opt_sage.step()

    model_sage.eval()
    t0 = time.time()
    with torch.no_grad():
        sage_probs = model_sage(graph_data.x, graph_data.edge_index)[test_mask][:, 1].cpu().numpy()
        
    y_test = graph_data.y[test_mask].cpu().numpy()
    sage_infer_time = (time.time() - t0) / max(1, len(y_test)) * 1000.0
    sage_metrics = compute_eval_metrics(y_test, sage_probs, sage_infer_time)
    torch.save(model_sage.state_dict(), os.path.join(artifacts_dir, "graphsage.pt"))

    # 2. Graph Attention Network (GAT)
    model_gat = GATFraudNet(in_channels=graph_data.x.shape[1], hidden_channels=16, heads=4, out_channels=2)
    opt_gat = torch.optim.Adam(model_gat.parameters(), lr=0.008)

    model_gat.train()
    for epoch in range(50):
        opt_gat.zero_grad()
        out = model_gat(graph_data.x, graph_data.edge_index)
        loss = criterion(out[train_mask], graph_data.y[train_mask])
        loss.backward()
        opt_gat.step()

    model_gat.eval()
    t0 = time.time()
    with torch.no_grad():
        gat_probs = model_gat(graph_data.x, graph_data.edge_index)[test_mask][:, 1].cpu().numpy()
        
    gat_infer_time = (time.time() - t0) / max(1, len(y_test)) * 1000.0
    gat_metrics = compute_eval_metrics(y_test, gat_probs, gat_infer_time)
    torch.save(model_gat.state_dict(), os.path.join(artifacts_dir, "gat.pt"))

    results = {
        "GNN (GraphSAGE)": sage_metrics,
        "GNN (Graph Attention Network - GAT)": gat_metrics
    }
    
    save_metrics_json(results, metrics_path)
    with open(os.path.join(artifacts_dir, "graph_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"GNN GraphSAGE & GAT models trained successfully. Saved to {artifacts_dir}")
    return results

if __name__ == "__main__":
    train_and_eval_gnn_model()
