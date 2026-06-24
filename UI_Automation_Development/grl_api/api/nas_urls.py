from django.urls import path

from .views_nas import UploadFileView

urlpatterns = [
    path('UploadFile/', UploadFileView.as_view(), name='nas_upload_file'),
]




