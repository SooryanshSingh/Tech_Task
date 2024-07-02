from . import views
from django.urls import path, include

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('login/', views.login_user, name='button1'),
    path('logout/', views.logout_user, name='button2'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('marks/', views.marks_view, name='marks'),
    path('', include('django.contrib.auth.urls')),
    path('exam_manage/', views.exam_manage, name='exam_manage'),
    path('exam_manage/<int:exam_id>/', views.exam_manage, name='exam_manage'),
    path('exam_list/', views.exam_list, name='exam_list'),
     path('delete_exam/<int:exam_id>/', views.delete_exam, name='delete_exam'),  # Example delete exam URL
    path('company_dashboard/', views.company_dashboard, name='company_dashboard'),
    path('proctor_dashboard/', views.proctor_dashboard, name='proctor_dashboard'),

]
