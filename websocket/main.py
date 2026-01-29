import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from websocket.core.logging import configure_logging
from websocket.core.middleware import RequestContextMiddleware
from websocket.interfaces.api.http import router as http_router
from websocket.interfaces.api.ws import router as websocket_router
from websocket.services.manager import AbstractConnectionManager, ConnectionTracker
from websocket.services.notifier import periodic_notifications
from websocket.services.shutdown import graceful_shutdown
from websocket.services.unit_of_work import AbstractUnitOfWork, BroadcastUnitOfWork

configure_logging()


logger = logging.getLogger(__name__)

logger.info(f'Worker process started with')

notification_task = None  # Background task for periodic notifications
shutdown_task = None  # Shutdown task reference


@asynccontextmanager
async def lifespan(app: FastAPI):
    global notification_task, shutdown_task

    ws_manager: AbstractConnectionManager = ConnectionTracker()
    uow: AbstractUnitOfWork = BroadcastUnitOfWork

    app.state.ws_manager = ws_manager
    app.state.uow = uow

    logger.info('Starting WebSocket server...')

    if ws_manager.broadcaster:
        try:
            await ws_manager.broadcaster.connect()
            logger.info('Broadcaster connected')
        except Exception as e:
            logger.error(f'Failed to connect broadcaster: {e}')

    notification_task = asyncio.create_task(periodic_notifications(ws_manager))

    yield

    logger.info('Shutdown signal received. Starting graceful shutdown...')

    if notification_task:
        notification_task.cancel()
        try:
            await notification_task
        except asyncio.CancelledError:
            pass

    shutdown_task = asyncio.create_task(graceful_shutdown(ws_manager))
    await shutdown_task

    if ws_manager.broadcaster:
        try:
            await ws_manager.broadcaster.disconnect()
            logger.info('Broadcaster disconnected')
        except Exception as e:
            logger.error(f'Error disconnecting broadcaster: {e}')

    logger.info('Worker shutdown complete')


app = FastAPI(title='WebSocket Notification Server', lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)
# Routers
app.include_router(websocket_router)
app.include_router(http_router)


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level='info')
