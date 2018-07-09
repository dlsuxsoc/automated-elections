from django.urls import path

from vote.views import VoteView, json_take

app_name = 'vote'

urlpatterns = [
    # /
    path('', VoteView.as_view(), name='vote'),

    # AJAX handlers
    # takes/<candidate_id>/<issue>/
    path('takes/<int:candidate_id>/<str:issue>/', json_take, name='candidate_takes'),
]
