# Create your views here.
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.views import View

from vote.models import Voter


class VoterLoginView(View):
    template_name = 'login/login.html'

    def get(self, request):
        # If the user is already logged in, avoid the login page
        if request.user.is_authenticated:
            try:
                # If the user is a voter, redirect to the voting page
                if Group.objects.get(name='voter') in request.user.groups.all():
                    return redirect('vote:vote')
                # If the user is a system administrator, redirect to the system administrator's page
                elif Group.objects.get(name='sysadmin') in request.user.groups.all():
                    return redirect('sysadmin:voters')
                else:
                    # If not, redirect to the admin's page
                    return redirect('passcode:passcode')
            except Group.DoesNotExist:
                # If the queried group does not exist, log the user out
                logout(request)

                return redirect('login:login')
        else:
            return render(request, self.template_name)

    def post(self, request):
        id_number = request.POST.get('username', False)
        password = request.POST.get('password', False)

        # If the username and password objects exist in the request dictionary, then it is a valid login POST
        if id_number is not False and password is not False:
            # Authenticate the credentials
            user = authenticate(request, username=id_number, password=password)

            # If the credentials are valid, try to log the user in and go straight to the voting page
            if user is not None:
                # But only log the user in if the user is actually a voter
                try:
                    # If the user is a voter, log the user in
                    if Group.objects.get(name='voter') in user.groups.all():
                        print(user.username)

                        # Get the current voter from the current user
                        voter = Voter.objects.get(user__username=user.username)

                        # Check if the user is eligible for voting and hasn't already voted
                        # If either is true, then the user is allowed to log in
                        if voter.eligibility_status is True and voter.voting_status is False:
                            login(request, user)

                            return redirect('vote:vote')
                        else:
                            messages.error(request, 'You are not eligible for voting.')

                            return render(request, self.template_name)
                    else:
                        # If the user is not a voter, stay on the login page and then show an error message
                        messages.error(request, 'You are not allowed to log in here.')

                        return render(request, self.template_name)
                except (Group.DoesNotExist, Voter.DoesNotExist):
                    # If the group does not exist, stay on the login page and then show an error message
                    messages.error(request, 'Internal server error.')

                    return render(request, self.template_name)
            else:
                # If the credentials aren't valid, stay on the login page and then show an error message
                messages.error(request, 'Incorrect ID number or password. Try again!')

                return render(request, self.template_name)
        else:
            # If no objects are received, it's an invalid request, so stay on the login page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            return render(request, self.template_name)


class AdminLoginView(View):
    template_name = 'login/admin_login.html'

    def get(self, request):
        # If the user is already logged in, avoid the login page
        if request.user.is_authenticated:
            try:
                # If the user is a voter, redirect to the voting page
                if Group.objects.get(name='voter') in request.user.groups.all():
                    return redirect('vote:vote')
                # If the user is a system administrator, redirect to the system administrator's page
                elif Group.objects.get(name='sysadmin') in request.user.groups.all():
                    return redirect('sysadmin:voters')
                else:
                    # If not, redirect to the admin's page
                    return redirect('passcode:passcode')
            except Group.DoesNotExist:
                # If the queried group does not exist, log the user out
                logout(request)

                return redirect('login:login')
        else:
            return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)

        # If the username and password objects exist in the request dictionary, then it is a valid login POST
        if username is not False and password is not False:
            # Authenticate the credentials
            user = authenticate(request, username=username, password=password)

            # If the credentials are valid, try to log the user in and go straight to the voting page
            if user is not None:
                # But only log the user in if the user is a COMELEC officer or a system administrator
                try:
                    # If the user is a COMELEC officer, log the user in
                    if Group.objects.get(name='comelec') in user.groups.all():
                        login(request, user)

                        return redirect('passcode:passcode')
                    # If the user is a system administrator, log the user in
                    elif Group.objects.get(name='sysadmin') in user.groups.all():
                        login(request, user)

                        return redirect('sysadmin:voters')
                    else:
                        # If the user is not a COMELEC officer, stay on the login page and then show an error message
                        messages.error(request, 'You are not allowed to log in here.')

                        return render(request, self.template_name)
                except Group.DoesNotExist:
                    # If the group does not exist, stay on the login page and then show an error message
                    messages.error(request, 'Internal server error.')

                    return render(request, self.template_name)
            else:
                # If the credentials aren't valid, stay on the login page and then show an error message
                messages.error(request, 'Incorrect username or password. Try again!')

                return render(request, self.template_name)
        else:
            # If no objects are received, it's an invalid request, so stay on the login page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            return render(request, self.template_name)
