# Create your views here.
from django.conf import settings

# Send an email receipt containing the candidates the voter voted for
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.views import View


# Sends an email receipt containing the voted candidates to the voter
def send_email_receipt(user, voted):
    from_email = settings.EMAIL_HOST_USER
    to_email = [user.username + '@dlsu.edu.ph']
    subject = '[COMELEC] Voter\'s receipt'
    message = '''Good day, {0} {1}!,\n\nThank you for voting! You have voted for the following candidates:\n\n{2}''' \
        .format(
        user.first_name, user.last_name,
        voted)

    send_mail(subject=subject, from_email=from_email, recipient_list=to_email, message=message, fail_silently=False)


# TODO: If the user who just logged in is not a voter, redirect to the dashboard/administration page
class VoteView(LoginRequiredMixin, View):
    template_name = 'vote/voting.html'

    def get(self, request):
        # Get this page
        return render(request, self.template_name)

    @staticmethod
    def post(request):
        # Check if the user has already voted

        # Submit voting results

        # Save voter submission

        # Send email receipt
        send_email_receipt(request.user, request.POST)

        # Log the user out
        return redirect('logout:logout_voter')
