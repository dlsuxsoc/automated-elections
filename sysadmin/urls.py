from django.urls import path

from sysadmin.views import VotersView, CandidatesView, OfficersView, UnitView

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

    # # /sysadmin/voters_list/
    # path('voters_list', DownloadVotersListView.as_view(), name='voters_list')
]
