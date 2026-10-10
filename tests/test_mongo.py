import pytest
import time
from backend.app.db.database import (
    get_mongo_client,
    get_mongo_db,
    check_mongo_health,
    MongoPersistence,
    init_db
)

def test_mongo_health_check_safe():
    """Verify MongoDB Atlas health probe reports connected status without credential leaks."""
    status = check_mongo_health()
    assert isinstance(status, dict)
    assert status.get("configured") is True
    assert status.get("connected") is True
    assert status.get("status") == "CONNECTED"
    assert status.get("database") == "quantum_kavacha"
    assert status.get("driver") == "pymongo"

    # Assert secrets and sensitive connection credentials are never disclosed
    status_str = str(status)
    assert "mongodb+srv://" not in status_str
    assert "password" not in status_str.lower() or status.get("password") is None
    assert "23hp1a4263_db_user" not in status_str

def test_mongo_roundtrip_persistence():
    """Verify creating, querying, and updating a test record in MongoDB Atlas."""
    test_id = f"TEST-CASE-{int(time.time() * 1000)}"
    now = time.time()
    test_payload = {
        "case_id": test_id,
        "status": "UNDER_REVIEW",
        "created_at": now,
        "updated_at": now,
        "source": "UNIT_TEST",
        "test_marker": True
    }

    # 1. Save case
    MongoPersistence.save_case(
        case_id=test_id,
        status="UNDER_REVIEW",
        created_at=now,
        updated_at=now,
        source="UNIT_TEST",
        case_json=pytest.importorskip("json").dumps(test_payload)
    )

    # 2. Retrieve case
    retrieved_raw = MongoPersistence.get_case(test_id)
    assert retrieved_raw is not None
    import json
    data = json.loads(retrieved_raw)
    assert data["case_id"] == test_id
    assert data["test_marker"] is True

    # 3. Clean up test record from Atlas
    db = get_mongo_db()
    if db is not None:
        db.investigation_cases.delete_one({"case_id": test_id})
