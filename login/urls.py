from django.urls import path

from login.views import VoterLoginView, AdminLoginView

app_name = 'login'

urlpatterns = [
    # /login/
    path('', VoterLoginView.as_view(), name='login'),

    # /admin_login/
    path('admin/', AdminLoginView.as_view(), name='admin_login'),
]
