import os
import json
import pytest
from backend.app.db.database import get_db_connection, init_db
from backend.app.schemas.transaction import TransactionPayload
from backend.app.services.fraud_engine import fraud_engine
from backend.app.api.routes.transactions import get_transactions

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Use an in-memory or temp DB for tests
    test_db = os.path.abspath("test_qf.db")
    if os.path.exists(test_db):
        os.remove(test_db)
    init_db(test_db)

    # Overwrite DB_PATH in database module just for this run
    from backend.app.db import database
    old_db = database.DB_PATH
    database.DB_PATH = test_db
    yield
    database.DB_PATH = old_db
    if os.path.exists(test_db):
        os.remove(test_db)

def test_db_initialization():
    with get_db_connection() as conn:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t["name"] for t in tables]
        assert "transactions" in table_names
        assert "investigation_cases" in table_names

def test_predict_and_retrieve_transaction():
    import asyncio
    async def _run():
        # Force the app to use our test DB for the actual predict route test
        from backend.app.api.routes.transactions import predict_transaction

        payload = TransactionPayload(
        txn_id="TXN-DB-TEST-001",
        user_id="USR-DB-TEST",
        amount=100.0,
        merchant_id="M1",
        device_id="D1",
        ip="1.1.1.1"
        )

        pred = await predict_transaction(payload)
        assert pred.txn_id == "TXN-DB-TEST-001"

        # Retrieve
        txns = await get_transactions(limit=5)
        assert len(txns) > 0
        assert any(t["txn_id"] == "TXN-DB-TEST-001" for t in txns)
    asyncio.run(_run())

def test_investigation_service_db():
    from backend.app.services.investigation_service import investigation_service
    cases = investigation_service.list_cases()
    assert len(cases) >= 1 # Seed cases should be created

    first_case = cases[0]
    fetched = investigation_service.get_case(first_case.case_id)
    assert fetched.case_id == first_case.case_id
    assert fetched.status == first_case.status
