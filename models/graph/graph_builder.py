import os
import sys
import torch
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import torch_geometric
    from torch_geometric.data import Data
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

def build_transaction_graph(df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """
    Constructs a PyTorch Geometric graph representation from payment transaction records.
    Nodes: Transaction, User, Device, Merchant, IP.
    Edges connect transactions to entities and shared entities across transactions.
    """
    if not HAS_PYG:
        return None, {"status": "PyG missing"}

    num_txns = len(df)
    
    # Map entities to unique integer IDs
    user_map = {uid: idx for idx, uid in enumerate(df["user_id"].unique())}
    device_map = {did: idx for idx, did in enumerate(df["device_id"].unique())}
    merchant_map = {mid: idx for idx, mid in enumerate(df["merchant_id"].unique())}
    ip_map = {ip: idx for idx, ip in enumerate(df["ip"].unique())}

    n_users = len(user_map)
    n_devices = len(device_map)
    n_merchants = len(merchant_map)
    n_ips = len(ip_map)

    total_nodes = num_txns + n_users + n_devices + n_merchants + n_ips

    # Offset indices for homogeneous graph construction
    user_offset = num_txns
    device_offset = user_offset + n_users
    merchant_offset = device_offset + n_devices
    ip_offset = merchant_offset + n_merchants

    src_nodes, dst_nodes = [], []

    for idx, row in df.iterrows():
        t_id = idx
        u_id = user_offset + user_map[row["user_id"]]
        d_id = device_offset + device_map[row["device_id"]]
        m_id = merchant_offset + merchant_map[row["merchant_id"]]
        ip_id = ip_offset + ip_map[row["ip"]]

        # Bidirectional edges (MADE_TRANSACTION, USED_DEVICE, PURCHASED_FROM, USED_IP)
        for entity_id in [u_id, d_id, m_id, ip_id]:
            src_nodes.extend([t_id, entity_id])
            dst_nodes.extend([entity_id, t_id])

    edge_index = torch.tensor([src_nodes, dst_nodes], dtype=torch.long)

    # Node features: 6 numeric features for transactions, zero-padded for entities
    numeric_cols = ["amount", "hour", "velocity_1h", "account_age_days", "device_score", "location_score", "merchant_risk"]
    available_cols = [c for c in numeric_cols if c in df.columns]
    
    x_txn = torch.tensor(df[available_cols].values, dtype=torch.float32)
    feat_dim = x_txn.shape[1]
    
    x_entities = torch.zeros((total_nodes - num_txns, feat_dim), dtype=torch.float32)
    x_all = torch.cat([x_txn, x_entities], dim=0)

    # Label vector (only transaction nodes have labels)
    y_txn = torch.tensor(df["label"].values, dtype=torch.long)
    y_all = torch.full((total_nodes,), -1, dtype=torch.long)
    y_all[:num_txns] = y_txn

    data = Data(x=x_all, edge_index=edge_index, y=y_all)
    data.num_transactions = num_txns
    data.num_classes = 2

    metadata = {
        "num_nodes": total_nodes,
        "num_edges": edge_index.shape[1],
        "num_transactions": num_txns,
        "num_users": n_users,
        "num_devices": n_devices,
        "num_merchants": n_merchants,
        "num_ips": n_ips
    }
    return data, metadata
