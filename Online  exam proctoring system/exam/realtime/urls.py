from django.urls import path
from . import views

urlpatterns = [
    path('test/<int:exam_id>/', views.test_with_chat, name='test_with_chat'),
        path('test_end/<int:exam_id>/', views.test_end, name='test_end'),

]

