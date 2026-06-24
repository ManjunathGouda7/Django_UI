"""DRF endpoints that delegate into the existing FastAPI MongoDB implementation.

NOTE:
- This is a bridge to keep the behavior identical while we port modules fully.
- As FastAPI uses APIRouter functions and Pydantic models, the delegate layer adapts
  request inputs and returns the same response envelope.

The goal of this file is to get endpoints working quickly under Django.
"""

from __future__ import annotations

from typing import Any, Optional, List

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class PassThroughAPIView(APIView):
    """Simple pass-through base class.

    Child classes must set `handler_path` to an async callable in FastAPI.
    """

    handler_path: Optional[str] = None

    async def get_handler(self):
        if not self.handler_path:
            raise RuntimeError("handler_path not set")
        module_path, func_name = self.handler_path.rsplit(".", 1)
        # Local import to avoid importing heavy modules at Django start.
        mod = __import__(module_path, fromlist=[func_name])
        return getattr(mod, func_name)

    async def _call(self, handler, request: Request, **kwargs):
        result = await handler(**kwargs)
        # FastAPI handlers already return python dict envelopes.
        return result

    async def get(self, request: Request, *args, **kwargs):
        handler = await self.get_handler()
        payload = await self._call(handler, request, **kwargs)
        return Response(payload)

    async def post(self, request: Request, *args, **kwargs):
        handler = await self.get_handler()
        # Forward JSON body into handler kwargs when shapes match.
        body = request.data if hasattr(request, "data") else {}
        payload = await self._call(handler, request, **body, **kwargs)
        return Response(payload)

    async def put(self, request: Request, *args, **kwargs):
        handler = await self.get_handler()
        body = request.data if hasattr(request, "data") else {}
        payload = await self._call(handler, request, **body, **kwargs)
        return Response(payload)

    async def delete(self, request: Request, *args, **kwargs):
        handler = await self.get_handler()
        # Prefer query params for deletes
        payload = await self._call(handler, request, **kwargs)
        return Response(payload)

