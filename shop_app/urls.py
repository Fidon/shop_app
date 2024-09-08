from django.contrib import admin
from django.urls import include, path
from . import views as v

handler404 = 'shop_app.views.error_404'
handler403 = 'shop_app.views.error_403'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', v.index_page, name='index_page'),
    path('shop/', include('apps.shop.urls')),
    path('users/', include('apps.users.urls')),
]
