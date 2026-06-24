from django.http import HttpResponse
from django.shortcuts import render

def issues_and_tasks_view(request):
    """Render the Issues and Tasks Tracking page"""
    return render(request, 'grl_api/IssuesAndTasksTracking.html')

