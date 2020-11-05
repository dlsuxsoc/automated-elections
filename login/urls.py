from honeypot.decorators import check_honeypot

from django.urls import path

from login.views import VoterLoginView, AdminLoginView

app_name = 'login'

urlpatterns = [
    # /login/
    path('', check_honeypot(VoterLoginView.as_view(), field_name="idnumber"), name='login'),

    # /admin_login/
    path('admin/', check_honeypot(AdminLoginView.as_view(), field_name="username1"), name='admin_login'),
]
