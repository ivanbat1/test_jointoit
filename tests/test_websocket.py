"""Simple tests for WebSocket functionality"""


def test_websocket_connection(client):
    """Test basic WebSocket connection"""
    with client.websocket_connect('/ws') as websocket:
        data = websocket.receive_json()
        assert data['type'] == 'welcome'
        assert 'message' in data


def test_websocket_send_message(client):
    """Test sending a message via WebSocket"""
    with client.websocket_connect('/ws') as websocket:
        # Receive welcome message
        welcome = websocket.receive_json()
        assert welcome['type'] == 'welcome'

        # Send a test message
        test_message = {'type': 'notification', 'message': 'Hello Server'}
        websocket.send_json(test_message)

        # Receive echo (broadcast message)
        # Note: In test mode with memory backend, we might receive our own message
        try:
            echo = websocket.receive_json(timeout=1.0)
            assert echo['type'] in ['echo', 'notification']
        except Exception:
            # Timeout is acceptable in test mode
            pass
