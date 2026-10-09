# System Architecture — Q-FraudShield

## System Overview
Q-FraudShield combines Classical Machine Learning, Deep Autoencoders, Graph Intelligence, and Qiskit 2.x Quantum Kernel Feature Representations to provide real-time payment fraud detection.

```mermaid
flowchart TD
    A[Incoming Payment Request] --> B[Dataset Adapter & Capability Prober]
    B --> C[Stage 1: Preprocessing & Scaling]
    C --> D1[Stage 2: Classical Models XGBoost/RF/CatBoost]
    C --> D2[Stage 2: Deep Autoencoder Anomaly Score]
    C --> D3[Stage 2: GraphSAGE GNN Entity Aggregation]
    C --> E[Stage 3: PCA to 4-Qubits & Qiskit zz_feature_map]
    E --> F[FidelityStatevectorKernel Evaluation]
    F --> G1[Supervised QSVC Head]
    F --> G2[Unsupervised Quantum OneClassSVM Head]
    D1 & D2 & D3 & G1 & G2 --> H[Stage 4: Calibrated Stacking Ensemble]
    H --> I[Decision Engine: APPROVE / MONITOR / BLOCK]
    I --> J[Stage 5: SHAP & Quantum Similarity Risk Explanations]
```

## Core Modules
1. **Dataset Adapter**: Auto-detects schema targets (`label`/`Class`/`is_fraud`), handles time-ordered & stratified splits with zero data leakage.
2. **Classical Models**: XGBoost, LightGBM, CatBoost, Random Forest, Logistic Regression.
3. **Deep Learning**: PyTorch Tabular Autoencoder trained strictly on legitimate transactions ($y=0$) for anomaly detection.
4. **Graph Intelligence**: 2-layer GraphSAGE aggregating entity relationships (User, Device, Merchant, IP).
5. **Quantum Engine**: Pluggable `zz_feature_map` (Qiskit 2.x API), `FidelityStatevectorKernel`, QSVC, and OneClassSVM.
6. **Stacking Ensemble**: Logistic regression meta-learner with Isotonic probability calibration and risk thresholding.
