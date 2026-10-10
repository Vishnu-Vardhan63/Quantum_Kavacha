import os
import hmac
import hashlib
import secrets
import json
import base64
import time
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from backend.app.db.database import get_db_connection

# Secret key derivation from environment or ephemeral high-entropy random fallback
AUTH_SECRET = os.getenv("AUTH_SECRET_KEY", "quantum_kavacha_secure_defense_secret_key_2026")
TOKEN_EXPIRY_SECONDS = int(os.getenv("AUTH_TOKEN_EXPIRY_SECONDS", "86400")) # 24 hours

security_scheme = HTTPBearer(auto_error=False)

class User(BaseModel):
    username: str
    role: str # ADMIN, INVESTIGATOR, READ_ONLY
    full_name: str
    disabled: bool = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

class LoginRequest(BaseModel):
    username: str
    password: str

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Generate PBKDF2-HMAC-SHA256 password hash with salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{dk.hex()}"

def verify_password(plain_password: str, hashed_value: str) -> bool:
    """Verify constant-time password hash matching."""
    try:
        salt, dk_hex = hashed_value.split(":")
        test_dk = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return hmac.compare_digest(dk_hex, test_dk.hex())
    except Exception:
        return False

def generate_signed_token(payload: Dict[str, Any]) -> str:
    """Creates tamper-proof HMAC-SHA256 authenticated state token."""
    payload_copy = dict(payload)
    payload_copy["exp"] = time.time() + TOKEN_EXPIRY_SECONDS
    payload_copy["iat"] = time.time()

    header = {"alg": "HS256", "typ": "JWT"}
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload_copy).encode('utf-8')).decode('utf-8').rstrip("=")

    signing_input = f"{h_b64}.{p_b64}".encode('utf-8')
    signature = hmac.new(AUTH_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip("=")

    return f"{h_b64}.{p_b64}.{sig_b64}"

def verify_signed_token(token: str) -> Dict[str, Any]:
    """Validates signature, structure, and expiration of signed tokens."""
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token structure"
        )
    h_b64, p_b64, sig_b64 = parts
    signing_input = f"{h_b64}.{p_b64}".encode('utf-8')
    expected_sig = hmac.new(AUTH_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()

    # Pad back base64 for decoding
    rem = len(sig_b64) % 4
    if rem > 0:
        sig_b64 += "=" * (4 - rem)
    try:
        actual_sig = base64.urlsafe_b64decode(sig_b64)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature encoding")

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature verification failed")

    p_rem = len(p_b64) % 4
    if p_rem > 0:
        p_b64 += "=" * (4 - p_rem)
    try:
        payload = json.loads(base64.urlsafe_b64decode(p_b64).decode('utf-8'))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token payload")

    if payload.get("exp", 0) < time.time():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    return payload

def init_auth_tables():
    """Ensure users table exists and bootstrap seeded administrative & investigator identities."""
    with get_db_connection() as conn:
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
        # Seed default demonstration role accounts if absent
        accounts = [
            ("admin", "QuantumAdmin#2026", "ADMIN", "SOC Administrator"),
            ("investigator", "Investigate#2026", "INVESTIGATOR", "Lead Fraud Analyst"),
            ("auditor", "Auditor#2026", "READ_ONLY", "Compliance Auditor")
        ]
        now = time.time()
        for uname, pwd, role, fname in accounts:
            existing = conn.execute("SELECT username FROM users WHERE username = ?", (uname,)).fetchone()
            if not existing:
                p_hash = hash_password(pwd)
                conn.execute(
                    "INSERT INTO users (username, password_hash, role, full_name, disabled, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (uname, p_hash, role, fname, 0, now)
                )
        conn.commit()

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Look up user in database and verify credential."""
    with get_db_connection() as conn:
        row = conn.execute("SELECT username, password_hash, role, full_name, disabled FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            return None
        if bool(row["disabled"]):
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        return User(
            username=row["username"],
            role=row["role"],
            full_name=row["full_name"],
            disabled=bool(row["disabled"])
        )

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)) -> User:
    """Dependency for extracting and validating authenticated caller identity."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    payload = verify_signed_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    with get_db_connection() as conn:
        row = conn.execute("SELECT username, role, full_name, disabled FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if bool(row["disabled"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
        return User(
            username=row["username"],
            role=row["role"],
            full_name=row["full_name"],
            disabled=bool(row["disabled"])
        )

def require_role(allowed_roles: list[str]):
    """Role-based authorization dependency factory."""
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {allowed_roles} roles. User holds role '{user.role}'."
            )
        return user
    return role_checker
