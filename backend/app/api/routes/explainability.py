from fastapi import APIRouter
from backend.app.schemas.transaction import TransactionPayload
from backend.app.services.explanation_service import explanation_service
from backend.app.services.fraud_engine import fraud_engine

router = APIRouter(prefix="/api", tags=["Explainable AI & FraudDNA"])

@router.post("/explainability/fraud-dna", summary="Generate FraudDNA 5-Axis Fingerprint")
async def get_fraud_dna(txn: TransactionPayload):
    pred = fraud_engine.predict(txn)
    dna = explanation_service.generate_fraud_dna(txn.model_dump(), pred.model_scores, pred.risk_score)
    cf = explanation_service.generate_counterfactuals(txn.model_dump(), pred.risk_score)
    return {
        "txn_id": pred.txn_id,
        "risk_score": pred.risk_score,
        "risk_level": pred.risk_level,
        "decision": pred.decision,
        "fraud_dna": dna,
        "counterfactuals": cf
    }
