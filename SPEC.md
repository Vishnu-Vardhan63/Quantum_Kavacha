# SPEC.md: Q-FraudShield Specifications

You are a senior ML engineer + quantum ML engineer + full-stack engineer + 3D web engineer. Build "Q-FraudShield: Quantum-Enhanced Digital Payment Fraud Intelligence" for the Qiskit Fall Fest 2026 24-hour hackathon (problem: Quantum-Enhanced Digital Payment Fraud Detection).

FIRST ACTION: save this entire message as SPEC.md in the project root. Then work milestone by milestone (M1..M10 below). After EACH milestone: run its acceptance check, report in max 5 lines (what passed, real numbers, what failed), then STOP and wait for me to reply "continue". Start with M1 now.

HONESTY RULES (non-negotiable)
1. No fabricated numbers. Every metric in the UI comes from model_artifacts/**/metrics.json written by real eval scripts. Untrained model => UI shows "Not evaluated".
2. No claim of quantum advantage. Use wording: "quantum-enhanced feature representation" and "experimental comparison of classical vs quantum-kernel approaches". Label every quantum result SIMULATION, NOISY SIMULATION, or HARDWARE. Default = SIMULATION.
3. Risk-factor explanations are computed from real outputs (SHAP, kernel similarity to nearest legit/fraud neighbors, graph neighbor risk). Never hard-code reason text per transaction.
4. Synthetic data is labelled SYNTHETIC in UI and docs.
5. Demo transaction TXN-QF-001 (amount 85000 INR, time 23:15, frequency 10, location score 0.82, device score 0.78, velocity 12, merchant risk 0.76, account age 40 days) must be scored by the real pipeline. If it isn't HIGH RISK, tune scenario inputs (not the model) and label it "scripted demo scenario". Never hard-code its output.
6. If something can't be verified, say so plainly. Never claim it works without running it.

DATA STRATEGY
- creditcard.csv (Kaggle ULB, V1-V28 are anonymized PCA components, NO device/IP/merchant/location columns). Used for classical, deep, and quantum benchmarks. Dataset adapter auto-detects target column (Class/is_fraud/isFraud/fraud/label), amount and time columns, and returns capability flags (has_graph, has_geo, has_device) so the UI disables unsupported panels.
- SYNTHETIC payments generator (scripts/generate_demo_data.py): txn_id, user_id, account_id, device_id, ip, merchant_id, lat, lon, amount, hour, velocity_1h, account_age_days, device_score, location_score, merchant_risk, label. Inject realistic fraud patterns (new device + high amount + velocity burst, shared-device rings, compromised merchant). Powers graph, heatmap, live simulation, investigation, INR demo. Optionally support PaySim via the adapter.
- No raw data committed. data/sample/demo_transactions.csv is small and synthetic.

EVALUATION PROTOCOL
- Time-ordered split for creditcard.csv; stratified for synthetic. SMOTE/class weights on TRAIN only. Scalers/PCA fit on train only. Threshold tuned on validation, applied once to test.
- Report precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, FPR, inference ms/txn. Primary: PR-AUC and recall at fixed precision.

MODELS
Classical: Logistic Regression, Random Forest, XGBoost, LightGBM, CatBoost + SHAP TreeExplainer.
Deep: Dense NN, Autoencoder (train on legit only; reconstruction error -> anomaly score normalized to [0,1]). VAE and Transformer = stretch goals.
Graph: PyTorch Geometric GraphSAGE (GAT optional) on the synthetic graph (nodes user/account/device/merchant/IP/location/transaction; edges MADE_TRANSACTION, USED_DEVICE, USED_IP, VISITED_LOCATION, PURCHASED_FROM, CONNECTED_TO) with NeighborLoader sampling, CPU-friendly.
Quantum (core differentiator), Qiskit 2.x API ONLY:
- Python 3.11/3.12; qiskit>=2.1, qiskit-machine-learning>=0.8, qiskit-aer, qiskit-ibm-runtime. Verify with pip and print resolved versions in /api/quantum/status.
- Use the zz_feature_map(...) FUNCTION (class ZZFeatureMap is deprecated since 2.1). Make feature map pluggable; benchmark ZZ (reps 1/2, linear vs full entanglement) vs at least one alternative (pauli_feature_map or data re-uploading).
- V2 primitives only (StatevectorSampler / Aer SamplerV2 / Runtime SamplerV2). No V1 Sampler/Estimator, no legacy BackendSampler.
- Kernel: FidelityStatevectorKernel by default; FidelityQuantumKernel + ComputeUncompute when shots/noise/hardware requested.
- Pipeline: preprocess -> feature selection -> PCA to 4/6/8 -> scale into rotation range -> feature map -> kernel.
- Heads: QSVC or sklearn SVC(kernel="precomputed") supervised; OneClassSVM(kernel="precomputed") on legit-only for unsupervised quantum_anomaly_score; plus kernel similarity to k nearest legit transactions for explanation.
- Compute budget: stratified subsample (default 600 train, configurable to ~2000), 4-8 qubits, kernel matrices cached on disk keyed by (feature-map config, data hash). Scoring one new txn = kernel vs support vectors only.
- Fair comparison: classical RBF-SVM and XGBoost on the SAME subsample and SAME PCA features. Report full-data classical results separately and labelled.
- IBM hardware optional, only if IBM_QUANTUM_TOKEN is in backend .env, never exposed to frontend, explicitly labelled HARDWARE. Demo path = SIMULATION.
- Quantum Lab data comes from the REAL QuantumCircuit: serialize gate list, qubit indices, params, depth, size, 2-qubit gate count; show decomposed circuit, fidelity kernel matrix heatmap, backend, measured execution time. Do not invent gate structures.
Ensemble: stacking meta-learner (logistic regression) on out-of-fold validation predictions of xgboost_prob, autoencoder_anomaly, gnn_prob, quantum_anomaly, behavioral_anomaly (z-score vs user history). Learned weights stored and displayed; manual override in Settings. Calibration (isotonic/Platt). Thresholds configurable: NORMAL <40, SUSPICIOUS 40-69, HIGH RISK >=70. Report ensemble vs each single model AND an ablation "ensemble without quantum".

