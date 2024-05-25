from . import views
from django.urls import path,include



urlpatterns=[path('',views.home, name='home'),
path('about',views.about,name='about'),
path('login',views.login_user, name='button1'),
path('logout',views.logout_user, name='button2'),
path('signup/', views.signup, name='signup'),
path('login', include('django.contrib.auth.urls')),
path('exams/', views.exam_list, name='exam_list'),
path('exams/<int:exam_id>/', views.exam_detail, name='exam_detail'),
path('exams/create/', views.exam_create, name='exam_create'),
path('exams/<int:exam_id>/update/', views.exam_update, name='exam_update'),
path('exams/<int:exam_id>/delete/', views.exam_delete, name='exam_delete'),
]
