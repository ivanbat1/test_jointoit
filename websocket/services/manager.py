import abc
import asyncio
import json
import logging
import time
from typing import Optional, Set
from uuid import uuid4

from broadcaster import Broadcast
from fastapi import WebSocket

from websocket.core.settings import REDIS_URL

logger = logging.getLogger(__name__)


class AbstractConnectionManager(abc.ABC):
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_ids: dict[WebSocket, str] = {}
        self.async_lock = asyncio.Lock()
        self.shutdown_initiated = False
        self.shutdown_start_time = None
        self.shutdown_start_time = None
        self.broadcaster: Optional[Broadcast] = self.get_broadcaster()

    def get_broadcaster(self) -> Optional[Broadcast]:
        return None

    async def connect(self, websocket: WebSocket) -> str:
        raise NotImplementedError

    async def disconnect(self, websocket: WebSocket) -> None:
        raise NotImplementedError

    async def broadcast(self, message: dict):
        raise NotImplementedError

    def get_connection_count(self) -> int:
        return len(self.active_connections)

    def is_shutdown_initiated(self) -> bool:
        return self.shutdown_initiated

    def initiate_shutdown(self):
        self.shutdown_initiated = True
        self.shutdown_start_time = time.time()
        logger.info('Shutdown initiated for this worker')

    def get_shutdown_elapsed_time(self) -> float:
        """Get elapsed time since shutdown was initiated"""
        if self.shutdown_start_time is None:
            return 0.0
        return time.time() - self.shutdown_start_time


class ConnectionTracker(AbstractConnectionManager):
    def get_broadcaster(self) -> Broadcast:
        return Broadcast(REDIS_URL)

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        connection_id = str(uuid4())
        async with self.async_lock:
            self.active_connections.add(websocket)
            self.connection_ids[websocket] = connection_id
        logger.info(f'Client connected. ID: {connection_id}. Total connections: {len(self.active_connections)}')
        return connection_id

    async def disconnect(self, websocket: WebSocket):
        async with self.async_lock:
            if websocket in self.active_connections:
                connection_id = self.connection_ids.get(websocket, 'unknown')
                self.active_connections.remove(websocket)
                self.connection_ids.pop(websocket, None)
                logger.info(
                    f'Client disconnected. ID: {connection_id}. Total connections: {len(self.active_connections)}'
                )

    async def broadcast(self, message: dict):
        if not self.broadcaster:
            logger.error('Broadcaster not initialized')
            raise RuntimeError('Broadcaster not initialized')

        try:
            await self.broadcaster.publish(channel='notifications', message=json.dumps(message))
            logger.debug(f'Broadcast message published: {message.get("type", "unknown")}')
        except Exception as e:
            logger.error(f'Failed to publish broadcast message: {e}')
            # If broadcaster is not connected, try to connect and retry
            try:
                await self.broadcaster.connect()
                await self.broadcaster.publish(channel='notifications', message=json.dumps(message))
                logger.debug(f'Broadcast message published after reconnect: {message.get("type", "unknown")}')
            except Exception as connect_error:
                logger.error(f'Failed to connect broadcaster and publish: {connect_error}')
                raise
