"""Simple tests for HTTP API endpoints"""


def test_root_endpoint(client):
    """Test root endpoint returns HTML page"""
    response = client.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.headers.get('content-type', '')


def test_notify_endpoint(client):
    """Test notify endpoint sends notification"""
    response = client.post('/notify', params={'message': 'Test message'})
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'
    assert 'message' in data


def test_notify_endpoint_default_message(client):
    """Test notify endpoint with default message"""
    response = client.post('/notify')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'
