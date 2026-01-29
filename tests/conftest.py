import pytest
from fastapi.testclient import TestClient
from broadcaster import Broadcast

from websocket.main import app
from websocket.services.manager import ConnectionTracker
from websocket.services.unit_of_work import BroadcastUnitOfWork


@pytest.fixture(scope='function')
def client():
    """Create a test client for the FastAPI app."""

    # Use memory backend for tests (no Redis required)
    class TestConnectionTracker(ConnectionTracker):
        def get_broadcaster(self):
            return Broadcast('memory://')

    ws_manager = TestConnectionTracker()
    uow = BroadcastUnitOfWork

    # Set app state
    app.state.ws_manager = ws_manager
    app.state.uow = uow

    # Create test client
    # TestClient manages its own event loop and will handle cleanup
    # We don't manually clean up the broadcaster to avoid interfering with TestClient's event loop
    test_client = TestClient(app)

    yield test_client

    # No cleanup needed - TestClient handles its own event loop lifecycle
    # The broadcaster's background tasks will be cleaned up when TestClient's event loop closes
