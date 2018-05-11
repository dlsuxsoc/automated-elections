# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View


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

        # Log the user out
        return redirect('logout:logout_voter')
