from django.contrib.auth.views import LogoutView
from django.urls import path, reverse_lazy

from logout.views import VoterLogoutView, VoterFailView

app_name = 'logout'

urlpatterns = [
    # /logout/
    path('', LogoutView.as_view(next_page=reverse_lazy('login:login')), name='logout'),

    # /success/
    path('done/', VoterLogoutView.as_view(), name='logout_voter'),

    # /failure/
    path('failure/', VoterFailView.as_view(), name='logout_fail'),
]
