import os
import random
import numpy as np
import pandas as pd

def generate_synthetic_transactions(num_samples: int = 1200, seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic payment transactions with realistic fraud patterns.
    Outputs columns:
    [txn_id, user_id, account_id, device_id, ip, merchant_id, lat, lon,
     amount, hour, velocity_1h, account_age_days, device_score, location_score,
     merchant_risk, label]
    """
    np.random.seed(seed)
    random.seed(seed)

    records = []
    
    # Pre-generate pool of users, devices, merchants
    num_users = max(50, num_samples // 15)
    num_merchants = max(20, num_samples // 30)
    num_devices = max(60, num_samples // 12)
    
    users = [f"USR-{1000 + i}" for i in range(num_users)]
    accounts = [f"ACC-{1000 + i}" for i in range(num_users)]
    devices = [f"DEV-{2000 + i}" for i in range(num_devices)]
    merchants = [f"MERCH-{500 + i}" for i in range(num_merchants)]
    
    # Compromised merchants and shared fraud device pool for ring fraud injection
    fraud_ring_devices = random.sample(devices, k=min(5, len(devices)))
    compromised_merchants = random.sample(merchants, k=min(3, len(merchants)))
    
    # Base location centers (e.g. major Indian tech hubs: Mumbai, Bangalore, Delhi)
    cities = [
        (19.0760, 72.8777), # Mumbai
        (12.9716, 77.5946), # Bangalore
        (28.6139, 77.2090), # Delhi
    ]

    for i in range(1, num_samples):
        txn_id = f"TXN-{100000 + i}"
        u_idx = random.randint(0, num_users - 1)
        user_id = users[u_idx]
        account_id = accounts[u_idx]
        
        # Decide if this sample should be fraud (~5-8% overall rate)
        is_fraud = 1 if (random.random() < 0.07) else 0
        
        if is_fraud:
            fraud_type = random.choice(["velocity_burst", "shared_device_ring", "compromised_merchant"])
            if fraud_type == "velocity_burst":
                device_id = random.choice(devices)
                merchant_id = random.choice(merchants)
                amount = float(np.random.lognormal(mean=10.0, sigma=0.8)) # Large amount
                hour = random.choice([22, 23, 0, 1, 2, 3, 4]) # Late night
                velocity_1h = random.randint(8, 25)
                account_age_days = random.randint(1, 45) # Young account
                device_score = round(random.uniform(0.70, 0.95), 2)
                location_score = round(random.uniform(0.75, 0.98), 2)
                merchant_risk = round(random.uniform(0.4, 0.85), 2)
            elif fraud_type == "shared_device_ring":
                device_id = random.choice(fraud_ring_devices) # Shared fraud device
                merchant_id = random.choice(merchants)
                amount = float(np.random.lognormal(mean=9.2, sigma=0.6))
                hour = random.randint(0, 23)
                velocity_1h = random.randint(5, 18)
                account_age_days = random.randint(5, 90)
                device_score = round(random.uniform(0.80, 0.99), 2)
                location_score = round(random.uniform(0.60, 0.90), 2)
                merchant_risk = round(random.uniform(0.50, 0.90), 2)
            else: # compromised merchant
                device_id = random.choice(devices)
                merchant_id = random.choice(compromised_merchants)
                amount = float(np.random.lognormal(mean=9.5, sigma=0.7))
                hour = random.randint(0, 23)
                velocity_1h = random.randint(6, 20)
                account_age_days = random.randint(10, 200)
                device_score = round(random.uniform(0.40, 0.80), 2)
                location_score = round(random.uniform(0.50, 0.85), 2)
                merchant_risk = round(random.uniform(0.85, 0.99), 2)
        else: # Legitimate transaction
            device_id = devices[u_idx % len(devices)]
            merchant_id = random.choice(merchants)
            amount = float(np.random.lognormal(mean=7.0, sigma=1.0)) # Normal amounts (e.g. 500 - 5000 INR)
            amount = max(10.0, min(amount, 25000.0))
            hour = random.randint(6, 22) # Daytime/evening
            velocity_1h = random.randint(1, 4)
            account_age_days = random.randint(60, 1500)
            device_score = round(random.uniform(0.01, 0.25), 2)
            location_score = round(random.uniform(0.01, 0.30), 2)
            merchant_risk = round(random.uniform(0.01, 0.30), 2)
            
        base_lat, base_lon = random.choice(cities)
        lat = base_lat + random.uniform(-0.08, 0.08)
        lon = base_lon + random.uniform(-0.08, 0.08)
        ip = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"

        records.append({
            "txn_id": txn_id,
            "user_id": user_id,
            "account_id": account_id,
            "device_id": device_id,
            "ip": ip,
            "merchant_id": merchant_id,
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "amount": round(amount, 2),
            "hour": hour,
            "velocity_1h": velocity_1h,
            "account_age_days": account_age_days,
            "device_score": device_score,
            "location_score": location_score,
            "merchant_risk": merchant_risk,
            "label": is_fraud
        })

    # ALWAYS include the benchmark scripted demo transaction TXN-QF-001 as required by SPEC.md
    demo_txn = {
        "txn_id": "TXN-QF-001",
        "user_id": "USR-9901",
        "account_id": "ACC-9901",
        "device_id": "DEV-9901",
        "ip": "192.168.1.105",
        "merchant_id": "MERCH-8802",
        "lat": 19.0760,
        "lon": 72.8777,
        "amount": 85000.0, # High INR amount
        "hour": 23,        # Late night 23:15
        "velocity_1h": 12,
        "account_age_days": 40,
        "device_score": 0.78,
        "location_score": 0.82,
        "merchant_risk": 0.76,
        "label": 1         # Ground truth fraud / high risk demo
    }
    records.insert(0, demo_txn)

    df = pd.DataFrame(records)
    return df

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    sample_dir = os.path.join(project_root, "data", "sample")
    os.makedirs(sample_dir, exist_ok=True)
    
    output_path = os.path.join(sample_dir, "demo_transactions.csv")
    df = generate_synthetic_transactions(num_samples=1200, seed=42)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} synthetic transactions saved to {output_path}")
    print(f"Sample fraud count: {df['label'].sum()} / {len(df)}")
    print(f"TXN-QF-001 present: {'TXN-QF-001' in df['txn_id'].values}")

if __name__ == "__main__":
    main()
