from . import views
from django.urls import path, include

urlpatterns = [
    path('', views.home, name='home'),
    path('', include('realtime.urls')), 
    path('about/', views.about, name='about'),
    path('login/', views.login_user, name='button1'),
    path('logout/', views.logout_user, name='button2'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('marks/', views.marks_view, name='marks'),
    path('', include('django.contrib.auth.urls')),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/<int:exam_id>/', views.exam_detail, name='exam_detail'),  
    path('exams/create/', views.exam_create, name='exam_create'), 
    path('exams/<int:exam_id>/update/', views.exam_update, name='exam_update'),  
    path('exams/<int:exam_id>/delete/', views.exam_delete, name='exam_delete'), 
    path('exams/questions/<int:exam_id>/', views.question_list, name='question_list'),
    path('exams/questions/<int:exam_id>/create/', views.question_create, name='question_create'), 
    path('exams/questions/<int:exam_id>/update/<int:question_id>/', views.question_update, name='question_update'),  
    path('exams/questions/<int:exam_id>/delete/<int:question_id>/', views.question_delete, name='question_delete'), 
    path('company_dashboard/', views.company_dashboard, name='company_dashboard'),
    path('proctor_dashboard/', views.proctor_dashboard, name='proctor_dashboard'),


]
