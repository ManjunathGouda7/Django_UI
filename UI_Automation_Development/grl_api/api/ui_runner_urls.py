from django.urls import path

from .views_ui_runner import (
    GetBaseURLView,
    ExecuteUITestsView,
    UIExecutionStatusView,
    ForceStopView,
    CheckPowerModePacketView,
    GetScanedIPAddressView,
)

urlpatterns = [
    path('GetBaseURL/', GetBaseURLView.as_view(), name='uirunner_get_base_url'),
    path('ExecuteUITest/', ExecuteUITestsView.as_view(), name='uirunner_execute_ui_tests'),
    path('UIExecutionStatus/<str:JobID>/', UIExecutionStatusView.as_view(), name='uirunner_ui_execution_status'),
    path('ForceStop/<str:JOB_ID>/', ForceStopView.as_view(), name='uirunner_force_stop'),
    path('CheckPowerModePacket/<str:PowerMode>/', CheckPowerModePacketView.as_view(), name='uirunner_check_power_mode_packet'),
    path(
        'GetScanedIPAddress/<str:Product>/<str:Category>/',
        GetScanedIPAddressView.as_view(),
        name='uirunner_get_scanned_ip',
    ),
]



