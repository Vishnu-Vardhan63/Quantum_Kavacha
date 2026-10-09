import urllib.request
import json
import time

# Direct connection without system proxy
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(opener)

base = "http://127.0.0.1:8000"

get_endpoints = [
    "/api/health",
    "/api/analytics",
    "/api/models/comparison",
    "/api/quantum/status",
    "/api/quantum/benchmark",
    "/api/attack-lab/scenarios",
    "/api/investigation/cases",
    "/api/investigation/cases/QF-20261007-49910",
    "/api/investigation/cases/QF-20261007-49910/attack-chain",
    "/api/investigation/cases/QF-20261007-49910/response",
    "/api/graph/cases/QF-20261007-49910"
]

print("--- TESTING GET ENDPOINTS ---")
for ep in get_endpoints:
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(base + ep)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            dur = (time.perf_counter() - t0) * 1000.0
            print(f"[PASS] {ep:<50} -> HTTP {resp.status} ({dur:.1f}ms)", flush=True)
    except Exception as e:
        print(f"[FAIL] {ep:<50} -> {e}", flush=True)

post_scenarios = [
    "SCENARIO_1_GENUINE_PAYMENT",
    "SCENARIO_2_QR_AMOUNT_MANIPULATION",
    "SCENARIO_3_SCREENSHOT_PAYMENT_FRAUD",
    "SCENARIO_4_PHISHING_PAYMENT_LINK",
    "SCENARIO_5_ACCOUNT_TAKEOVER",
    "SCENARIO_6_TRANSACTION_VELOCITY_ATTACK",
    "SCENARIO_7_DEVICE_ANOMALY",
    "SCENARIO_8_PAYMENT_PAYLOAD_TAMPERING",
    "SCENARIO_9_SUSPICIOUS_ENTITY_CLUSTER"
]

print("\n--- TESTING 9 ATTACK LAB SCENARIOS (REAL PIPELINE EXECUTION) ---", flush=True)
for sc_id in post_scenarios:
    t0 = time.perf_counter()
    url = f"{base}/api/attack-lab/run/{sc_id}"
    try:
        req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read().decode())
            dur = (time.perf_counter() - t0) * 1000.0
            risk = res.get("risk_score")
            decision = res.get("decision")
            trust = res.get("trust_level")
            quantum = res.get("quantum_analysis", {}).get("escalation_status")
            dna = res.get("transaction_dna", {}).get("status")
            integrity = res.get("payload_integrity", {}).get("integrity_status")
            print(f"[PASS] {sc_id:<40} -> Risk: {risk}% | Dec: {decision:<6} | Trust: {trust:<15} | Q: {quantum:<8} | DNA: {dna:<20} | Payload: {integrity:<18} ({dur:.1f}ms)", flush=True)
    except Exception as e:
        print(f"[FAIL] {sc_id:<40} -> {e}", flush=True)
