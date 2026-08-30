from django.urls import path

from . import views


urlpatterns = [
    path('test/<int:exam_id>/', views.test_with_chat, name='test_with_chat'),
    path('test_end/<int:exam_id>/', views.test_end, name='test_end'),
    path('get_remaining_time/<int:exam_id>/', views.get_remaining_time, name='get_remaining_time'),
    path('proctor/<int:exam_id>/dashboard', views.proctor_dash, name='Dash'),
    path('proctor/<int:exam_id>/session/<str:session_id>/data', views.proctor, name='proctor'),
    path("agora/token/<int:exam_id>/", views.get_agora_token),
    path("api/detect-phone/", views.detect_phone, name="detect_phone"),
    path("proctor/report/<int:exam_id>/", views.generate_report, name="generate_report"),
    path("proctor/report/status/<int:report_id>/", views.report_status, name="report_status"),
    path("proctor/report/download/<int:report_id>/", views.download_report, name="download_report"),
]
