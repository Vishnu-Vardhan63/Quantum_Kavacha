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

