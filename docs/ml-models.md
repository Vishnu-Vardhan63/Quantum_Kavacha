# Machine Learning Models Specification

## Classical Baseline Models
- **Logistic Regression**: Baseline linear classifier with balanced class weights.
- **Random Forest**: Ensemble of 100 decision trees.
- **XGBoost & LightGBM & CatBoost**: Gradient boosted trees tuned with positive scale weights to handle class imbalance.

## Deep Learning Models
- **Tabular Autoencoder**: PyTorch neural network trained strictly on legitimate payments ($y=0$). Reconstruction MSE mapped to $[0, 1]$ anomaly score.
- **Dense NN**: Supervised PyTorch classifier with dropout layers.

## Graph Intelligence (PyTorch Geometric)
- **GraphSAGE**: 2-layer Graph Neural Network sampling local 1-hop and 2-hop neighborhoods of transaction nodes and shared entity nodes (User, Device, Merchant, IP).

## Stacking Hybrid Ensemble
- Logistic regression meta-learner with Isotonic probability calibration combining out-of-fold predictions.
- **Risk Thresholds**:
  - `NORMAL`: Risk Score < 40
  - `SUSPICIOUS`: Risk Score 40 - 69
  - `HIGH RISK`: Risk Score >= 70
