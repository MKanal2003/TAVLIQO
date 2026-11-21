from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('robots.txt', views.robots_txt, name='robots_txt'), # This was crashing
    path('auth-redirect/', views.login_redirect, name='login_redirect'),
    path('portal/', views.secret_portal, name='secret_portal'),
]