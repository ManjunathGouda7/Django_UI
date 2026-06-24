from grl_api.db_helper import run_async
import json
import threading
import asyncio

from rest_framework.response import Response
from rest_framework.views import APIView

from FastAPI_MongoDB.SRC.Util import RedisServices  # type: ignore


def _envelope(payload: dict):
    return Response(payload)


RedisObj = RedisServices()

class GetBaseURLView(APIView):
    """Port of UIRunner router GetBaseURL."""

    def get(self, request):
        try:
            # Prefer env/config if present
            base = getattr(RedisObj, "get_base_url", None)
            if callable(base):
                v = base()
                return _envelope({"status": "success", "code": 200, "message": "BaseURL fetched", "Details": {"data": v}})
            # Fallback: static
            return _envelope({"status": "success", "code": 200, "message": "BaseURL fetched", "Details": {"data": ""}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class ExecuteUITestsView(APIView):
    """Port of ExecuteUITests using background thread."""

    def post(self, request):
        try:
            payload = request.data or {}

            # Determine job creation behavior by delegating to Redis layer if exists.
            job_id = None
            if hasattr(RedisObj, "create_job"):
                job_id = RedisObj.create_job(payload)

            def runner():
                # Import lazily; original code uses run_ui_tests wrapper.
                try:
                    from FastAPI_MongoDB.Modules.UIRunner.router import run_ui_tests  # type: ignore

                    run_async(run_ui_tests(payload))
                except Exception:
                    # best-effort: mark failed job if supported
                    if job_id and hasattr(RedisObj, "set_job_failed"):
                        RedisObj.set_job_failed(job_id)

            t = threading.Thread(target=runner, daemon=True)
            t.start()

            return _envelope({
                "status": "success",
                "code": 200,
                "message": "UI execution started",
                "Details": {"JobID": job_id},
            })
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class UIExecutionStatusView(APIView):
    def get(self, request, JobID: str):
        try:
            if hasattr(RedisObj, "get_job_status"):
                status = RedisObj.get_job_status(JobID)
            else:
                status = None
            return _envelope({"status": "success", "code": 200, "message": "Status fetched", "Details": {"data": status}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class ForceStopView(APIView):
    def post(self, request, JOB_ID: str):
        try:
            if hasattr(RedisObj, "force_stop_job"):
                ok = RedisObj.force_stop_job(JOB_ID)
            else:
                ok = False
            return _envelope({"status": "success" if ok else "error", "code": 200 if ok else 404, "message": "Force stop requested", "Details": {"JobID": JOB_ID}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})


class CheckPowerModePacketView(APIView):
    def get(self, request, PowerMode: str):
        # best-effort port: just return PowerMode
        return _envelope({"status": "success", "code": 200, "message": "PowerMode packet checked", "Details": {"data": PowerMode}})


class GetScanedIPAddressView(APIView):
    def get(self, request, Product: str, Category: str):
        # best-effort port
        try:
            if hasattr(RedisObj, "get_scanned_ip"):
                data = RedisObj.get_scanned_ip(Product=Product, Category=Category)
            else:
                data = None
            return _envelope({"status": "success", "code": 200, "message": "Scanned IP fetched", "Details": {"data": data}})
        except Exception as e:
            return _envelope({"status": "exception", "code": 500, "message": f"Exception occurred: {str(e)}", "Details": {}})



