import os
import sys
import torch
import torch.nn as nn
import numpy as np

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class TabularAutoencoder(nn.Module):
    """
    Tabular Autoencoder trained strictly on legitimate transactions (y=0) ONLY.
    Reconstruction error (MSE) is mapped into [0, 1] anomaly score.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 16, latent_dim: int = 4):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed

    def compute_reconstruction_error(self, x: torch.Tensor) -> np.ndarray:
        self.eval()
        with torch.no_grad():
            recon = self.forward(x)
            mse = torch.mean((x - recon) ** 2, dim=1).cpu().numpy()
        return mse

class DenseFraudNN(nn.Module):
    """
    Supervised Dense Neural Network for fraud classification.
    """
    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
