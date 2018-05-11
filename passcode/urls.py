from django.urls import path

from passcode.views import PasscodeView

app_name = 'passcode'

urlpatterns = [
    # /passcode/
    path('', PasscodeView.as_view(), name='passcode')
]
