# grl_api/api/views.py
from django.views import View
from django.http import JsonResponse

# ==================== HEALTH CHECK ====================
class HealthCheckView(View):
    def get(self, request):
        return JsonResponse({"status": "healthy", "timestamp": "2026-01-15"})