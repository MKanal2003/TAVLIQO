from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('restaurants/', views.restaurants_list, name='restaurants'),
    path('restaurants/create/', views.create_restaurant_admin, name='create_restaurant_admin'),
    path('restaurants/<int:pk>/edit/', views.edit_restaurant, name='edit_restaurant'),
    path('restaurants/<int:pk>/toggle/', views.toggle_restaurant, name='toggle_restaurant'),
    path('restaurants/<int:pk>/regenerate-qr/', views.regenerate_restaurant_qr, name='regenerate_restaurant_qr'),
]