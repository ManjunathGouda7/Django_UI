from django.http import HttpResponse
from django.shortcuts import render

def main_menu_view(request):
    """Render the main dashboard"""
    return render(request, 'grl_api/dashboard.html')

