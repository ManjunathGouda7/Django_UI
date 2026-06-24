# grl_api/api/urls.py
from django.urls import path, include
from .views import HealthCheckView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='grl_api_health'),
    path('UIChecks/', include('grl_api.api.uichecks_urls')),
    path('UIRunner/', include('grl_api.api.ui_runner_urls')),
    path('NAS/', include('grl_api.api.nas_urls')),
    path('PFO/', include('grl_api.api.pfo_urls')), 
    path('chatbot/', include('grl_api.api.chatbot_urls')),
    path('IssuesAndTasksTracking/', include('grl_api.api.IssuesAndTasksTracking_urls')),
]