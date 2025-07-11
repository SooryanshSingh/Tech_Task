from django.urls import path
from . import views
from .views import get_remaining_time


urlpatterns = [
    path('test/<int:exam_id>/', views.test_with_chat, name='test_with_chat'),
        path('test_end/<int:exam_id>/', views.test_end, name='test_end'),
        path('get_remaining_time/<int:exam_id>/', get_remaining_time, name='get_remaining_time'),
        path('proctor/<int:exam_id>/', views.proctor, name='proctor')


]

