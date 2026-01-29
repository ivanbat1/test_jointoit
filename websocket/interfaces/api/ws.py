import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from websocket.interfaces.api.deps import get_uow, get_ws_manager
from websocket.services.manager import AbstractConnectionManager
from websocket.services.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket('/ws')
async def websocket_endpoint(
    websocket: WebSocket,
    manager: AbstractConnectionManager = Depends(get_ws_manager),
    unit_of_work: AbstractUnitOfWork = Depends(get_uow),
):
    # Reject new connections if shutdown is initiated
    if manager.is_shutdown_initiated():
        await websocket.close(code=1001, reason='Server is shutting down')
        return

    connection_id = await manager.connect(websocket)

    try:
        async with unit_of_work(
            manager=manager,
            websocket=websocket,
            connection_id=connection_id,
        ) as uow:
            await uow.run()

    except WebSocketDisconnect:
        logger.info(f'Client {connection_id} disconnected normally')
    except Exception as e:
        logger.error(f'Error in WebSocket connection {connection_id}: {e}')
    finally:
        await manager.disconnect(websocket)
