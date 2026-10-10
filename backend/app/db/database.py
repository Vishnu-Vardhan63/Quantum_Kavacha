import os
import json
import time
import sqlite3
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from backend.app.core.config import settings

logger = logging.getLogger("quantum_kavacha.db")

# SQLite fallback path
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
DB_PATH = os.path.join(DB_DIR, "quantum_kavacha.db")

# Global PyMongo client & database singleton
_mongo_client = None
_mongo_db = None
_mongo_init_attempted = False


def get_mongo_client():
    """
    Returns active PyMongo MongoClient instance or None if not configured/failed.
    Reuses connection pool; does not leak credentials in logs or exceptions.
    """
    global _mongo_client, _mongo_db, _mongo_init_attempted
    if _mongo_client is not None:
        return _mongo_client
    if _mongo_init_attempted:
        return None

    mongo_uri = getattr(settings, "MONGODB_URI", "")
    if not mongo_uri:
        _mongo_init_attempted = True
        return None

    try:
        import pymongo
        # Connect with safe timeout
        _mongo_client = pymongo.MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=2000,
            appname="QuantumKavacha"
        )
        # Test connection ping
        _mongo_client.admin.command("ping")
        db_name = getattr(settings, "MONGODB_DATABASE", "quantum_kavacha")
        _mongo_db = _mongo_client[db_name]
        logger.info("Successfully connected to MongoDB Atlas cluster.")
        return _mongo_client
    except Exception as e:
        logger.warning(f"MongoDB Atlas connection unready or unreachable: {type(e).__name__}. Falling back to SQLite.")
        _mongo_client = None
        _mongo_db = None
        _mongo_init_attempted = True
        return None


def get_mongo_db():
    """Returns PyMongo Database object if available, else None."""
    global _mongo_db
    if _mongo_db is not None:
        return _mongo_db
    client = get_mongo_client()
    if client:
        db_name = getattr(settings, "MONGODB_DATABASE", "quantum_kavacha")
        _mongo_db = client[db_name]
        return _mongo_db
    return None


