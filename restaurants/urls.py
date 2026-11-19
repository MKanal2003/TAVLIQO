from django.urls import path
from . import views
from orders import views as orders_views

app_name = 'restaurants'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    path('profile/', views.profile, name='profile'),
    path('categories/', views.categories, name='categories'),
    path('categories/<int:pk>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:pk>/delete/', views.delete_category, name='delete_category'),
    path('items/', views.menu_items, name='menu_items'),
    path('items/add/', views.add_item, name='add_item'),
    path('items/<int:pk>/edit/', views.edit_item, name='edit_item'),
    path('items/<int:pk>/delete/', views.delete_item, name='delete_item'),
    path('items/<int:pk>/toggle/', views.toggle_availability, name='toggle_availability'),
    path('qr-code/', views.qr_code_view, name='qr_code_view'),
    path('qr-code/regenerate/', views.regenerate_qr, name='regenerate_qr'),
    path('staff/manage/', views.manage_staff, name='manage_staff'),

    # Staff Dashboard
    path('staff/', orders_views.staff_dashboard, name='staff_dashboard'),
    path('staff/orders/create/', orders_views.staff_create_order, name='staff_order'),
    path('staff/orders/<int:pk>/advance/', orders_views.staff_advance_order, name='staff_order_advance'),
    path('staff/orders/<int:pk>/accept/', orders_views.staff_accept_order, name='staff_order_accept'),
    path('staff/orders/<int:pk>/reject/', orders_views.staff_reject_order, name='staff_order_reject'),
    path('staff/orders/<int:pk>/receipt/', orders_views.staff_order_receipt, name='staff_order_receipt'),

    # Admin Orders
    path('orders/', orders_views.admin_orders, name='orders'),
    path('orders/<int:pk>/accept/', orders_views.admin_order_accept, name='order_accept'),
    path('orders/<int:pk>/reject/', orders_views.admin_order_reject, name='order_reject'),
    path('orders/<int:pk>/advance/', orders_views.admin_order_advance, name='order_advance'),
    path('orders/<int:pk>/receipt/', orders_views.order_receipt, name='order_receipt'),
]