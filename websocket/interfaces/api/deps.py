from starlette.requests import HTTPConnection

from websocket.services.manager import AbstractConnectionManager
from websocket.services.unit_of_work import AbstractUnitOfWork


async def get_ws_manager(request: HTTPConnection) -> AbstractConnectionManager:
    return request.app.state.ws_manager


async def get_uow(request: HTTPConnection) -> AbstractUnitOfWork:
    return request.app.state.uow