def init_db(db_path: str = DB_PATH):
    """
    Initializes both MongoDB Atlas collections/indexes and local SQLite fallback.
    Ensures safe dual-read/write and index creation.
    """
    # 1. Initialize SQLite schema
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with get_db_connection(db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                txn_id TEXT PRIMARY KEY,
                user_id TEXT,
                amount REAL,
                merchant_id TEXT,
                device_id TEXT,
                ip TEXT,
                timestamp REAL,
                risk_score REAL,
                decision TEXT,
                risk_level TEXT,
                is_simulated INTEGER DEFAULT 0,
                prediction_data TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS investigation_cases (
                case_id TEXT PRIMARY KEY,
                status TEXT,
                created_at REAL,
                updated_at REAL,
                source TEXT,
                case_data TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT NOT NULL,
                disabled INTEGER DEFAULT 0,
                created_at REAL NOT NULL
            )
        ''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_timestamp ON transactions(timestamp DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_user ON transactions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_case_created ON investigation_cases(created_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_case_status ON investigation_cases(status)")
        conn.commit()

    # 2. Initialize MongoDB Atlas collections & indexes if connected
    db = get_mongo_db()
    if db is not None:
        try:
            import pymongo
            # Collections: investigation_cases, transactions, users, audit_logs
            db.investigation_cases.create_index([("case_id", pymongo.ASCENDING)], unique=True)
            db.investigation_cases.create_index([("created_at", pymongo.DESCENDING)])
            db.investigation_cases.create_index([("status", pymongo.ASCENDING)])

            db.transactions.create_index([("txn_id", pymongo.ASCENDING)], unique=True)
            db.transactions.create_index([("timestamp", pymongo.DESCENDING)])
            db.transactions.create_index([("user_id", pymongo.ASCENDING)])

            db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
            db.audit_logs.create_index([("timestamp", pymongo.DESCENDING)])
            logger.info("MongoDB Atlas indexes verified and initialized.")

            # Run initial background migration from SQLite if Mongo collection is empty
            migrate_sqlite_to_mongo(db_path)
        except Exception as e:
            logger.warning(f"Notice during MongoDB index initialization: {type(e).__name__}")


def migrate_sqlite_to_mongo(db_path: str = DB_PATH):
    """
    Safely migrates existing records from SQLite into MongoDB Atlas without deletion.
    Idempotent: uses upsert on unique keys.
    """
    db = get_mongo_db()
    if db is None or not os.path.exists(db_path):
        return

    try:
        with sqlite3.connect(db_path) as s_conn:
            s_conn.row_factory = sqlite3.Row

            # Migrate users
            user_rows = s_conn.execute("SELECT * FROM users").fetchall()
            for r in user_rows:
                db.users.update_one(
                    {"username": r["username"]},
                    {"$set": {
                        "username": r["username"],
                        "password_hash": r["password_hash"],
                        "role": r["role"],
                        "full_name": r["full_name"],
                        "disabled": bool(r["disabled"]),
                        "created_at": r["created_at"],
                        "migrated_at": time.time()
                    }},
                    upsert=True
                )

            # Migrate investigation cases
            case_rows = s_conn.execute("SELECT * FROM investigation_cases").fetchall()
            for r in case_rows:
                try:
                    c_data = json.loads(r["case_data"])
                except Exception:
                    c_data = {}
                db.investigation_cases.update_one(
                    {"case_id": r["case_id"]},
                    {"$set": {
                        "case_id": r["case_id"],
                        "status": r["status"],
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                        "source": r["source"],
                        "case_data": r["case_data"],
                        "parsed": c_data,
                        "migrated_at": time.time()
                    }},
                    upsert=True
                )

            # Migrate transactions
            txn_rows = s_conn.execute("SELECT * FROM transactions").fetchall()
            for r in txn_rows:
                try:
                    p_data = json.loads(r["prediction_data"])
                except Exception:
                    p_data = {}
                db.transactions.update_one(
                    {"txn_id": r["txn_id"]},
                    {"$set": {
                        "txn_id": r["txn_id"],
                        "user_id": r["user_id"],
                        "amount": r["amount"],
                        "merchant_id": r["merchant_id"],
                        "device_id": r["device_id"],
                        "ip": r["ip"],
                        "timestamp": r["timestamp"],
                        "risk_score": r["risk_score"],
                        "decision": r["decision"],
                        "risk_level": r["risk_level"],
                        "is_simulated": bool(r["is_simulated"]),
                        "prediction_data": r["prediction_data"],
                        "parsed": p_data,
                        "migrated_at": time.time()
                    }},
                    upsert=True
                )
            logger.info(f"Synchronized {len(case_rows)} cases, {len(user_rows)} users, and {len(txn_rows)} transactions to MongoDB Atlas.")
    except Exception as e:
        logger.warning(f"SQLite -> MongoDB synchronization notice: {type(e).__name__}")


def check_mongo_health() -> Dict[str, Any]:
    """
    Safe health check for MongoDB Atlas connectivity.
    Never exposes credentials, secrets, host IP, or raw URI in the response.
    """
    mongo_uri = getattr(settings, "MONGODB_URI", "")
    if not mongo_uri:
        return {
            "configured": False,
            "connected": False,
            "status": "NOT_CONFIGURED",
            "driver": "pymongo",
            "message": "MONGODB_URI environment variable is not set."
        }

    t0 = time.perf_counter()
    try:
        db = get_mongo_db()
        if db is None:
            return {
                "configured": True,
                "connected": False,
                "status": "CONNECTION_FAILED",
                "driver": "pymongo",
                "message": "Unable to establish active cluster session."
            }
        # Run cluster ping
        db.client.admin.command("ping")
        latency_ms = (time.perf_counter() - t0) * 1000.0

        # Safe collection counts
        cases_count = db.investigation_cases.count_documents({})
        txns_count = db.transactions.count_documents({})
        users_count = db.users.count_documents({})

        return {
            "configured": True,
            "connected": True,
            "status": "CONNECTED",
            "driver": "pymongo",
            "database": getattr(settings, "MONGODB_DATABASE", "quantum_kavacha"),
            "ping_latency_ms": round(latency_ms, 2),
            "collection_counts": {
                "investigation_cases": cases_count,
                "transactions": txns_count,
                "users": users_count
            }
        }
    except Exception as e:
        return {
            "configured": True,
            "connected": False,
            "status": "ERROR",
            "driver": "pymongo",
            "error_type": type(e).__name__,
            "message": "Connection verification encountered an error."
        }


# =============================================================================
# Higher-Level Dual Persistence Layer (MongoDB Atlas Primary + SQLite Local)
# =============================================================================

class MongoPersistence:
    """Helper methods for dual-persisting cases, users, and transactions."""

    @staticmethod
    def save_case(case_id: str, status: str, created_at: float, updated_at: float, source: str, case_json: str):
        # 1. MongoDB Atlas
        db = get_mongo_db()
        if db is not None:
            try:
                parsed = json.loads(case_json) if isinstance(case_json, str) else case_json
                db.investigation_cases.update_one(
                    {"case_id": case_id},
                    {"$set": {
                        "case_id": case_id,
                        "status": status,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "source": source,
                        "case_data": case_json,
                        "parsed": parsed,
                        "synced_at": time.time()
                    }},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"MongoDB save_case error: {type(e).__name__}")

        # 2. Local SQLite
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO investigation_cases (case_id, status, created_at, updated_at, source, case_data) VALUES (?, ?, ?, ?, ?, ?)",
                    (case_id, status, created_at, updated_at, source, case_json)
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"SQLite save_case error: {type(e).__name__}")

    @staticmethod
    def get_case(case_id: str) -> Optional[str]:
        # Try Mongo first
        db = get_mongo_db()
        if db is not None:
            try:
                doc = db.investigation_cases.find_one({"case_id": case_id})
                if doc and "case_data" in doc:
                    return doc["case_data"]
            except Exception:
                pass

        # Fallback to SQLite
        try:
            with get_db_connection() as conn:
                row = conn.execute("SELECT case_data FROM investigation_cases WHERE case_id = ?", (case_id,)).fetchone()
                if row:
                    return row["case_data"]
        except Exception:
            pass
        return None

    @staticmethod
    def list_all_cases() -> List[str]:
        # Try Mongo first
        db = get_mongo_db()
        if db is not None:
            try:
                docs = list(db.investigation_cases.find({}, {"case_data": 1}).sort("created_at", -1))
                if docs:
                    return [d["case_data"] for d in docs if "case_data" in d]
            except Exception:
                pass

        # Fallback to SQLite
        try:
            with get_db_connection() as conn:
                rows = conn.execute("SELECT case_data FROM investigation_cases ORDER BY created_at DESC").fetchall()
                return [r["case_data"] for r in rows]
        except Exception:
            return []

    @staticmethod
    def delete_all_cases():
        db = get_mongo_db()
        if db is not None:
            try:
                db.investigation_cases.delete_many({})
            except Exception:
                pass
        try:
            with get_db_connection() as conn:
                conn.execute("DELETE FROM investigation_cases")
                conn.commit()
        except Exception:
            pass

    @staticmethod
    def save_transaction(txn_id: str, user_id: str, amount: float, merchant_id: str, device_id: str, ip: str, timestamp: float, risk_score: float, decision: str, risk_level: str, pred_json: str):
        db = get_mongo_db()
        if db is not None:
            try:
                parsed = json.loads(pred_json) if isinstance(pred_json, str) else pred_json
                db.transactions.update_one(
                    {"txn_id": txn_id},
                    {"$set": {
                        "txn_id": txn_id,
                        "user_id": user_id,
                        "amount": amount,
                        "merchant_id": merchant_id,
                        "device_id": device_id,
                        "ip": ip,
                        "timestamp": timestamp,
                        "risk_score": risk_score,
                        "decision": decision,
                        "risk_level": risk_level,
                        "prediction_data": pred_json,
                        "parsed": parsed,
                        "synced_at": time.time()
                    }},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"MongoDB save_transaction error: {type(e).__name__}")

        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO transactions (txn_id, user_id, amount, merchant_id, device_id, ip, timestamp, risk_score, decision, risk_level, prediction_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (txn_id, user_id, amount, merchant_id, device_id, ip, timestamp, risk_score, decision, risk_level, pred_json)
                )
                conn.commit()
        except Exception:
            pass


@contextmanager
def get_db_connection(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
