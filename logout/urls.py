from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

app_name = 'logout'

urlpatterns = [
    # /logout/
    path('', LogoutView.as_view(next_page=reverse_lazy('login:login')), name='logout'),

    # /logout/done
    path('done/', LogoutView.as_view(template_name='logout/success.html'), name='logout_voter'),
]
