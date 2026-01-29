import asyncio
import logging
import time

from websocket.core.settings import PERIODIC_NOTIFICATION
from websocket.domain.entities import MessageType
from websocket.services.manager import AbstractConnectionManager

logger = logging.getLogger(__name__)


async def periodic_notifications(manager: AbstractConnectionManager):
    """Send periodic test notifications to all connected clients"""
    try:
        while not manager.is_shutdown_initiated():
            await asyncio.sleep(PERIODIC_NOTIFICATION)
            if manager.is_shutdown_initiated():
                break
            if manager.get_connection_count() > 0:
                message = {
                    'type': MessageType.notification,
                    'message': 'Test notification',
                    'timestamp': time.time(),
                    'source': 'system',
                    'connection_count': manager.get_connection_count(),
                }
                try:
                    await manager.broadcast(message)
                    logger.info(f'Sent periodic notification to {manager.get_connection_count()} clients')
                except Exception as e:
                    logger.error(f'Error broadcasting periodic notification: {e}')
    except asyncio.CancelledError:
        logger.debug('Periodic notifications task cancelled')
    except Exception as e:
        logger.error(f'Error in periodic notifications task: {e}')
