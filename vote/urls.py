from honeypot.decorators import check_honeypot

from django.urls import path

from vote.views import VoteView, json_take

app_name = 'vote'

urlpatterns = [
    # /
    path('', check_honeypot(VoteView.as_view(), field_name='poll-answer'), name='vote'),

    # AJAX handlers
    # takes/<candidate_identifier>/<issue>/
    path('takes/<uuid:candidate_identifier>/<str:issue>/', json_take, name='candidate_takes'),
]
