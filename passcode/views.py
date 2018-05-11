# Create your views here.
from random import randint

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.contrib.sessions.models import Session
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View


# Generate a random passcode for a user
def generate_passcode():
    # Length of the passcode
    length = 8

    # The character domain of the passcode
    charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    # The passcode to be generated
    passcode = ''

    # Generate a random passcode of specified length
    for index in range(length):
        passcode += charset[randint(0, len(charset))]

    return passcode


# Check if a different user is currently logged in
def is_currently_in(user):
    # Query all unexpired sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())

    # Build a list of authenticated IDs from that query
    ids = []

    for session in sessions:
        data = session.get_decoded()
        ids.append(data.get('_auth_user_id', None))

    # Check if the given user's id is in that list
    return user.id in ids


class PasscodeView(UserPassesTestMixin, View):
    template_name = 'passcode/password_generator.html'

    # Redirect the user to a 404 page when the user does is not allowed to view this page
    def get_login_url(self):
        return redirect('page_404:page_404')

    # Check whether the user accessing this page is a COMELEC officer or not
    def test_func(self):
        try:
            group = Group.objects.get(name='comelec')
        except Group.DoesNotExist:
            return False

        return group in self.request.user.groups.all()

    def get(self, request):
        # Get this page
        context = {'message': ''}

        return render(request, self.template_name, context)

    def post(self, request):
        # Set error messages up
        does_not_exist = 'dne'
        already_in = 'ai'
        invalid_request = 'ir'

        # Please note that the user's password really isn't returned here (that would be indicative of poor security)
        # What these lines actually do is generate a new password every time a valid user is queried
        # Then the user's password is actually changed to this new password
        # There are two reasons for this:
        #  1) To be able to actually show something to the user, because passwords can't be shown from the DB,
        #  2) A different passcode is given every time a user asks for a passcode, for security purposes.

        # Get the ID number queried
        id_number = request.POST.get('id-number', False)

        # If there was no ID number sent, return an invalid request error
        if id_number is not False:
            # Check whether a user with the queried ID number exists
            try:
                # Get the user associated with that ID number
                user = User.objects.get(username=id_number)

                # FIXME: is_currently_in() does not work yet
                # Check if that user is currently logged in
                if not is_currently_in(user):
                    # Generate a passcode
                    passcode = generate_passcode()

                    # And then change the queried user's password to the generated passcode
                    user.set_password(passcode)

                    # Save the changes to the user
                    user.save()

                    # Store that passcode in the context
                    context = {'message': passcode}
                else:
                    # If not, we can't modify a currently logged in user's password, so return an already in error
                    # Also, this would be a red flag, because this means someone has entered an ID number of someone
                    # currently in the process of voting
                    context = {'message': already_in}
            except User.DoesNotExist:
                # That user does not exist, so return a does not exist error.
                context = {'message': does_not_exist}
        else:
            # Send back an invalid request error.
            context = {'message': invalid_request}

        # Go back to this page
        return render(request, self.template_name, context)
