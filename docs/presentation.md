# Qiskit Fall Fest 2026 Presentation Outline

## Slide 1: Title & Problem Statement
- **Title**: Q-FraudShield — Quantum-Enhanced Digital Payment Fraud Intelligence
- **Problem**: Detecting sophisticated fraud patterns in high-velocity digital payment networks.

## Slide 2: Hybrid System Architecture
- Classical Gradient Boosting (XGBoost / CatBoost / LightGBM)
- PyTorch Tabular Autoencoder & GraphSAGE GNN
- Qiskit 2.x Quantum Kernel Feature Representation (`zz_feature_map`, `FidelityStatevectorKernel`)
- Calibrated Stacking Meta-Learner

## Slide 3: Real Qiskit 2.x Telemetry & Verification
- 4-qubit and 6-qubit quantum state vector fidelity kernel matrices.
- Verified properties: Symmetric, Diagonal = 1.0, Positive Semi-Definite.
- Disk caching for $O(N_{sv})$ support vector scoring latency.

## Slide 4: Experimental Results & Benchmarks
- Real PR-AUC, ROC-AUC, Precision, Recall, and per-txn inference latency metrics loaded directly from `model_artifacts/**/metrics.json`.
- Fair comparison against Classical RBF-SVM and XGBoost on identical 4-qubit PCA subsamples.

## Slide 5: CRITICAL HONESTY DISCLOSURE — What We Did NOT Claim
> [!IMPORTANT]
> 1. **No Claim of Quantum Advantage**: NISQ simulators do not beat optimized classical XGBoost on classical tabular data. We frame our work as an *experimental comparison of quantum-enhanced feature representations*.
> 2. **Execution Labeling**: All quantum kernel results are strictly labeled **SIMULATION** (Qiskit Aer).
> 3. **No Fabricated Numbers**: All UI metrics originate directly from real evaluation scripts with zero hardcoded metrics.
> 4. **Synthetic Data Disclosure**: Payment streaming uses synthetic distributions clearly marked **SYNTHETIC**.

## Slide 6: Verified References
- Havlicek et al. *Supervised learning with quantum-enhanced feature spaces*. Nature 567, 209–212 (2019).
- Grossi et al. *Mixed Quantum-Classical Machine Learning Pipeline for Credit Card Fraud Detection*. IEEE TQE (2022).
- Kyriienko & Magnusson. *Quantum Kernels for Real-World Fraud Detection Datasets*. arXiv:2208.01203 (2022).
- Qiskit Machine Learning Documentation (v0.9.1).
