# grl_api/api/pfo_urls.py
from django.urls import path
from .views_pfo import (
    GetPFODataView,
    ExecutePFOTestView,
    GetPFOStatsView,
    ExportPFOReportView,
    PFOHealthView,
    PFOFilterOptionsView
)

urlpatterns = [
    path('health/', PFOHealthView.as_view(), name='pfo_health'),
    path('GetData/', GetPFODataView.as_view(), name='pfo_get_data'),
    path('ExecuteTest/', ExecutePFOTestView.as_view(), name='pfo_execute_test'),
    path('GetStats/', GetPFOStatsView.as_view(), name='pfo_get_stats'),
    path('ExportReport/', ExportPFOReportView.as_view(), name='pfo_export_report'),
    path('filter-options/', PFOFilterOptionsView.as_view(), name='pfo_filter_options'),
]