from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:item_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<str:order_token>/', views.order_status, name='order_status'),
    path('api/order/<str:order_token>/status/', views.check_order_status, name='check_order_status'),
    path('api/order/<str:order_token>/call-waiter/', views.call_waiter, name='call_waiter'),
]