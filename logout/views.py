# Create your views here.
from django.contrib.auth import logout
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.views import View


class VoterLogoutView(View):
    template_name = 'logout/success.html'

    def get(self, request):
        # Only show the success page if the user is not authenticated
        if not request.user.is_authenticated:
            return render(request, self.template_name)
        else:
            # If the user is authenticated, redirect them to the appropriate pages
            try:
                # If the user is a voter, redirect to the voting page
                if Group.objects.get(name='voter') in request.user.groups.all():
                    return redirect('vote:vote')
                else:
                    # If not, redirect to the admin's page
                    return redirect('passcode:passcode')
            except Group.DoesNotExist:
                # If the queried group does not exist, log the user out
                logout(request)

                return redirect('login:login')

    def post(self, request):
        return render(request, self.template_name)
