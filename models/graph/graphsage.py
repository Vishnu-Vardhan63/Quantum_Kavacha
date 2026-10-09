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
    from torch_geometric.nn import SAGEConv
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

class GraphSAGEFraudNet(nn.Module):
    """
    2-layer GraphSAGE architecture for transaction risk propagation and entity aggregation.
    """
    def __init__(self, in_channels: int, hidden_channels: int = 32, out_channels: int = 2):
        super().__init__()
        if not HAS_PYG:
            raise ImportError("PyTorch Geometric is required for GraphSAGEFraudNet.")
        self.conv1 = SAGEConv(in_channels, hidden_channels)
        self.conv2 = SAGEConv(hidden_channels, out_channels)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.conv2(x, edge_index)
        return F.softmax(x, dim=1)
