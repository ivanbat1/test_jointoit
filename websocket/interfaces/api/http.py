import time

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from websocket.domain.entities import MessageType
from websocket.interfaces.api.deps import get_ws_manager
from websocket.services.manager import AbstractConnectionManager

router = APIRouter()


templates = Jinja2Templates(directory='websocket/templates')


@router.get('/')
async def get(request: Request):
    """Simple HTML page for testing WebSocket connections"""
    return templates.TemplateResponse(request=request, name='main.html')


@router.post('/notify')
async def send_notification(
    message: str = 'Manual notification', manager: AbstractConnectionManager = Depends(get_ws_manager)
):
    """API endpoint to send a notification to all connected clients"""
    if manager.is_shutdown_initiated():
        return {'status': 'error', 'message': 'Server is shutting down'}

    notification = {'type': MessageType.notification, 'message': message, 'timestamp': time.time(), 'source': 'api'}
    await manager.broadcast(notification)
    return {'status': 'success', 'message': f'Notification sent to {manager.get_connection_count()} clients'}
