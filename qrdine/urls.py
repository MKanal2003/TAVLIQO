from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from menu.views import menu_viewer_by_token

urlpatterns = [
    path('manage-qrdine/', admin.site.urls),
    
    path('r/<str:token>/', menu_viewer_by_token, name='menu_by_token'),
    path('r/<str:token>/', include('orders.urls')),
    path('menu/', include('menu.urls')),

    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('restaurants.urls')),
    path('superadmin/', include('superadmin.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'