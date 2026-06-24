import os
import shutil
import asyncio
from pathlib import Path

from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

# FastAPI_MongoDB optional imports (may not exist in local Django env)
try:
    from FastAPI_MongoDB.SRC.Util import RedisServices, DBmodule, JsonOperations, GeneralFunctions  # type: ignore
except Exception:  # pragma: no cover
    RedisServices = DBmodule = JsonOperations = GeneralFunctions = None  # type: ignore


def _envelope(payload: dict):
    return Response(payload)


class NASHealthView(APIView):
    def get(self, request):
        return Response({"status": "success", "code": 200, "Details": {"data": "NAS wired"}})

class UploadFileView(APIView):
    """Port of FastAPI NAS UploadFile endpoint.

    Supports:
    - Local mode: copy2 into assets upload directory
    - NAS mode: if SynologyClient is available in FastAPI_MongoDB, delegate upload there
    """

    def post(self, request):
        try:
            # Expected input keys (camelCase as in FastAPI):
            # FilePath, DestPath, Mode (optional)
            payload = request.data or {}
            file_path = payload.get("FilePath") or payload.get("file_path")
            dest_path = payload.get("DestPath") or payload.get("dest_path")
            mode = payload.get("Mode") or payload.get("mode") or "local"

            if not file_path or not dest_path:
                return _envelope(
                    {
                        "status": "error",
                        "code": 400,
                        "message": "FilePath and DestPath are required",
                        "Details": {},
                    }
                )

            file_path = str(file_path)
            dest_path = str(dest_path)

            if not os.path.exists(file_path):
                return _envelope(
                    {"status": "error", "code": 404, "message": "File not found", "Details": {"FilePath": file_path}}
                )

            # If NAS mode and FastAPI Synology client exists, try it.
            if str(mode).lower() in {"nas", "synology"}:
                try:
                    # Keep import inside to avoid breaking Django dev if NAS deps are absent.
                    from FastAPI_MongoDB.Modules.NAS.router import SynologyClient  # type: ignore

                    client = SynologyClient()
                    result = client.upload_file(file_path=file_path, dest_path=dest_path)
                    return _envelope(
                        {
                            "status": "success",
                            "code": 200,
                            "message": "File uploaded successfully (NAS mode)",
                            "Details": {"data": result},
                        }
                    )
                except Exception:
                    # Fallback to local copy
                    pass

            # Local mode
            dest_abs = Path(dest_path)
            dest_abs.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, str(dest_abs))
            return _envelope(
                {
                    "status": "success",
                    "code": 200,
                    "message": "File uploaded successfully (Local mode)",
                    "Details": {"data": {"FilePath": file_path, "DestPath": dest_path}},
                }
            )
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})



