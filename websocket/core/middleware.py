import logging
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID', uuid.uuid4().hex)

        logging.LoggerAdapter(logger, extra={'request_id': request_id})

        response = await call_next(request)
        response.headers['X-Request-ID'] = request_id
        return response
