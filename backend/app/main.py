import time
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.utils.preprocessing import probe_system_capabilities

from backend.app.api.routes import (
    transactions, fraud, quantum, models, analytics, simulation,
    drift, attacks, copilot, explainability, check_payment, investigation,
    graph, evidence, device_trust, adaptive_mfa, auth, ingest
)
from backend.app.core.auth import init_auth_tables

# Initialize core authentication store
init_auth_tables()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Quantum-Enhanced Digital Payment Fraud Intelligence System",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register API Routers
app.include_router(auth.router)
app.include_router(ingest.router)
app.include_router(check_payment.router)
app.include_router(evidence.router)
app.include_router(device_trust.router)
app.include_router(adaptive_mfa.router)
app.include_router(investigation.router)
app.include_router(graph.router)
app.include_router(transactions.router)
app.include_router(fraud.router)
app.include_router(quantum.router)
app.include_router(models.router)
app.include_router(analytics.router)
app.include_router(simulation.router)
app.include_router(drift.router)
app.include_router(attacks.router)
app.include_router(copilot.router)
app.include_router(explainability.router)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response

@app.get("/api/health", summary="System Health & Capability Probe")
async def health_check():
    capabilities = probe_system_capabilities()
    
    # Core quantum engine status
    qiskit_status = capabilities.get("qiskit", {}).get("status", "UNAVAILABLE")
    qml_status = capabilities.get("qiskit_machine_learning", {}).get("status", "UNAVAILABLE")
    quantum_engine_online = (qiskit_status == "AVAILABLE") and (qml_status == "AVAILABLE")
    
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "quantum_engine": {
            "online": quantum_engine_online,
            "mode": settings.QUANTUM_MODE_DEFAULT,
            "hardware_available": bool(settings.IBM_QUANTUM_TOKEN)
        },
        "capabilities": capabilities
    }

@app.get("/", summary="Root Endpoint")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "health": "/api/health"
    }
