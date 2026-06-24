from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# Page Views
from UI_Automation_Development.pages.Issue import issues_and_tasks_view
from UI_Automation_Development.pages.MainMenu import main_menu_view
from UI_Automation_Development.pages.UIhome import ui_home_view
from UI_Automation_Development.pages.PFO import pfo_view
from UI_Automation_Development.pages.ChatBot import chatbot_view

def root_view(request):
    return main_menu_view(request)

def api_index_view(request):
    return JsonResponse({
        "status": "success",
        "message": "GRL Automation API v1",
        "endpoints": {
            "health": "/api/v1/health/",
            "UIChecks": "/api/v1/UIChecks/",
            "UIRunner": "/api/v1/UIRunner/",
            "NAS": "/api/v1/NAS/",
            "PFO": "/api/v1/PFO/",
            "ChatBot": "/api/v1/ChatBot/",
            "IssuesAndTasksTracking": "/api/v1/IssuesAndTasksTracking/",
        }
    })

urlpatterns = [
    path('', root_view, name='root'),           
    path('MainMenu/', main_menu_view, name='main_menu'),
    path('UIhome/', ui_home_view, name='ui_home'),
    path('PFO/', pfo_view, name='pfo'),
    path('ChatBot/', chatbot_view, name='chatbot'),
    path('IssuesAndTasksTracking/', issues_and_tasks_view, name='issues_and_tasks'), 

    path('admin/', admin.site.urls),

    # API Base v1
    path('api/v1/', api_index_view, name='api_index'),
    path('api/v1/', include('grl_api.api.urls')),   # ← Your API urls
]