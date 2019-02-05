from django.urls import path

from vote.views import VoteView, json_take

app_name = 'vote'

urlpatterns = [
    # /
    path('', VoteView.as_view(), name='vote'),

    # AJAX handlers
    # takes/<candidate_identifier>/<issue>/
    path('takes/<uuid:candidate_identifier>/<int:issue_id>/', json_take, name='candidate_takes'),
]
