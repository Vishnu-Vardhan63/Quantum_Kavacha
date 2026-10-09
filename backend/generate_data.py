import os
import numpy as np
import pandas as pd

def generate_creditcard_csv():
    np.random.seed(42)
    n_samples = 2000
    n_fraud = 150
    n_normal = n_samples - n_fraud

    # Normal transactions
    time_normal = np.random.uniform(0, 172800, n_normal)
    amount_normal = np.random.exponential(scale=88.0, size=n_normal)
    v_normal = np.random.normal(loc=0.0, scale=1.0, size=(n_normal, 28))

    # Fraud transactions (shifted distributions for PCA features and higher amounts)
    time_fraud = np.random.uniform(0, 172800, n_fraud)
    amount_fraud = np.random.exponential(scale=350.0, size=n_fraud) + 50.0
    v_fraud = np.random.normal(loc=0.0, scale=1.0, size=(n_fraud, 28))
    
    # Introduce distinct anomaly patterns in specific PCA dimensions for fraud
    v_fraud[:, 0] -= 2.5   # V1 shift
    v_fraud[:, 1] += 3.0   # V2 shift
    v_fraud[:, 3] -= 3.5   # V4 shift
    v_fraud[:, 10] -= 4.0  # V11 shift
    v_fraud[:, 13] -= 3.0  # V14 shift
    v_fraud[:, 16] -= 2.8  # V17 shift

    # Combine normal and fraud
    time_col = np.concatenate([time_normal, time_fraud])
    amount_col = np.concatenate([amount_normal, amount_fraud])
    v_cols = np.vstack([v_normal, v_fraud])
    class_col = np.concatenate([np.zeros(n_normal, dtype=int), np.ones(n_fraud, dtype=int)])

    data = {'Time': time_col}
    for i in range(1, 29):
        data[f'V{i}'] = v_cols[:, i-1]
    data['Amount'] = amount_col
    data['Class'] = class_col

    df = pd.DataFrame(data)
    # Shuffle
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    out_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'creditcard.csv')
    df.to_csv(out_path, index=False)
    print(f"Successfully generated {out_path} with shape {df.shape}")
    print("Class breakdown:")
    print(df['Class'].value_counts())

if __name__ == '__main__':
    generate_creditcard_csv()
