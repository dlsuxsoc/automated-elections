# Create your views here.
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View

# Sends an email receipt containing the voted candidates to the voter
from vote.models import Issue, Candidate, Voter, Take


# Test function for this view
def vote_test_func(user):
    if user.is_authenticated:
        try:
            return Group.objects.get(name='voter') in user.groups.all()
        except Group.DoesNotExist:
            return False
    else:
        return False


class VoteView(UserPassesTestMixin, View):
    template_name = 'vote/voting.html'

    # Sends an email receipt to the voter
    @staticmethod
    def send_email_receipt(user, voted):
        from_email = settings.EMAIL_HOST_USER
        to_email = [user.email]
        subject = '[COMELEC] Voter\'s receipt'
        message = '''Good day, {0} {1}!,\n\nThank you for voting! You have voted for the following candidates:\n\n{2}''' \
            .format(
            user.first_name, user.last_name,
            voted)

        send_mail(subject=subject, from_email=from_email, recipient_list=to_email, message=message, fail_silently=False)

    # Check whether the user accessing this page is a voter or not
    def test_func(self):
        return vote_test_func(self.request.user)

    def get(self, request):
        # Get the current voter from the current user
        voter = Voter.objects.get(user__username=request.user.username)

        # Get the college of the current voter
        college = voter.college.name

        # Get the batch of the current voter
        batch = voter.user.username[:3]

        # Get all executive board candidates
        executive_board = Candidate.objects.filter(position__unit__batch__isnull=True,
                                                   position__unit__college__isnull=True)

        # Get all college board candidates
        college_board = Candidate.objects.filter(position__unit__batch__isnull=True,
                                                 position__unit__college__isnull=False,
                                                 position__unit__college__name=college)

        # Get all batch board candidates
        batch_board = Candidate.objects.filter(position__unit__batch__isnull=False,
                                               position__unit__college__isnull=False,
                                               position__unit__batch=batch)

        # Get all issues
        issues = Issue.objects.all().order_by('name')

        context = {
            'executive_board': executive_board,
            'college_board': college_board,
            'batch_board': batch_board,
            'issues': issues
        }

        # Get this page
        return render(request, self.template_name, context)

    @staticmethod
    def post(request):
        voter = request.user.voter

        # Check if the voter has already voted
        # If not yet...
        if not voter.voting_status:
            # Submit voting results

            # Save voter submission

            # Send email receipt
            # self.send_email_receipt(request.user, request.POST)

            # Mark the voter as already voted
            voter.voting_status = True
            voter.save()

            # Log the user out
            logout(request)

            return redirect('logout:logout_voter')
        else:
            # But if the voter already did...
            messages.error(request, 'You have already voted. You may only vote once.')

            return redirect('logout:logout_fail')


@user_passes_test(vote_test_func)
def json_take(request, candidate_id, issue):
    # Get the take
    try:
        take = Take.objects.get(candidate__id=candidate_id, issue__name=issue)
    except Take.DoesNotExist:
        return JsonResponse({'response': "This candidate doesn't have a take on this issue yet."})

    # Then return its response
    return JsonResponse({'response': take.response})
