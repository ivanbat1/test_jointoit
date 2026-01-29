import asyncio
import logging
import time

from websocket.core.settings import CHECK_INTERVAL, SHUTDOWN_TIMEOUT
from websocket.services.manager import AbstractConnectionManager

logger = logging.getLogger(__name__)


async def graceful_shutdown(manager: AbstractConnectionManager):
    """Handle graceful shutdown for this worker process"""
    logger.info('Graceful shutdown initiated')
    manager.initiate_shutdown()

    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        remaining = SHUTDOWN_TIMEOUT - elapsed
        connection_count = manager.get_connection_count()

        logger.info(f'Shutdown in progress: {connection_count} active connections, {remaining:.1f} seconds remaining')

        # Check if all connections are closed
        if connection_count == 0:
            logger.info('All connections closed. Worker ready to shutdown.')
            break

        # Check if timeout exceeded
        if elapsed >= SHUTDOWN_TIMEOUT:
            logger.warning(
                f'Shutdown timeout ({SHUTDOWN_TIMEOUT}s) exceeded. '
                f'Force shutting down with {connection_count} active connections.'
            )
            async with manager.async_lock:
                connections_to_close = list(manager.active_connections)
            for connection in connections_to_close:
                try:
                    await connection.close()
                except Exception as e:
                    logger.warning(f'Error closing connection: {e}')
                await manager.disconnect(connection)
            break

        await asyncio.sleep(CHECK_INTERVAL)

    logger.info('Graceful shutdown complete')
