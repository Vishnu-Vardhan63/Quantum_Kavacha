# Quantum Methodology & Benchmark Approach

## Quantum Feature Space Mapping
Q-FraudShield uses Qiskit 2.x API function `zz_feature_map(feature_dimension, reps, entanglement)` to map scaled transaction features $x \in [0, 2\pi]^d$ into Hilbert space state vectors $|\Phi(x)\rangle$.

The quantum kernel fidelity between two transactions $x_i$ and $x_j$ is given by:
$$K(x_i, x_j) = |\langle \Phi(x_i) | \Phi(x_j) \rangle|^2$$

## Implementation Protocol (Qiskit 2.x API)
- **Feature Map**: `zz_feature_map(feature_dimension=4, reps=2, entanglement='linear')`
- **Kernel Computation**: `FidelityStatevectorKernel(feature_map=fm)`
- **Mathematical Guarantees**:
  1. $K(x_i, x_j) = K(x_j, x_i)$ (Symmetric)
  2. $K(x_i, x_i) = 1.0$ (Diagonal Ones)
  3. $\lambda_{\min}(K) \ge 0$ (Positive Semi-Definite)

## Benchmark Comparison & Advantage Disclaimers
- All quantum kernel results in this system are executed in **SIMULATION** mode using Qiskit Aer Statevector simulators.
- **Fair Subsample Comparison**: Quantum QSVC is benchmarked against Classical RBF-SVM and XGBoost trained on the **exact same 600-sample stratified subset** and **exact same 4-qubit PCA features**.
- **Honesty Disclosure**: No claim of quantum advantage is made. We present an experimental comparison of classical vs quantum-kernel feature representations under NISQ constraints.

## Verified Scientific References
1. Havlicek, V., Córcoles, A.D., Temme, K. et al. *Supervised learning with quantum-enhanced feature spaces*. Nature 567, 209–212 (2019).
2. Grossi, M. et al. *Mixed Quantum-Classical Machine Learning Pipeline for Credit Card Fraud Detection*. IEEE Transactions on Quantum Engineering (2022).
3. Kyriienko, O., & Magnusson, E. *Quantum Kernels for Real-World Fraud Detection Datasets*. arXiv:2208.01203 (2022).
4. Qiskit Machine Learning Documentation (v0.9.1).
