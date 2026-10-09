from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.app.services.simulation_service import simulation_service

router = APIRouter(prefix="/api", tags=["Simulation & Streaming"])

@router.post("/simulate/start", summary="Start Live Transaction Simulation")
async def start_simulation():
    simulation_service.start_simulation()
    return {"status": "started", "message": "Live transaction stream active."}

@router.post("/simulate/stop", summary="Stop Live Transaction Simulation")
async def stop_simulation():
    simulation_service.stop_simulation()
    return {"status": "stopped", "message": "Live transaction stream paused."}

@router.get("/stream", summary="SSE Server-Sent Events Stream")
async def stream_transactions():
    return StreamingResponse(
        simulation_service.stream_events(),
        media_type="text/event-stream"
    )
