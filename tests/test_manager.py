"""Simple tests for connection manager"""

import pytest
from broadcaster import Broadcast

from websocket.services.manager import ConnectionTracker


class MockWebSocket:
    """Mock WebSocket for testing"""

    def __init__(self):
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def close(self):
        self.closed = True


@pytest.fixture
async def test_manager():
    """Create a test connection manager with memory broadcaster"""

    class TestConnectionTracker(ConnectionTracker):
        def get_broadcaster(self):
            return Broadcast('memory://')

    manager = TestConnectionTracker()
    try:
        await manager.broadcaster.connect()
        yield manager
    finally:
        # Ensure cleanup happens even if test fails
        try:
            await manager.broadcaster.disconnect()
        except Exception:
            # Ignore errors during cleanup
            pass


@pytest.mark.asyncio
async def test_manager_connection_count(test_manager):
    """Test connection count tracking"""
    assert test_manager.get_connection_count() == 0

    mock_ws = MockWebSocket()
    connection_id = await test_manager.connect(mock_ws)

    assert test_manager.get_connection_count() == 1
    assert connection_id is not None

    await test_manager.disconnect(mock_ws)
    assert test_manager.get_connection_count() == 0


@pytest.mark.asyncio
async def test_manager_shutdown_state(test_manager):
    """Test shutdown state management"""
    assert not test_manager.is_shutdown_initiated()
    assert test_manager.get_shutdown_elapsed_time() == 0.0

    test_manager.initiate_shutdown()
    assert test_manager.is_shutdown_initiated()
    assert test_manager.get_shutdown_elapsed_time() > 0
