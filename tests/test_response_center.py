import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.investigation_service import investigation_service
from backend.app.services.response_service import response_service
from backend.app.services.copilot_service import copilot_service
from backend.app.schemas.investigation import (
    InvestigationCase, CaseSummary, InvestigationScorecard,
    CaseDecisionRecord, EntityDetail
)

client = TestClient(app)

@pytest.fixture
def sample_high_risk_case():
    return investigation_service.get_case("QF-20261007-49910")

def test_high_risk_response_recommendation(sample_high_risk_case):
    """Verify high risk / critical cases trigger DO NOT PAY / SECURE ACCOUNT recommendations."""
    resp = response_service.generate_response_center_data(sample_high_risk_case)
    assert resp.case_id == "QF-20261007-49910"
    assert resp.risk_score >= 90.0
    assert "DO NOT PAY" in resp.recommendation.primary_action or "SECURE ACCOUNT" in resp.recommendation.primary_action
    assert resp.recommendation.risk_level in ["HIGH", "CRITICAL"]
    assert resp.recommendation.verification_recommendation in ["STRONG_VERIFICATION", "DO_NOT_PROCEED"]
    assert len(resp.action_cards) >= 4
    assert len(resp.playbook) >= 4

def test_risk_vs_confidence_separation(sample_high_risk_case):
    """Verify that Risk Score, Confidence Level, and Action Recommendations are separated."""
    resp = response_service.generate_response_center_data(sample_high_risk_case)
    # Risk score is a float 0-100
    assert isinstance(resp.risk_score, float)
    assert 0.0 <= resp.risk_score <= 100.0
    # Confidence is 0.0-1.0
    assert 0.0 <= resp.confidence <= 1.0
    assert resp.recommendation.confidence_level in ["HIGH", "MEDIUM", "LOW"]
    # Action is a distinct string
    assert resp.recommendation.primary_action != ""

def test_low_risk_response():
    """Verify low risk cases recommend Proceed with Normal Caution (no overclaiming 100% safe)."""
    low_case = InvestigationCase(
        case_id="QF-TEST-LOW-001",
        status="RESOLVED",
        created_at=1700000000.0,
        updated_at=1700000000.0,
        source="CHECK_PAYMENT",
        summary=CaseSummary(
            what_happened="Verified payment to known merchant.",
            why_suspicious="No anomalies detected.",
            what_should_happen_next="Proceed with normal caution."
        ),
        risk={
            "risk_score": 14.5,
            "risk_level": "LOW RISK",
            "confidence": 0.94,
            "decision": "ALLOW",
            "recommendation": "PROCEED WITH NORMAL CAUTION"
        },
        quantum_escalation={},
        fraud_dna={},
        evidence=[{"field": "amount", "value": 500, "provenance": "OBSERVED"}],
        timeline=[],
        entities=[EntityDetail(entity_id="M-01", entity_type="MERCHANT", name="Coffee Shop", risk_score=5.0)],
        scorecard=InvestigationScorecard(evidence_quality="HIGH", model_confidence="HIGH"),
        model_analysis={},
        decision_history=CaseDecisionRecord(
            system_decision="ALLOW",
            system_recommendation="PROCEED WITH NORMAL CAUTION",
            system_risk_score=14.5,
            updated_at=1700000000.0
        )
    )
    resp = response_service.generate_response_center_data(low_case)
    assert resp.recommendation.risk_level == "LOW"
    assert resp.recommendation.primary_action == "PROCEED WITH NORMAL CAUTION"
    assert "100% safe" not in resp.recommendation.rationale.lower()
    assert resp.recommendation.verification_recommendation == "NORMAL_VERIFICATION"

def test_medium_risk_response():
    """Verify medium risk cases recommend Review Before Proceeding & Step-Up Auth."""
    med_case = InvestigationCase(
        case_id="QF-TEST-MED-002",
        status="UNDER_REVIEW",
        created_at=1700000000.0,
        updated_at=1700000000.0,
        source="CHECK_PAYMENT",
        summary=CaseSummary(
            what_happened="New payee handle with moderate amount.",
            why_suspicious="First time transferring to this beneficiary.",
            what_should_happen_next="Review details before authorizing."
        ),
        risk={
            "risk_score": 52.0,
            "risk_level": "MEDIUM RISK",
            "confidence": 0.78,
            "decision": "STEP_UP",
            "recommendation": "REVIEW BEFORE PROCEEDING"
        },
        quantum_escalation={},
        fraud_dna={},
        evidence=[{"field": "amount", "value": 7500, "provenance": "OBSERVED"}],
        timeline=[],
        entities=[EntityDetail(entity_id="RECIP-02", entity_type="RECIPIENT", name="Unknown Seller", risk_score=55.0)],
        scorecard=InvestigationScorecard(evidence_quality="MEDIUM", model_confidence="MEDIUM"),
        model_analysis={},
        decision_history=CaseDecisionRecord(
            system_decision="STEP_UP",
            system_recommendation="REVIEW BEFORE PROCEEDING",
            system_risk_score=52.0,
            updated_at=1700000000.0
        )
    )
    resp = response_service.generate_response_center_data(med_case)
    assert resp.recommendation.risk_level == "MEDIUM"
    assert resp.recommendation.primary_action == "REVIEW BEFORE PROCEEDING"
    assert resp.recommendation.verification_recommendation == "STEP_UP_VERIFICATION"

