from django.urls import path

from vote.views import VoteView

app_name = 'vote'

urlpatterns = [
    # /
    path('', VoteView.as_view(), name='vote')
]
