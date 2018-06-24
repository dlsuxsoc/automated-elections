# Create your views here.
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.shortcuts import render
from django.views import View

from passcode.views import generate_passcode
from vote.models import Voter, College, Candidate, Position


class SysadminView(UserPassesTestMixin, View):
    template_name = ''

    # Check whether the user accessing this page is a system administrator or not
    def test_func(self):
        try:
            return Group.objects.get(name='sysadmin') in self.request.user.groups.all()
        except Group.DoesNotExist:
            return False

    # Display the necessary objects for a specific context
    def display_objects(self):
        pass

    def get(self, request):
        pass

    def post(self, request):
        pass


class VotersView(SysadminView):
    template_name = 'sysadmin/admin-voter.html'

    def display_objects(self):
        voters = Voter.objects.all().order_by('user__last_name')
        colleges = College.objects.all().order_by('name')

        context = {
            'voters': voters,
            'colleges': colleges,
        }

        return context

    def get(self, request):
        context = self.display_objects()

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        if form_type is not False:
            # The submitted form is for adding a voter
            if form_type == 'add-voter':
                first_name = request.POST.get('voter-firstnames', False)
                last_name = request.POST.get('voter-lastname', False)
                username = request.POST.get('voter-id', False)
                college_name = request.POST.get('voter-college', False)
                voting_status_name = request.POST.get('voter-voting-status', False)
                eligibility_status_name = request.POST.get('voter-eligibility-status', False)

                if first_name is not False and last_name is not False and username is not False \
                        and college_name is not False \
                        and voting_status_name is not False and eligibility_status_name is not False:
                    # Derive the email from the username (the ID number)
                    email = username + '@dlsu.edu.ph'

                    # Set an initial password
                    password = generate_passcode()

                    # Retrieve the voting and eligibility statuses using the name provided
                    voting_status = True if voting_status_name == 'Has already voted' else False
                    eligibility_status = True if eligibility_status_name == 'Eligible' else False

                    try:
                        # Create the user given the information provided
                        user = User.objects.create_user(username=username, email=email, first_name=first_name,
                                                        last_name=last_name,
                                                        password=password)
                    except IntegrityError:
                        # Display an error message
                        messages.error(request, 'A voter with that ID number already exists.')

                        context = self.display_objects()

                        return render(request, self.template_name, context)

                    # Add the user to the voter group
                    group = Group.objects.get(name='voter')
                    group.user_set.add(user)

                    # Save the changes to the created user
                    user.save()

                    try:
                        # Retrieve the college using the name provided
                        college = College.objects.get(name=college_name)
                    except Group.DoesNotExist:
                        # Display an error message

                        # Delete the created user
                        user.delete()

                        messages.error(request, 'Invalid request.')

                        context = self.display_objects()

                        return render(request, self.template_name, context)

                    # Create the voter using the created user
                    Voter.objects.create(user=user, college=college,
                                         voting_status=voting_status, eligibility_status=eligibility_status)

                    # Display a success message
                    messages.success(request, 'Voter successfully created.')

                    context = self.display_objects()

                    return render(request, self.template_name, context)

                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects()

                    return render(request, self.template_name, context)
            else:
                # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                # message
                messages.error(request, 'Invalid request.')

                return render(request, self.template_name)
        else:
            # If no objects are received, it's an invalid request, so stay on the page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            return render(request, self.template_name)


class CandidatesView(SysadminView):
    template_name = 'sysadmin/admin-candidate.html'

    def display_objects(self):
        candidates = Candidate.objects.all().order_by('voter__user__last_name')
        positions = Position.objects.all().order_by('name')

        context = {
            'candidates': candidates,
            'positions': positions,
        }

        return context

    def get(self, request):
        context = self.display_objects()

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        if form_type is not False:
            # The submitted form is for adding a voter
            if form_type == 'add-voter':
                first_name = request.POST.get('voter-firstnames', False)
                last_name = request.POST.get('voter-lastname', False)
                username = request.POST.get('voter-id', False)
                college_name = request.POST.get('voter-college', False)
                voting_status_name = request.POST.get('voter-voting-status', False)
                eligibility_status_name = request.POST.get('voter-eligibility-status', False)

                if first_name is not False and last_name is not False and username is not False \
                        and college_name is not False \
                        and voting_status_name is not False and eligibility_status_name is not False:
                    # Derive the email from the username (the ID number)
                    email = username + '@dlsu.edu.ph'

                    # Set an initial password
                    password = generate_passcode()

                    # Retrieve the voting and eligibility statuses using the name provided
                    voting_status = True if voting_status_name == 'Has already voted' else False
                    eligibility_status = True if eligibility_status_name == 'Eligible' else False

                    try:
                        # Create the user given the information provided
                        user = User.objects.create_user(username=username, email=email, first_name=first_name,
                                                        last_name=last_name,
                                                        password=password)
                    except IntegrityError:
                        # Display an error message
                        messages.error(request, 'A voter with that ID number already exists.')

                        context = self.display_objects()

                        return render(request, self.template_name, context)

                    # Add the user to the voter group
                    group = Group.objects.get(name='voter')
                    group.user_set.add(user)

                    # Save the changes to the created user
                    user.save()

                    try:
                        # Retrieve the college using the name provided
                        college = College.objects.get(name=college_name)
                    except Group.DoesNotExist:
                        # Display an error message

                        # Delete the created user
                        user.delete()

                        messages.error(request, 'Invalid request.')

                        context = self.display_objects()

                        return render(request, self.template_name, context)

                    # Create the voter using the created user
                    Voter.objects.create(user=user, college=college,
                                         voting_status=voting_status, eligibility_status=eligibility_status)

                    # Display a success message
                    messages.success(request, 'Voter successfully created.')

                    context = self.display_objects()

                    return render(request, self.template_name, context)

                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects()

                    return render(request, self.template_name, context)
            else:
                # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                # message
                messages.error(request, 'Invalid request.')

                return render(request, self.template_name)
        else:
            # If no objects are received, it's an invalid request, so stay on the page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            return render(request, self.template_name)


class OfficersView(SysadminView):
    template_name = 'sysadmin/admin-officer.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        return render(request, self.template_name)


class UnitView(SysadminView):
    template_name = 'sysadmin/admin-unit.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        return render(request, self.template_name)
