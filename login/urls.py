from django.contrib.auth.views import LoginView
from django.urls import path

app_name = 'login'

urlpatterns = [
    # /login/
    path('', LoginView.as_view(template_name='login/index.html', redirect_authenticated_user=True), name='login')
]
