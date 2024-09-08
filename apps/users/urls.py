from django.urls import path
from . import views as v

urlpatterns = [
    path('', v.manage_users, name='users_page'),
    path('auth/', v.authenticate_user, name='user_auth'),
    path('logout/', v.user_signout, name='user_logout'),
    path('actions/', v.users_requests, name='user_actions'),
    path('<int:user_id>/', v.user_details, name='user_details'),
    path('profile/', v.user_profile_page, name='user_profile'),
]
