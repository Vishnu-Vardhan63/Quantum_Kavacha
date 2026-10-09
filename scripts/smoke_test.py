import urllib.request
import json
import sys

def get(url):
    req = urllib.request.Request(url)
    res = urllib.request.urlopen(req, timeout=5)
    return json.loads(res.read().decode())

def post(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req, timeout=5)
    return json.loads(res.read().decode())

def main():
    print("=== SMOKE TEST START ===")
    h = get("http://127.0.0.1:8000/api/health")
    print(f"1. Health: {h['status']} | Quantum Online: {h['quantum_engine']['online']}")

    cases = get("http://127.0.0.1:8000/api/investigation/cases")
    print(f"2. Indexed Cases: {len(cases)} cases found.")

    demo_id = "QF-20261007-49910"
    resp = get(f"http://127.0.0.1:8000/api/investigation/cases/{demo_id}/response")
    print(f"3. Response Recommendation: {resp['recommendation']['primary_action']} | Risk: {resp['risk_score']}% | Cards: {len(resp['action_cards'])}")

    rep = get(f"http://127.0.0.1:8000/api/investigation/cases/{demo_id}/report")
    print(f"4. Forensic Report: {len(rep.keys())} sections: {list(rep.keys())[:3]}...")

    ac = get(f"http://127.0.0.1:8000/api/investigation/cases/{demo_id}/attack-chain")
    print(f"5. Attack Chain: {ac['summary']['events_count']} events over {ac['summary']['time_span']}")

    cop = post("http://127.0.0.1:8000/api/copilot/chat", {"query": "What should I do next?", "context": {"txn_id": demo_id}})
    print(f"6. Copilot Grounded Sources: {cop['grounded_sources']}")

    graph = get(f"http://127.0.0.1:8000/api/graph/case/{demo_id}")
    print(f"7. Fraud Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    print("=== SMOKE TEST COMPLETE: ALL SYSTEMS VERIFIED ===")

if __name__ == "__main__":
    main()
