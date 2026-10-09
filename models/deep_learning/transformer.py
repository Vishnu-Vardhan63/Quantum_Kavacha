import os
import sys
import torch
import torch.nn as nn
import numpy as np

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class TabularTransformerFraudNet(nn.Module):
    """
    Tabular Transformer Neural Network with Multi-Head Self-Attention layers
    for capturing high-order non-linear feature interactions across payment attributes.
    """
    def __init__(self, input_dim: int, d_model: int = 32, nhead: int = 4, num_layers: int = 2):
        super().__init__()
        self.input_projection = nn.Linear(1, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=64,
            dropout=0.1,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.classifier = nn.Sequential(
            nn.Linear(input_dim * d_model, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Reshape input (batch_size, input_dim) -> (batch_size, input_dim, 1)
        x_seq = x.unsqueeze(-1)
        x_proj = self.input_projection(x_seq)
        
        # Transformer Self-Attention
        attn_out = self.transformer_encoder(x_proj)
        
        # Flatten and classify
        flat = attn_out.reshape(attn_out.size(0), -1)
        prob = self.classifier(flat)
        return prob
