import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.auth import (
    hash_password, verify_password, generate_signed_token,
    verify_signed_token, authenticate_user, init_auth_tables
)

client = TestClient(app)

def test_password_hashing():
    pwd = "Secr3tPassword!2026"
    hashed = hash_password(pwd)
    assert ":" in hashed
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_token_signing_and_verification():
    payload = {"sub": "investigator", "role": "INVESTIGATOR", "name": "Lead Analyst"}
    token = generate_signed_token(payload)
    assert len(token.split(".")) == 3

    verified = verify_signed_token(token)
    assert verified["sub"] == "investigator"
    assert verified["role"] == "INVESTIGATOR"

def test_login_and_me_endpoint():
    init_auth_tables()
    # Test valid credentials
    res = client.post("/api/auth/login", json={
        "username": "investigator",
        "password": "Investigate#2026"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "INVESTIGATOR"

    token = data["access_token"]

    # Test /api/auth/me with bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "investigator"
    assert me_data["role"] == "INVESTIGATOR"

    # Test unauthenticated access to /api/auth/me
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401

def test_login_invalid_credentials():
    res = client.post("/api/auth/login", json={
        "username": "investigator",
        "password": "WrongPassword123"
    })
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]

def test_token_tampering():
    payload = {"sub": "auditor", "role": "READ_ONLY"}
    token = generate_signed_token(payload)
    parts = token.split(".")
    # Tamper with the payload part
    tampered_token = f"{parts[0]}.eyJzdWIiOiAiYWRtaW4ifQ.{parts[2]}"

    tamper_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert tamper_res.status_code == 401
