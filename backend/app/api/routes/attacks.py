from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.attack_service import attack_simulator

router = APIRouter(prefix="/api", tags=["Adversarial Attack Simulator"])

class AttackRequest(BaseModel):
    attack_type: str = "ACCOUNT_TAKEOVER" # ACCOUNT_TAKEOVER, VELOCITY_BURST, DEVICE_HOPPING, TRANSACTION_SPLITTING

@router.post("/attacks/simulate", summary="Execute Red-Team Fraud Attack Simulation")
async def simulate_attack(req: AttackRequest):
    """Generate simulated adversarial fraud attack and measure Q-FraudShield defense."""
    res = attack_simulator.simulate_attack(req.attack_type)
    return res

@router.get("/attacks/scenarios", summary="List Supported Red-Team Attack Scenarios")
async def list_scenarios():
    return [
        {
            "id": "ACCOUNT_TAKEOVER",
            "name": "Account Takeover (ATO)",
            "description": "Credential compromise + new device + IP hop + ₹85,000 transfer."
        },
        {
            "id": "VELOCITY_BURST",
            "name": "Velocity Burst Attack",
            "description": "Rapid 25 micro-transactions in 60 seconds to probe account balance."
        },
        {
            "id": "DEVICE_HOPPING",
            "name": "Device Hopping / Botnet Ring",
            "description": "1 compromised device attempting payments across 15 user accounts."
        },
        {
            "id": "TRANSACTION_SPLITTING",
            "name": "Structured Transaction Splitting",
            "description": "Splitting ₹1,00,000 into 10 smaller payments to bypass single-txn threshold."
        }
    ]

@router.get("/attack-lab/scenarios", summary="List Interactive Attack Lab Scenarios")
async def list_attack_lab_scenarios():
    """Returns 9 deterministic real-pipeline attack lab scenarios."""
    from backend.app.services.attack_lab_service import attack_lab_service
    return attack_lab_service.list_scenarios()

@router.post("/attack-lab/run/{scenario_id}", summary="Execute Attack Lab Scenario through Real Detection Pipeline")
async def run_attack_lab_scenario(scenario_id: str):
    """Executes attack lab scenario through real forensics, ML, quantum escalation, fusion, and response pipelines."""
    from backend.app.services.attack_lab_service import attack_lab_service
    return attack_lab_service.execute_scenario(scenario_id)

class GenerateSimulatedQRRequest(BaseModel):
    scenario_type: str = "PHISHING_PAYMENT_LURE" # PHISHING_PAYMENT_LURE, TAMPERED_AMOUNT, UNVERIFIED_MULE
    custom_txn: str | None = None

@router.post("/attack-lab/generate-qr", summary="Generate Real Downloadable QR Artifact for Cybersecurity Lab")
async def generate_simulated_qr(req: GenerateSimulatedQRRequest | None = None):
    """
    Generates deterministic or custom simulated QR code for attack testing:
    - Builds real RFC 2606/6761 compliant test payment verification payload
    - Produces real downloadable PNG Base64 QR code image
    - Assigns ground-truth label SIMULATED_SUSPICIOUS
    - Ready for direct piping into /api/check-payment
    """
    import io
    import time
    import base64
    import qrcode

    scenario = req.scenario_type if req and req.scenario_type else "PHISHING_PAYMENT_LURE"
    txn_id = req.custom_txn if req and req.custom_txn else f"DEMO{int(time.time() * 1000) % 100000:05d}"

    if scenario == "BENIGN_BASELINE":
        payload = f"upi://pay?pa=verified.store@icici&pn=Verified%20Store%20Retail&am=850.00&cu=INR&tn=Invoice%20{txn_id}"
        expected_verdict = "SIMULATED_BENIGN"
        category = "Verified Clean Retail"
        description = "Legitimate merchant checkout with clean parameters, verified payee format, and moderate amount."
    elif scenario == "TAMPERED_AMOUNT":
        payload = f"upi://pay?pa=tampered.store@icici&pn=Tampered%20Store&am=500.00&cu=INR&tn=Invoice%20{txn_id}"
        expected_verdict = "SIMULATED_SUSPICIOUS"
        category = "Amount Tampering"
        description = "Embedded QR requests ₹500.00 while claiming ₹5,000.00 in receipt lure."
    elif scenario == "UNVERIFIED_MULE":
        payload = f"upi://pay?pa=mule.drain.88@ybl&pn=Quick%20Cash%20Transfer&am=45000.00&cu=INR&tn=Immediate%20Drain%20{txn_id}"
        expected_verdict = "SIMULATED_SUSPICIOUS"
        category = "Mule Rapid Outflow"
        description = "Unregistered account with high outflow ratio and proxy IP origin."
    else:
        # Default: Phishing Payment Verification Lure on reserved .test TLD
        payload = f"https://payment-verification.example.test/confirm?txn={txn_id}"
        expected_verdict = "SIMULATED_SUSPICIOUS"
        category = "Phishing Payment Lure"
        description = "Simulated credential harvesting & fake bank confirmation gateway on RFC 2606 .test domain."

    # Generate real high-contrast PNG QR with standard quiet-zone border for 100% OpenCV detection
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="#ffffff")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()
    b64_qr = base64.b64encode(png_bytes).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64_qr}"

    return {
        "status": "GENERATED",
        "simulation_id": f"SIM-{txn_id}",
        "scenario_type": scenario,
        "category": category,
        "description": description,
        "decoded_payload": payload,
        "ground_truth_label": expected_verdict,
        "qr_base64": b64_qr,
        "qr_data_uri": data_uri,
        "file_name": f"simulated_attack_qr_{txn_id}.png",
        "file_size_bytes": len(png_bytes),
        "target_endpoint": "/api/check-payment",
        "created_at": time.time()
    }

