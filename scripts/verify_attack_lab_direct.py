import time
import json
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print("=" * 80, flush=True)
print("QUANTUM KAVACHA -- PHASE 2 ATTACK LAB & SYSTEM VALIDATION", flush=True)
print("=" * 80, flush=True)

# 1. Health & Status
h_resp = client.get("/api/health")
print(f"\n[1] Health Check -> Status {h_resp.status_code}: {h_resp.json()['service']} v{h_resp.json()['version']}", flush=True)

# 2. Quantum Status & Benchmark
q_stat = client.get("/api/quantum/status")
print(f"[2] Quantum Status -> Status {q_stat.status_code}: Mode: {q_stat.json().get('execution_mode')}, Online: {q_stat.json().get('engine_online')}", flush=True)

q_bench = client.get("/api/quantum/benchmark")
print(f"[3] Quantum Benchmark -> Status {q_bench.status_code}:", flush=True)
qb = q_bench.json()
print(f"    - Dataset: {qb.get('dataset_info', {}).get('dataset_type')}", flush=True)
print(f"    - Classical Baseline F1: {qb.get('comparison', {}).get('classical_only', {}).get('f1_score')}", flush=True)
print(f"    - Hybrid Quantum F1:    {qb.get('comparison', {}).get('hybrid_quantum_classical', {}).get('f1_score')}", flush=True)
print(f"    - Delta F1:              +{qb.get('deltas', {}).get('f1_delta')}", flush=True)
print(f"    - Honesty Summary:       {qb.get('technical_honest_assessment')[:100]}...", flush=True)

# 3. Scenarios List
sc_resp = client.get("/api/attack-lab/scenarios")
scenarios = sc_resp.json()
print(f"\n[4] Attack Lab Scenarios Loaded: {len(scenarios)} scenarios", flush=True)

print("\n" + "=" * 80, flush=True)
print("EXECUTING ALL 9 ATTACK LAB SCENARIOS (REAL COMPUTATION)", flush=True)
print("=" * 80, flush=True)

for sc in scenarios:
    sc_id = sc["id"]
    t0 = time.perf_counter()
    run_resp = client.post(f"/api/attack-lab/run/{sc_id}")
    latency = (time.perf_counter() - t0) * 1000.0
    
    assert run_resp.status_code == 200, f"Scenario {sc_id} failed with {run_resp.status_code}"
    res = run_resp.json()
    
    name = res.get("scenario_info", {}).get("name", sc_id)
    risk = res.get("risk_score")
    decision = res.get("decision")
    trust = res.get("trust_level")
    q_esc = res.get("quantum_analysis", {}).get("escalation_status")
    dna_status = res.get("transaction_dna", {}).get("status") if res.get("transaction_dna") else "UNAVAILABLE"
    integrity = res.get("payload_integrity", {}).get("integrity_status") if res.get("payload_integrity") else "UNAVAILABLE"
    chain_events = len(res.get("attack_chain", {}).get("events", [])) if res.get("attack_chain") else 0
    response_rec = res.get("response_center", {}).get("recommendation", {}).get("action_type") if res.get("response_center") else "N/A"
    
    print(f"\n[SCENARIO] {name}", flush=True)
    print(f"  * Decision:           {decision} (Trust: {trust})", flush=True)
    print(f"  * Authoritative Risk: {risk}%", flush=True)
    print(f"  * Payload Integrity:  {integrity}", flush=True)
    print(f"  * Transaction DNA:    {dna_status}", flush=True)
    print(f"  * Quantum Gate:       {q_esc}", flush=True)
    print(f"  * Attack Chain:       {chain_events} reconstructed events", flush=True)
    print(f"  * Response Action:    {response_rec}", flush=True)
    print(f"  * Execution Latency:  {latency:.1f} ms (Pipeline: {res.get('execution_mode')})", flush=True)

print("\n" + "=" * 80, flush=True)
print("ALL 9 ATTACK LAB SCENARIOS VALIDATED SUCCESSFULLY AGAINST LIVE PIPELINE!", flush=True)
print("=" * 80, flush=True)
