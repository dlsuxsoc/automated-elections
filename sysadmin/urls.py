from django.urls import path

from sysadmin.views import VotersView, CandidatesView, OfficersView, UnitView, json_take, json_details

app_name = 'sysadmin'

urlpatterns = [
    # /sysadmin/voters/
    path('voters/', VotersView.as_view(), name='voters'),

    # /sysadmin/candidates/
    path('candidates/', CandidatesView.as_view(), name='candidates'),

    # /sysadmin/officers/
    path('officers/', OfficersView.as_view(), name='officers'),

    # /sysadmin/unit/
    path('unit/', UnitView.as_view(), name='unit'),

    # AJAX handlers
    # /sysadmin/voters/details/<voter_id>
    path('voters/details/<int:voter_id>/', json_details, name='voter_details'),

    # /sysadmin/candidates/takes/<candidate_id>/<issue>/
    path('candidates/takes/<int:candidate_id>/<str:issue>/', json_take, name='candidate_takes'),
]
