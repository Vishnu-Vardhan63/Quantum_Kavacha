import pytest
from backend.app.services.fraud_engine import fraud_engine
from backend.app.services.payment_forensics import payment_forensics_service
from backend.app.services.explanation_service import explanation_service
from backend.app.schemas.transaction import TransactionPayload
from backend.app.schemas.check_payment import CheckPaymentRequest

def test_explicit_fusion_weights_and_contributions():
    """Verify that fusion contributions use explicit normalized weights summing to 1.00."""
    txn = TransactionPayload(
        txn_id="TXN-FUSION-TEST",
        amount=15000.0,
        device_score=0.85,
        velocity_1h=4,
        account_age_days=120,
        merchant_risk=0.20,
        location_score=0.15,
    )
    result = fraud_engine.predict(txn)
    
    fusion = result.fusion_result
    assert fusion is not None
    assert len(fusion.evidence_contributions) >= 6
    
    total_weight = sum(c.weight for c in fusion.evidence_contributions)
    assert abs(total_weight - 1.0) < 1e-4, f"Weights sum to {total_weight}, expected 1.00"
    
    # Check that score calculation is bounded
    assert 0.0 <= fusion.base_score <= 100.0
    assert 0.0 <= fusion.final_score <= 100.0
    assert 0.0 <= result.risk_score <= 100.0
    assert fusion.provenance in ["MODEL_INFERRED", "OBSERVED", "HEURISTIC", "SYSTEM_GENERATED"]

def test_counterfactual_genuine_rescoring():
    """Verify counterfactuals re-score the transaction through predict_raw_score."""
    txn = TransactionPayload(
        txn_id="TXN-COUNTERFACTUAL-TEST",
        amount=85000.0,
        device_score=0.85,
        velocity_1h=12,
        account_age_days=2,
        merchant_risk=0.75,
        location_score=0.65,
    )
    result = fraud_engine.predict(txn)
    
    cf_result = result.counterfactual_result
    assert cf_result is not None
    assert cf_result.baseline_score == result.risk_score
    assert len(cf_result.counterfactuals) > 0
    
    for cf in cf_result.counterfactuals:
        # Expected score should be lower or equal to baseline for risk-reducing mutations
        assert cf.new_score <= cf_result.baseline_score
        assert cf.delta == round(cf.new_score - cf_result.baseline_score, 1)

def test_cross_validation_qr_ocr_mismatch():
    """Verify that OCR vs QR amount mismatch creates a high-confidence mismatch."""
    upi_data = {"is_upi": True, "pa": "store@upi", "am": "5000.00", "pn": "Store A"}
    res = payment_forensics_service.evaluate_cross_validation(
        ocr_text="Paid ₹100.00 to Store A store@upi",
        upi_data=upi_data,
        transaction_context={},
        extracted_ocr_amt=100.0,
        extracted_ocr_vpa="store@upi",
        extracted_ocr_merchant="Store A"
    )
    assert res.items["amount"].status == "MISMATCH"
    assert res.items["amount"].severity == "CRITICAL"
    assert res.status == "MISMATCH"
    assert res.mismatches_count >= 1

def test_cross_validation_unavailable_is_not_mismatch():
    """Verify that missing metadata is tagged UNAVAILABLE and not penalised as MISMATCH."""
    upi_data = {}
    txn_ctx = {"amount": 250.0, "recipient_vpa": "merchant@icici"}
    res = payment_forensics_service.evaluate_cross_validation(
        ocr_text="Paid ₹250.00",
        upi_data=upi_data,
        transaction_context=txn_ctx,
        extracted_ocr_amt=250.0
    )
    assert res.items["amount"].status == "MATCH"
    assert res.items["vpa"].status == "UNAVAILABLE"
    assert res.items["merchant"].status == "UNAVAILABLE"
    assert res.status == "MATCH"

def test_deterministic_demo_scenarios():
    """Verify all 5 deterministic demo fixtures evaluate consistently."""
    sc_a = payment_forensics_service.get_scenario_by_id("SCENARIO_A_GENUINE_PAYMENT")
    res_a = payment_forensics_service.analyze_payment(CheckPaymentRequest(**sc_a))
    assert res_a.risk_score < 35.0
    assert res_a.cross_validation.status in ["MATCH", "UNAVAILABLE"]
    
    sc_b = payment_forensics_service.get_scenario_by_id("SCENARIO_B_QR_AMOUNT_MISMATCH")
    res_b = payment_forensics_service.analyze_payment(CheckPaymentRequest(**sc_b))
    assert res_b.risk_score >= 82.0
    assert res_b.cross_validation.items["amount"].status == "MISMATCH"
    
    sc_c = payment_forensics_service.get_scenario_by_id("SCENARIO_C_MERCHANT_VPA_MISMATCH")
    res_c = payment_forensics_service.analyze_payment(CheckPaymentRequest(**sc_c))
    assert res_c.risk_score >= 70.0
    assert any("recipient" in s.name.lower() or "payee" in s.name.lower() or "identity" in s.name.lower() for s in res_c.risk_signals)
    
    sc_d = payment_forensics_service.get_scenario_by_id("SCENARIO_D_SUSPICIOUS_PAYMENT_LINK")
    res_d = payment_forensics_service.analyze_payment(CheckPaymentRequest(**sc_d))
    assert res_d.risk_score >= 65.0
    
    sc_e = payment_forensics_service.get_scenario_by_id("SCENARIO_E_TRANSACTION_ANOMALY")
    res_e = payment_forensics_service.analyze_payment(CheckPaymentRequest(**sc_e))
    assert res_e.risk_score > 40.0

def test_gemini_strict_boundary_fallback():
    """Verify that Gemini explanation fallback is deterministic and marked with valid analysis status."""
    req = CheckPaymentRequest(
        input_type="SCREENSHOT",
        payload="Paid ₹500.00 to grocery@upi",
        transaction_context={"amount": 500.0, "recipient_vpa": "grocery@upi"}
    )
    res = payment_forensics_service.analyze_payment(req)
    assert res.evidence_verification is not None
    assert res.evidence_verification.provider in ["Gemini Multimodal", "Gemini 1.5 Flash (Fallback)", "Heuristic Local Fallback"]
    assert res.evidence_verification.analysis_status in ["COMPLETED", "FALLBACK", "UNAVAILABLE"]
