import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import torch_geometric
    from torch_geometric.nn import GATConv
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

class GATFraudNet(nn.Module):
    """
    Graph Attention Network (GAT) using multi-head attention (GATConv)
    to dynamically weight edge importance between users, devices, merchants, and transactions.
    """
    def __init__(self, in_channels: int, hidden_channels: int = 16, heads: int = 4, out_channels: int = 2):
        super().__init__()
        if not HAS_PYG:
            raise ImportError("PyTorch Geometric is required for GATFraudNet.")
        
        self.conv1 = GATConv(in_channels, hidden_channels, heads=heads, dropout=0.1)
        self.conv2 = GATConv(hidden_channels * heads, out_channels, heads=1, concat=False, dropout=0.1)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = F.elu(x)
        x = self.conv2(x, edge_index)
        return F.softmax(x, dim=1)
