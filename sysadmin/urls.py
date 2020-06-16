from django.urls import path

from sysadmin.views import VotersView, CandidatesView, OfficersView, UnitView, json_take, json_details, PositionView, \
    IssueView, PollView

app_name = 'sysadmin'

urlpatterns = [
    # /sysadmin/voters/
    path('voters/', VotersView.as_view(), name='voters'),

    # /sysadmin/candidates/
    path('candidates/', CandidatesView.as_view(), name='candidates'),

    # /sysadmin/officers/
    path('officers/', OfficersView.as_view(), name='officers'),

    # /sysadmin/unit/
    path('units/', UnitView.as_view(), name='units'),

    # /sysadmin/position/
    path('positions/', PositionView.as_view(), name='positions'),

    # /sysadmin/issue/
    path('issues/', IssueView.as_view(), name='issues'),

    # /sysadmin/poll/
    path('polls/', PollView.as_view(), name='polls'),

    # AJAX handlers
    # /sysadmin/voters/details/<voter_id>
    path('voters/details/<int:voter_id>/', json_details, name='voter_details'),

    # /sysadmin/candidates/takes/<candidate_id>/<issue>/
    path('candidates/takes/<int:candidate_id>/<str:issue>/', json_take, name='candidate_takes'),
]
