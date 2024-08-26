from django.urls import path
from . import views as v

urlpatterns = [
    path('dashboard/', v.dashboard_page, name='dashboard_page'),
    path('inventory/', v.inventory_page, name='inventory_page'),
    path('inventory/actions/', v.product_actions, name='product_actions'),
    path('<int:product_id>/', v.product_details, name='product_details'),
]
