import asyncio
import time
import random
import json
import numpy as np
import pandas as pd
from typing import AsyncGenerator, Dict, Any, List
from backend.app.schemas.transaction import TransactionPayload
from backend.app.services.fraud_engine import fraud_engine

class SimulationService:
    """
    Real-time transaction simulator and streaming engine.
    Generates realistic payment stream at 1-2s cadence with ~5% fraud rate.
    Maintains an in-memory buffer of scored transactions.
    """
    def __init__(self):
        self.is_running = False
        self.buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 500
        self.counter = 1000

    def start_simulation(self):
        self.is_running = True

    def stop_simulation(self):
        self.is_running = False

    def generate_single_event(self) -> Dict[str, Any]:
        self.counter += 1
        txn_id = f"TXN-SIM-{self.counter}"
        
        is_fraud = (random.random() < 0.05)
        
        if is_fraud:
            amount = float(np.random.lognormal(mean=10.0, sigma=0.8))
            hour = random.choice([23, 0, 1, 2, 3])
            velocity = random.randint(8, 20)
            account_age = random.randint(1, 50)
            dev_score = round(random.uniform(0.7, 0.95), 2)
            loc_score = round(random.uniform(0.7, 0.95), 2)
            merch_risk = round(random.uniform(0.6, 0.9), 2)
        else:
            amount = float(np.random.lognormal(mean=7.0, sigma=1.0))
            amount = max(10.0, min(amount, 20000.0))
            hour = random.randint(7, 21)
            velocity = random.randint(1, 4)
            account_age = random.randint(60, 1000)
            dev_score = round(random.uniform(0.01, 0.2), 2)
            loc_score = round(random.uniform(0.01, 0.25), 2)
            merch_risk = round(random.uniform(0.01, 0.25), 2)

        payload = TransactionPayload(
            txn_id=txn_id,
            user_id=f"USR-{random.randint(100, 999)}",
            account_id=f"ACC-{random.randint(100, 999)}",
            device_id=f"DEV-{random.randint(100, 999)}",
            ip=f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
            merchant_id=f"MERCH-{random.randint(50, 200)}",
            lat=round(19.0760 + random.uniform(-0.1, 0.1), 4),
            lon=round(72.8777 + random.uniform(-0.1, 0.1), 4),
            amount=round(amount, 2),
            hour=hour,
            velocity_1h=velocity,
            account_age_days=account_age,
            device_score=dev_score,
            location_score=loc_score,
            merchant_risk=merch_risk
        )

        res = fraud_engine.predict(payload)
        
        event_data = {
            "transaction": payload.model_dump(),
            "prediction": res.model_dump(),
            "timestamp": time.time()
        }
        
        self.buffer.insert(0, event_data)
        if len(self.buffer) > self.max_buffer_size:
            self.buffer.pop()

        return event_data

    async def stream_events(self) -> AsyncGenerator[str, None]:
        while True:
            if self.is_running:
                event_data = self.generate_single_event()
                yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(1.5)

simulation_service = SimulationService()
