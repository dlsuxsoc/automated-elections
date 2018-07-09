from django.urls import path

from sysadmin.views import VotersView, CandidatesView, OfficersView, UnitView, json_take

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
    # /sysadmin/candidates/takes/<candidate_id>/<issue>
    path('candidates/takes/<int:candidate_id>/<str:issue>', json_take, name='voters_list')
]
