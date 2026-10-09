import pytest
from backend.app.services.velocity_engine import velocity_engine

@pytest.fixture(autouse=True)
def reset_velocity_engine_state():
    """
    Ensure the velocity engine starts with a clean slate for every test.
    This prevents shared-state contamination (e.g. accumulating transactions
    for standard mock users) which was causing false positive mule/structuring detections.
    """
    velocity_engine.reset()
    yield
    velocity_engine.reset()
