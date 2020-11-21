# Create your views here.
import requests

from django.contrib import messages
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.views import View

from passcode.views import ResultsView
from vote.models import Voter, ElectionStatus

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
        # Captcha validation
        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()
        if result['success']:
            # Log in only if there are actually elections ongoing
            if ResultsView.is_election_ongoing():
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
                                # Get the current voter from the current user
                                voter = Voter.objects.get(user__username=user.username)

                                # Get the college of the current voter
                                college = voter.college.name

                                # Get the batch of the current voter
                                batch = voter.user.username[:3]

                                # Only log the user if
                                # (1) The user is eligible
                                # (2) The user hasn't voted yet
                                # (3) The user's batch and college is eligible for the elections
                                if voter.eligibility_status is True and voter.voting_status is False \
                                        and (ElectionStatus.objects.filter(college__name=college, batch=batch).count() != 0
                                            or ElectionStatus.objects.filter(college__name=college,
                                                                            batch__contains='below').count() == 1
                                            and batch <= ElectionStatus.objects.get(college__name=college,
                                                                                    batch__contains='below').batch):
                                    # Check if the user is eligible for voting and hasn't already voted
                                    # If either is true, then the user is allowed to log in
                                    login(request, user)

                                    return redirect('vote:vote')
                                else:
                                    messages.error(request,
                                                'You are not eligible for voting.' + (
                                                    ' You have already voted.'
                                                    if voter.voting_status is True else
                                                    ' You aren\'t part of the elections.')
                                                )

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
            else:
                messages.error(request, 'There are no elections currently ongoing.')
        else: 
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')    
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
        # Captcha validation
        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()
        if result['success']:
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
        else: 
            #If the captcha was invalid then return the error 
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')

            return render(request, self.template_name)
