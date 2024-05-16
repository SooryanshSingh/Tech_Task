from . import views
from django.urls import path,include



urlpatterns=[path('login',views.login_user, name='button1'),
path('logout',views.logout_user, name='button2'),
path('signup/', views.signup, name='signup'),
]
