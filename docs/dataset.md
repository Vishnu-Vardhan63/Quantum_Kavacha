# Dataset Strategy & Disclosures

## Datasets Supported
1. **Synthetic Payments Dataset (`data/sample/demo_transactions.csv`)**:
   - Generated via `scripts/generate_demo_data.py`.
   - Explicitly labeled **SYNTHETIC** in UI and documentation.
   - Contains fields: `txn_id`, `user_id`, `account_id`, `device_id`, `ip`, `merchant_id`, `lat`, `lon`, `amount`, `hour`, `velocity_1h`, `account_age_days`, `device_score`, `location_score`, `merchant_risk`, `label`.
   - Embeds benchmark demo transaction `TXN-QF-001` (INR 85,000, 23:15, velocity 12, account age 40 days).

2. **Kaggle Credit Card Fraud Dataset (`creditcard.csv`)**:
   - Contains anonymized PCA features $V_1 \dots V_{28}$, `Time`, `Amount`, `Class`.
   - **Disclosure & Limitation**: $V_1 \dots V_{28}$ are anonymized numerical vectors with no device, IP, merchant, or location columns. Dataset adapter auto-detects column capabilities and sets `has_graph=False`, `has_geo=False`, `has_device=False` so UI panels degrade gracefully.
