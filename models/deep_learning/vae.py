import os
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class TabularVAE(nn.Module):
    """
    Variational Autoencoder (VAE) for Deep Generative Fraud Anomaly Detection.
    Trained strictly on legitimate transactions (y=0) ONLY.
    Uses Reparameterization Trick z = mu + std * eps and computes KL Divergence + MSE.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 16, latent_dim: int = 4):
        super().__init__()
        self.fc_enc = nn.Linear(input_dim, hidden_dim)
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
        
        self.fc_dec1 = nn.Linear(latent_dim, hidden_dim)
        self.fc_dec2 = nn.Linear(hidden_dim, input_dim)

    def encode(self, x: torch.Tensor):
        h = F.relu(self.fc_enc(x))
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor):
        h = F.relu(self.fc_dec1(z))
        return self.fc_dec2(h)

    def forward(self, x: torch.Tensor):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon_x = self.decode(z)
        return recon_x, mu, logvar

    def loss_function(self, recon_x, x, mu, logvar, beta: float = 0.1):
        recon_loss = F.mse_loss(recon_x, x, reduction='sum')
        kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        return recon_loss + beta * kl_loss

    def compute_anomaly_score(self, x: torch.Tensor) -> np.ndarray:
        self.eval()
        with torch.no_grad():
            recon_x, mu, logvar = self.forward(x)
            mse = torch.mean((x - recon_x) ** 2, dim=1)
            kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=1)
            total_error = (mse + 0.05 * kl).cpu().numpy()
        return total_error
