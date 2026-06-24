from django.http import HttpResponse
from django.shortcuts import render

def ui_home_view(request):
    return render(request, 'grl_api/UIhome.html')