def test_evidence_package_provenance_and_unavailable_fields(sample_high_risk_case):
    """Verify evidence package identifies OBSERVED, INFERRED, and UNAVAILABLE fields without hallucination."""
    resp = response_service.generate_response_center_data(sample_high_risk_case)
    pkg = resp.evidence_package
    assert pkg.case_id == "QF-20261007-49910"
    assert pkg.observed_fields_count > 0
    assert pkg.unavailable_fields_count > 0
    assert "ss7_telecom_routing" in pkg.unavailable_fields
    assert len(pkg.items) >= 5

def test_action_audit_trail_recording():
    """Verify real actions are recorded in the audit trail without fabricated timestamps."""
    case_id = "QF-20261007-49910"
    entry = response_service.record_audit_action(
        case_id=case_id,
        action_name="Evidence Dossier Exported",
        actor="ANALYST",
        details="Generated clean report for compliance review."
    )
    assert entry.action_name == "Evidence Dossier Exported"
    assert entry.actor == "ANALYST"
    assert entry.provenance == "OBSERVED"

    case_obj = investigation_service.get_case(case_id)
    resp = response_service.generate_response_center_data(case_obj)
    action_names = [a.action_name for a in resp.audit_trail]
    assert "Evidence Dossier Exported" in action_names

def test_api_get_response():
    """Test GET /api/investigation/cases/{case_id}/response endpoint."""
    res = client.get("/api/investigation/cases/QF-20261007-49910/response")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "QF-20261007-49910"
    assert "recommendation" in data
    assert "action_cards" in data
    assert "playbook" in data
    assert "evidence_package" in data
    assert "audit_trail" in data
    assert "simple_view_guide" in data

def test_api_get_response_404():
    """Test GET /api/investigation/cases/{case_id}/response returns 404 for non-existent case."""
    res = client.get("/api/investigation/cases/NON-EXISTENT-9999/response")
    assert res.status_code == 404

def test_api_forensic_report_11_sections():
    """Test GET /api/investigation/cases/{case_id}/report returns all 11 required sections."""
    res = client.get("/api/investigation/cases/QF-20261007-49910/report")
    assert res.status_code == 200
    dossier = res.json()
    
    sections = [
        "1_case_overview", "2_payment_details", "3_risk_assessment",
        "4_evidence_summary", "5_why_it_was_flagged", "6_fraud_dna",
        "7_attack_chain", "8_connected_entities", "9_recommended_actions",
        "10_limitations", "11_provenance"
    ]
    for sec in sections:
        assert sec in dossier, f"Missing required section: {sec}"

def test_api_analyst_decision_alias():
    """Test POST /api/investigation/cases/{case_id}/analyst-decision records decision separately."""
    payload = {
        "analyst_action": "CONFIRM_RECOMMENDATION",
        "rationale": "Forensic review confirms payee impersonation.",
        "author": "Lead SOC Analyst Vardh"
    }
    res = client.post("/api/investigation/cases/QF-20261007-49910/analyst-decision", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision_history"]["analyst_action"] == "CONFIRM_RECOMMENDATION"
    assert data["decision_history"]["analyst_review_status"] == "CONFIRMED"

def test_copilot_response_center_grounding():
    """Verify Copilot answers Response Center queries grounded in real case evidence."""
    ctx = {"txn_id": "QF-20261007-49910", "risk_score": 92.4, "decision": "BLOCK"}
    
    # 1. What should I do next?
    res_next = copilot_service.answer_query("What should I do next?", context_data=ctx)
    assert "DO NOT PAY" in res_next["answer"] or "Stop" in res_next["answer"]
    assert "Response Center" in str(res_next["grounded_sources"])
    
    # 2. Why are you recommending this action?
    res_why = copilot_service.answer_query("Why are you recommending this action?", context_data=ctx)
    assert "92.4" in res_why["answer"]
    assert "Risk Score" in res_why["answer"]
    
    # 3. What should I preserve?
    res_pres = copilot_service.answer_query("What should I preserve for a fraud report?", context_data=ctx)
    assert "QR" in res_pres["answer"]
    assert "screenshot" in res_pres["answer"].lower()
