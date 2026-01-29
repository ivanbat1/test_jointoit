import abc
import asyncio
import json
import logging
import time
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from websocket.domain.entities import MessageType
from websocket.services.manager import AbstractConnectionManager

logger = logging.getLogger(__name__)


class AbstractUnitOfWork(abc.ABC):
    def __init__(
        self,
        connection_id: str,
        manager: AbstractConnectionManager,
        websocket: WebSocket,
    ):
        self.manager = manager
        self.websocket = websocket
        self.connection_id = connection_id
        self._subscriber_context = None
        self._subscriber = None
        self.listen_task = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    @abc.abstractmethod
    async def run(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def rollback(self):
        raise NotImplementedError


class BroadcastUnitOfWork(AbstractUnitOfWork):
    async def __aenter__(self) -> AbstractUnitOfWork:
        self._is_active = True

        await self.websocket.send_json(
            {'type': MessageType.welcome, 'message': 'Connected to WebSocket server', 'timestamp': time.time()}
        )

        self._subscriber_context = self.manager.broadcaster.subscribe(channel='notifications')
        self._subscriber = await self._subscriber_context.__aenter__()

        self.listen_task = asyncio.create_task(self.listen_for_messages())
        return self

    async def listen_for_messages(self):
        """Listen for messages from broadcaster and forward to WebSocket"""
        try:
            async for event in self._subscriber:
                if not self._is_active:
                    break
                try:
                    # Parse the broadcast message from Redis
                    try:
                        message_data = json.loads(event.message) if isinstance(event.message, str) else event.message
                    except json.JSONDecodeError:
                        message_data = {'text': event.message} if isinstance(event.message, str) else event.message

                    # Forward the message to this WebSocket client
                    # The message_data contains the full broadcast message structure
                    # Send it as echo type so client can handle it
                    await self.websocket.send_json(
                        {'type': MessageType.echo, 'timestamp': time.time(), 'message': message_data}
                    )
                except Exception as e:
                    logger.warning(f'Error sending broadcast message to {self.connection_id}: {e}')
        except asyncio.CancelledError:
            logger.debug(f'Broadcast listener cancelled for {self.connection_id}')
        except Exception as e:
            logger.error(f'Error in broadcast listener for {self.connection_id}: {e}')

    async def process_client_message(self, data: str) -> None:
        """Process a message received from the client and broadcast it to all clients"""
        try:
            message = json.loads(data) if isinstance(data, str) else data
            logger.debug(f'Received message from {self.connection_id}: {message}')

            # Extract the actual message content for broadcasting
            if isinstance(message, dict):
                # If message has a 'message' field, use that; otherwise use the whole dict
                broadcast_content = message.get('message', message)
                if isinstance(broadcast_content, dict):
                    # If it's a nested dict, extract the text or message field
                    broadcast_content = (
                        broadcast_content.get('message') or broadcast_content.get('text') or str(broadcast_content)
                    )
            else:
                broadcast_content = str(message)

            # Broadcast the message to all connected clients via Redis
            broadcast_message = {
                'type': MessageType.notification,
                'message': broadcast_content,
                'timestamp': time.time(),
                'source': 'user',
            }
            await self.manager.broadcast(broadcast_message)
        except json.JSONDecodeError:
            # If not JSON, treat as plain text and broadcast
            broadcast_message = {
                'type': MessageType.notification,
                'message': data,
                'timestamp': time.time(),
                'source': 'user',
            }
            await self.manager.broadcast(broadcast_message)
        except Exception as e:
            logger.warning(f'Error processing message from {self.connection_id}: {e}')

    async def receive_client_message(self, timeout: float = 1.0) -> Optional[str]:
        """Receive a message from the client with timeout"""
        try:
            return await asyncio.wait_for(self.websocket.receive_text(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        except WebSocketDisconnect:
            raise

    async def run(self):
        while self._is_active:
            if self.manager.is_shutdown_initiated():
                await self.websocket.send_json(
                    {
                        'type': MessageType.shutdown_notice,
                        'text': 'Server is shutting down. Please disconnect.',
                        'timestamp': time.time(),
                    }
                )
                await asyncio.sleep(0.5)
                break

            try:
                data = await self.receive_client_message(timeout=1.0)
                if data is not None:
                    await self.process_client_message(data)
            except WebSocketDisconnect:
                logger.info(f'Client {self.connection_id} disconnected')
                break
            except Exception as e:
                logger.error(f'Error in message loop for {self.connection_id}: {e}')
                break

    async def rollback(self):
        self._is_active = False

        if self.listen_task:
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass

        if self._subscriber_context:
            await self._subscriber_context.__aexit__(None, None, None)