GRACEFUL DEGRADATION
Startup capability probes for qiskit, torch, torch_geometric, lightgbm, catboost, shap. Missing => marked UNAVAILABLE in /api/health, ensemble renormalizes, UI shows "Quantum Engine: OFFLINE" and clearly says a classical fallback score is used (never pretend it's quantum). Never crash.

BACKEND (FastAPI, Pydantic v2, async)
Keep exactly this structure: Q-FraudShield/{README.md, LICENSE, .gitignore, .env.example, docker-compose.yml, Makefile, docs/{architecture,quantum-approach,ml-models,api,dataset,demo-script,presentation}.md, data/{raw,processed,sample}, backend/{app/{main.py, api/routes/{transactions,fraud,quantum,models,analytics,simulation}.py, api/dependencies.py, core/{config,logging,security}.py, schemas/{transaction,fraud,quantum,model}.py, services/{fraud_engine,transaction_service,quantum_service,graph_service,explanation_service,simulation_service}.py, utils/{preprocessing,metrics,feature_utils}.py}, models/{classical/train_{xgboost,lightgbm,catboost,random_forest}.py, deep_learning/{autoencoder,transformer,train_deep}.py, graph/{graph_builder,graphsage,gat,train_gnn}.py, quantum/{feature_map,quantum_kernel,qsvc,quantum_anomaly,backend_manager}.py, ensemble/{ensemble_engine,calibration}.py}, notebooks/01..05, tests/{test_api,test_quantum,test_models,test_preprocessing}.py, requirements.txt, Dockerfile}, frontend/{public/{logo.svg,quantum-grid.svg}, src/{main.tsx, App.tsx, components/{layout,dashboard,transactions,fraud,quantum,graph,analytics,ui}, three/{QuantumUniverse,TransactionParticles,TransactionGraph3D,QuantumCore,NeuralNetwork3D}.tsx + effects/, pages/{Dashboard,Transactions,FraudAlerts,QuantumLab,GraphIntelligence,Models,Analytics,Investigation,Settings}.tsx (+ Landing, Dataset), services/{api,transactionApi,quantumApi,modelApi}.ts, hooks, store, types, utils}, package.json, vite.config.ts, tailwind.config.js, Dockerfile}, model_artifacts/{classical,deep_learning,graph,quantum}, scripts/{setup.sh,train_all.py,generate_demo_data.py,benchmark.py}}.
Endpoints: GET /api/health; POST /api/train (background task + status polling); GET /api/metrics; POST /api/predict (returns per-stage timings); GET /api/transactions; GET /api/fraud-alerts; GET /api/analytics; POST /api/simulate/start; POST /api/simulate/stop; GET /api/quantum/status; POST /api/quantum/kernel; GET /api/models; GET /api/models/comparison; GET /api/investigation/{transaction_id}; plus SSE/WebSocket /api/stream.
Security: pydantic bounds on all fields, CORS allowlist from env, slowapi rate limiting, no secrets in repo, CSV upload validation (size, extension), no unpickling user uploads.
Storage: SQLite default; Postgres/Redis optional via docker-compose profile.

FRONTEND (React 18, Vite, TS, Tailwind, R3F, drei, Framer Motion, Recharts, Lucide, react-leaflet)
Pages: landing, /dashboard, /transactions, /fraud-alerts, /quantum-lab, /graph-intelligence, /models, /analytics, /dataset, /investigation/:id, /settings.
Design: bg #050510, secondary #0B0D1F, electric purple primary, cyan secondary, amber warning, red fraud, green normal; glassmorphism, neon glow, depth. Must not look like a stock admin template.
3D (real WebGL): QuantumCore (icosphere + wireframe + glow + orbiting rings). TransactionParticles use InstancedMesh/Points with per-instance attributes (NOT one mesh per particle) for 5-10k particles at ~60fps; picking by instance id; normal = stable orbit, suspicious = jitter, fraud = accelerated trajectory + red/orange emissive + pulse ring. TransactionGraph3D: user/device/merchant/IP/location/txn nodes, animated edges, risk-propagation animation, smooth camera fly-to on selection. Add low-power mode and WebGL-unavailable fallback.
Dashboard: cards (Total Transactions, Fraud Detected, Suspicious, Avg Risk, Quantum Analyzed, Accuracy, PR-AUC, FPR) and charts (volume, fraud trend, risk distribution, model comparison, quantum vs classical), all from real API data. Animated live feed. Pipeline animation (Transaction -> Preprocessing -> Classical/DL/GNN -> Quantum Kernel -> Ensemble -> Decision) where each stage lights up only when the backend actually finished it.
Model comparison table rows: LR, RF, XGBoost, LightGBM, CatBoost, Autoencoder, GNN, Quantum Kernel, Hybrid Ensemble; columns Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Inference Time; "Not evaluated" when no metrics.json; show dataset, split, sample size, SIMULATION/HARDWARE tag.
Investigation page (SOC style): txn id, amount, timestamp, merchant, device, location, IP, account, risk score, per-model scores (classical, DL, GNN, quantum), SHAP factors, graph connections, quantum similarity, timeline.
Heatmap: Leaflet, 24h/7d/30d + risk filters, SYNTHETIC geo data; hidden if dataset has no geo.
"Run Custom Transaction" form -> /api/predict -> full breakdown.
"START LIVE SIMULATION" (1-2s cadence, lognormal amounts, hour-of-day patterns, ~2-5% fraud, ring patterns) and "START 24H DEMO" scripted cinematic sequence (stream -> normals -> suspicious -> fraud -> models analyze -> quantum kernel step -> score -> particle turns red -> graph edges appear -> investigation opens -> SHAP -> final decision), scored by the real backend.
Landing page: hero "Detect Fraud Before It Becomes Damage." subheading "Hybrid Classical AI + Deep Learning + Graph Intelligence + Quantum Machine Learning", CTAs "Launch Fraud Intelligence" and "Explore Quantum Engine", 3D quantum sphere with transaction particles, fraud particles gradually turning red.

MILESTONES (acceptance checks)
M1 Scaffold + data layer: structure, adapter, synthetic generator, capability probes, /api/health. CHECK: pytest passes; health lists each component's status.
M2 Classical models + eval harness + metrics.json. CHECK: models trained, leakage-free split verified by a test.
M3 Quantum kernel pipeline (MOST IMPORTANT). CHECK: kernel matrix symmetric, PSD within tolerance, diagonal=1; uses zz_feature_map function; exported circuit info matches the circuit actually used; supervised and one-class heads run at 4 and 6 qubits; cache reload works; benchmark vs RBF-SVM on identical data in metrics.json. Report real numbers even if quantum loses.
M4 Autoencoder + Dense NN. CHECK: scores in [0,1]; AE trained on legit only.
M5 GNN on synthetic graph. CHECK: runs on CPU with neighbor sampling; disables cleanly if PyG missing (don't fight installation >10 min).
M6 Ensemble + calibration + ablation. CHECK: weights learned on validation; honest test metrics even if ensemble doesn't win.
M7 Full API + stream + simulation service. CHECK: script hits every endpoint; per-stage latency measured.
M8 Frontend shell + dashboard/transactions/models/dataset on real API. CHECK: npm run build, zero TS errors.
M9 3D universe + graph 3D + Quantum Lab + investigation + heatmap. CHECK: headless Chromium smoke test; log particle count/FPS; WebGL fallback works.
M10 Demo mode polish, docs (README with mermaid architecture, quantum methodology, dataset disclosure incl. creditcard anonymization limitation, API docs, demo script 2-min and 5-min, presentation outline with a "what we did NOT claim" slide, verified references: Havlicek et al. 2019 Nature; Grossi et al. 2022 IEEE TQE; Kyriienko & Magnusson 2022 arXiv:2208.01203; Qiskit ML docs), Docker, Makefile, setup.sh. CHECK: fresh setup works; one command starts everything.

CUT LIST if time runs low (in this order; never cut honesty rules or M3): VAE -> Transformer -> GAT -> Postgres/Redis -> Mapbox -> notebooks (use scripts) -> advanced landing animation.

FINAL DELIVERABLE (after M10)
A) folder tree B) install commands C) env vars D) training commands E) frontend start F) backend start G) demo instructions H) endpoints I) architecture explanation J) 60-second hackathon pitch K) known limitations (simulation-only quantum unless a hardware run is shown, small-sample quantum training, synthetic data caveats, no advantage claim).

When something breaks: show the exact error, find the root cause, fix it, rerun the failing command and show it passing. Never edit tests just to make them pass.

BEGIN NOW: save SPEC.md, then do M1 only, then stop and wait for "continue".
