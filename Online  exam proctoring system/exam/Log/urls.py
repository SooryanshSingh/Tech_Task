for . import views
from django.urls import path,include



urlpatterns=[path('login',view.login_user, name='login'),
path('logout',view.logout_user, name='logout'),]
