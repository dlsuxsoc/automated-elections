from django.urls import path

from passcode.views import PasscodeView, VotersView, CandidatesView, ResultsView, json_details

app_name = 'passcode'

urlpatterns = [
    # /officer/voters/
    path('voters/', VotersView.as_view(), name='voters'),

    # /officer/candidates/
    path('candidates/', CandidatesView.as_view(), name='candidates'),

    # /officer/results/
    path('results/', ResultsView.as_view(), name='results'),

    # /officer/passcode/
    path('passcode/', PasscodeView.as_view(), name='passcode'),

    # AJAX handlers
    # /officer/voters/details/<voter_id>
    path('voters/details/<int:voter_id>/', json_details, name='voter_details'),
]
