# Create your views here.

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from passcode.views import PasscodeView
from sysadmin.forms import IssueForm, OfficerForm, UnitForm
from vote.models import Voter, College, Candidate, Position, Unit, Party, Issue, Take


# Test function for this view
def sysadmin_test_func(user):
    try:
        return Group.objects.get(name='sysadmin') in user.groups.all()
    except Group.DoesNotExist:
        return False


class RestrictedView(UserPassesTestMixin, View):
    # Check whether the user accessing this page is a system administrator or not
    def test_func(self):
        return sysadmin_test_func(self.request.user)


class SysadminView(RestrictedView):
    template_name = ''

    # Defines the number of objects shown in a page
    objects_per_page = 5

    # Display the necessary objects for a specific context
    def display_objects(self, page, query=False):
        pass

    def get(self, request):
        pass

    def post(self, request):
        pass


class VotersView(SysadminView):
    template_name = 'sysadmin/admin-voter.html'

    # A convenience function for creating a voter
    @staticmethod
    def create_voter(first_name, last_name, username, college_name, voting_status_name, eligibility_status_name):
        # Derive the email from the username (the ID number)
        email = username + '@dlsu.edu.ph'

        # Set an initial password
        password = PasscodeView.generate_passcode()

        # Retrieve the voting and eligibility statuses using the name provided
        voting_status = True if voting_status_name == 'Has already voted' else False
        eligibility_status = True if eligibility_status_name == 'Eligible' else False

        # Create the user given the information provided
        user = User.objects.create_user(username=username, email=email, first_name=first_name,
                                        last_name=last_name,
                                        password=password)

        # Add the user to the voter group
        group = Group.objects.get(name='voter')
        group.user_set.add(user)

        # Save the changes to the created user
        user.save()

        # Retrieve the college using the name provided
        college = College.objects.get(name=college_name)

        # Create the voter using the created user
        Voter.objects.create(user=user, college=college,
                             voting_status=voting_status, eligibility_status=eligibility_status)

    # A convenience function for changing a voter
    @staticmethod
    def change_voter_eligibility(voter_id, eligibility_status_name):
        # Retrieve the voter in question
        voter = Voter.objects.get(user__username=voter_id)

        # Resolve the input
        eligibility_status = True if eligibility_status_name == 'Eligible' else False

        # Modify the field in question with the given value
        voter.eligibility_status = eligibility_status

        # Save changes
        voter.save()

    # A convenience function for deleting a voter
    @staticmethod
    def delete_voter(user_id):
        # Take note that it is not really the voter that is deleted, but the user associated with that voter
        user = User.objects.get(id=user_id)

        # Get rid of that user
        user.delete()

    def display_objects(self, page, query=False):
        # Show everything if the query is empty
        if query is False:
            voters = Voter.objects.all().order_by('user__username')
        else:
            voters = Voter.objects.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query)
            ) \
                .order_by('user__username')

        colleges = College.objects.all().order_by('name')

        paginator = Paginator(voters, self.objects_per_page)
        paginated_voters = paginator.get_page(page)

        context = {
            'voters': paginated_voters,
            'colleges': colleges,
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)
        query = request.GET.get('query', False)

        context = self.display_objects(page if page is not False else 1, query)

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
                    try:
                        with transaction.atomic():
                            # Create the voter
                            self.create_voter(first_name, last_name, username, college_name, voting_status_name,
                                              eligibility_status_name)

                            # Display a success message
                            messages.success(request, 'Voter successfully created.')
                    except IntegrityError:
                        messages.error(request, 'A voter with that ID number already exists.')
                    except College.DoesNotExist:
                        messages.error(request, 'That college does not exist.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            elif form_type == 'edit-voter':
                # The submitted form is for editing a voter
                page = request.POST.get('page', False)
                voter_id = request.POST.get('edit-id', False)
                eligibility_status_name = request.POST.get('voter-eligibility-status', False)

                if page is not False and voter_id is not False and eligibility_status_name is not False:
                    try:
                        with transaction.atomic():
                            # Edit the voter
                            self.change_voter_eligibility(voter_id, eligibility_status_name)

                            # Display a success message
                            messages.success(request, 'Voter successfully edited.')
                    except Voter.DoesNotExist:
                        messages.error(request, 'No such voter exists.')

                    context = self.display_objects(page)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            elif form_type == 'add-bulk-voter':
                # The submitted form is for adding voters in bulk
                voting_status_name = request.POST.get('voter-voting-status', False)
                eligibility_status_name = request.POST.get('voter-eligibility-status', False)

                if request.FILES['voters-list'] is not None \
                        and voting_status_name is not None \
                        and eligibility_status_name is not None:
                    # Get the file from the request object
                    file = request.FILES['voters-list']

                    # Load all rows from the uploaded file
                    num_voters_added = 0
                    has_passed_header = False

                    # List of all voter information to be added
                    voter_info = []

                    # Either all voters are added, or none at all
                    # Iterate all rows
                    for row in file:
                        # Convert the row to string
                        row_str = row.decode('utf-8').strip()

                        # Skip the first row (the header)
                        if not has_passed_header:
                            has_passed_header = True

                            continue

                        # Check for missing rows
                        try:
                            voter_data_split = row_str.split(',', 4)

                            if len(voter_data_split) != 4:
                                raise ValueError
                        except ValueError:
                            messages.error(request,
                                           'There were missing fields in the uploaded list. No voters were'
                                           ' added.')

                            context = self.display_objects(1)

                            return render(request, self.template_name, context)

                        # Get specific values
                        id_number = voter_data_split[0].strip()
                        last_name = voter_data_split[1].strip()
                        first_names = voter_data_split[2].strip()
                        college = voter_data_split[3].strip()

                        # If the inputs contain invalid data, stop processing immediately
                        if User.objects.filter(username=id_number).count() > 0 \
                                or College.objects.filter(name=college).count() == 0:
                            messages.error(request,
                                           'The uploaded list contained invalid voter data or voters who were already'
                                           ' added previously. No further voters were added.')

                            context = self.display_objects(1)

                            return render(request, self.template_name, context)

                        # Add them to the list
                        voter_info.append(
                            {
                                'id_number': id_number,
                                'last_name': last_name,
                                'first_names': first_names,
                                'college': college,
                            }
                        )

                        # Increment the added voter count
                        num_voters_added += 1

                    # If the file uploaded was empty
                    if num_voters_added == 0:
                        messages.error(request,
                                       'The uploaded list did not contain any voters.')
                    try:
                        for voter in voter_info:
                            with transaction.atomic():
                                # Try to create the voter
                                self.create_voter(
                                    voter['first_names'],
                                    voter['last_name'],
                                    voter['id_number'],
                                    voter['college'],
                                    voting_status_name,
                                    eligibility_status_name
                                )

                        # Display a success message after all voters have been successfully added
                        messages.success(request, 'All {0} voter(s) successfully added.'.format(num_voters_added))
                    except IntegrityError:
                        messages.error(request, 'A voter with that ID number already exists.')
                    except College.DoesNotExist:
                        messages.error(request, 'The uploaded list contained invalid voter data. No voters were added')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            elif form_type == 'delete-voter':
                # The submitted form is for deleting voters
                voters_list = request.POST.getlist('voters')

                if voters_list is not False and len(voters_list) > 0:
                    try:
                        voters_deleted = 0

                        # Try to delete each voter in the list
                        with transaction.atomic():
                            for voter in voters_list:
                                self.delete_voter(voter)

                                voters_deleted += 1

                            messages.success(request, "All {0} voter(s) successfully deleted.".format(voters_deleted))
                    except User.DoesNotExist:
                        # If the user does not exist
                        messages.error(request,
                                       'One of the selected users do not exist in the first place. '
                                       'No voters were deleted.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            else:
                # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                # message
                messages.error(request, 'Invalid request.')

                context = self.display_objects(1)

                return render(request, self.template_name, context)
        else:
            # If no objects are received, it's an invalid request, so stay on the page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)


class CandidatesView(SysadminView):
    template_name = 'sysadmin/admin-candidate.html'

    # A convenience function for adding a candidate
    @staticmethod
    def add_candidate(voter_id, position_unit, position_name, party):
        # Retrieve the voter
        voter = Voter.objects.get(user__username=voter_id)

        # Retrieve the position
        position = Position.objects.get(unit__name=position_unit, name=position_name)

        # Retrieve the party
        if party == 'Independent':
            party = None
        else:
            party = Party.objects.get(name=party)

        # Create the candidate
        Candidate.objects.create(voter=voter, position=position, party=party)

    # A convenience function for adding a take
    @staticmethod
    def add_or_edit_take(candidate_id, issue, response):
        # Retrieve the candidate
        candidate = Candidate.objects.get(voter__user__username=candidate_id)

        # Retrieve the issue
        issue = Issue.objects.get(name=issue)

        # If a candidate's take on an issue already exists, edit it instead
        take, created = Take.objects.get_or_create(candidate=candidate, issue=issue, defaults={'response': response})

        if not created:
            take.response = response

            take.save()

    # A convenience function for deleting a candidate
    @staticmethod
    def delete_candidate(candidate_id):
        # Retrieve the candidate
        candidate = Candidate.objects.get(id=candidate_id)

        # Get rid of that candidate
        candidate.delete()

    # A convenience function for deleting a take
    @staticmethod
    def delete_take(candidate_id, issue):
        # Retrieve the candidate
        candidate = Candidate.objects.get(voter__user__username=candidate_id)

        # Retrieve the issue
        issue = Issue.objects.get(name=issue)

        # If a candidate's take on an issue already exists, delete it
        take = Take.objects.get(candidate=candidate, issue=issue)

        take.delete()

    def display_objects(self, page, query=False):
        # Show everything if the query is empty
        if query is False:
            candidates = Candidate.objects.all().order_by('voter__user__username')
        else:
            candidates = Candidate.objects.filter(
                Q(voter__user__username__icontains=query) |
                Q(voter__user__first_name__icontains=query) |
                Q(voter__user__last_name__icontains=query) |
                Q(party__name__icontains=query)
            ) \
                .order_by('voter__user__username')

        voters = Voter.objects.all().order_by('user__username')
        positions = Position.objects.all().order_by('unit__name', 'name')
        parties = Party.objects.all().order_by('name')
        issues = Issue.objects.all().order_by('name')

        paginator = Paginator(candidates, self.objects_per_page)
        paginated_candidates = paginator.get_page(page)

        issue_form = IssueForm()

        context = {
            'candidates': paginated_candidates,
            'voters': voters,
            'positions': positions,
            'parties': parties,
            'issues': issues,
            'issue_form': issue_form,
            'candidates_all': candidates
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)
        query = request.GET.get('query', False)

        context = self.display_objects(page if page is not False else 1, query)

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        issue_form = IssueForm(request.POST)

        if form_type is not False:
            # The submitted form is for adding a candidate
            if form_type == 'add-candidate':
                candidate = request.POST.get('cand-voter', False)
                position = request.POST.get('cand-position', False)
                party = request.POST.get('cand-party', False)

                if candidate is not False and position is not False and party is not False:
                    # Check for missing rows
                    try:
                        # Clean the input
                        candidate_details = candidate.split(":", 2)
                        position_details = position.split(":", 2)

                        if len(position_details) != 2 or len(candidate_details) != 2:
                            raise ValueError

                        candidate = candidate_details[0].strip()

                        position_unit = position_details[0].strip()
                        position_name = position_details[1].strip()
                    except ValueError:
                        messages.error(request,
                                       'Invalid position or candidate details.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)

                    # Try to create the candidate
                    try:
                        with transaction.atomic():
                            self.add_candidate(candidate, position_unit, position_name, party)

                            messages.success(request, 'Candidate successfully added.')
                    except IntegrityError:
                        messages.error(request,
                                       'A candidate with the same name or position and party has already been added.')
                    except Voter.DoesNotExist:
                        messages.error(request, 'That student does not exist or has not yet been registered in here.')
                    except Position.DoesNotExist:
                        messages.error(request, 'That position does not exist.')
                    except Party.DoesNotExist:
                        messages.error(request, 'That party does not exist.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            elif form_type == 'delete-candidate':
                # The submitted form is for deleting voters
                candidates_list = request.POST.getlist('candidates')

                if candidates_list is not False and len(candidates_list) > 0:
                    try:
                        candidates_deleted = 0

                        # Try to delete each candidate in the list
                        with transaction.atomic():
                            for candidate in candidates_list:
                                self.delete_candidate(candidate)

                                candidates_deleted += 1

                            messages.success(request,
                                             "All {0} candidate(s) successfully deleted.".format(candidates_deleted))
                    except User.DoesNotExist:
                        # If the user does not exist
                        messages.error(request,
                                       'One of the selected candidates do not exist in the first place. '
                                       'No candidates were deleted.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            elif form_type == 'add-issue':
                # The submitted form is for adding an issue
                if issue_form.is_valid():
                    # Save the form to the database if it is valid
                    issue_form.save()

                    messages.success(request, 'Issue successfully added.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Could not add this issue.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            elif form_type == 'change-take':
                action = request.POST.get('action', False)
                issue = request.POST.get('take-issue', False)
                candidate = request.POST.get('take-candidate', False)
                response = request.POST.get('take-response', False)

                if action is not False and issue is not False and candidate is not False and response is not False:
                    # Check for missing data
                    try:
                        # Clean the input
                        candidate_details = candidate.split(":", 2)

                        if len(candidate_details) != 2:
                            raise ValueError

                        candidate = candidate_details[0].strip()
                    except ValueError:
                        messages.error(request,
                                       'Invalid candidate details.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)
                    if action == 'Save changes':
                        # Try to add or edit the take
                        try:
                            with transaction.atomic():
                                self.add_or_edit_take(candidate, issue, response)

                                messages.success(request, 'Take successfully updated.')
                        except IntegrityError:
                            messages.error(request,
                                           'That candidate already has a take on that issue.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)
                    elif action == 'Delete this Take':
                        # Try to delete this take
                        try:
                            with transaction.atomic():
                                self.delete_take(candidate, issue)

                                messages.success(request, 'Take successfully deleted.')
                        except Take.DoesNotExist:
                            messages.error(request,
                                           'That take does not exist.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)
                    else:
                        # If the action for this form is unknown, it's an invalid request, so stay on the page and then
                        # show an error  message
                        messages.error(request, 'Invalid request.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an
                    # error message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            else:
                # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                # message
                messages.error(request, 'Invalid request.')

                context = self.display_objects(1)

                return render(request, self.template_name, context)
        else:
            # If no objects are received, it's an invalid request, so stay on the page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)


class OfficersView(SysadminView):
    template_name = 'sysadmin/admin-officer.html'

    # A convenience function for deleting an officer
    @staticmethod
    def delete_officer(officer_id):
        # Retrieve the officer
        officer = User.objects.get(id=officer_id)

        # Get rid of that user
        officer.delete()

    def display_objects(self, page, query=False):
        # Show everything if the query is empty
        if query is False:
            officers = User.objects.all().order_by('username').filter(groups__name='comelec')
        else:
            officers = User.objects.filter(groups__name='comelec').filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            ) \
                .order_by('username')

        colleges = College.objects.all().order_by('name')

        paginator = Paginator(officers, self.objects_per_page)
        paginated_officers = paginator.get_page(page)

        officer_form = OfficerForm()

        context = {
            'officers': paginated_officers,
            'colleges': colleges,
            'officer_form': officer_form
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)
        query = request.GET.get('query', False)

        context = self.display_objects(page if page is not False else 1, query)

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        officer_form = OfficerForm(request.POST)

        if form_type is not False:
            if form_type == 'add-officer':
                # The submitted form is for adding an officer
                if officer_form.is_valid():
                    with transaction.atomic():
                        # Save the form to the database if it is valid
                        officer = officer_form.save()

                        # Set the correctly hashed password
                        officer.set_password(officer_form.cleaned_data['password'])

                        # Add the officer to the COMELEC officer group
                        group = Group.objects.get(name='comelec')
                        group.user_set.add(officer)

                        officer.save()

                        messages.success(request, 'Officer successfully added.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Could not add this officer.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            elif form_type == 'delete-officer':
                # The submitted form is for deleting officers
                officers_list = request.POST.getlist('officers')

                if officers_list is not False and len(officers_list) > 0:
                    try:
                        officers_deleted = 0

                        # Try to delete each voter in the list
                        with transaction.atomic():
                            for officer in officers_list:
                                self.delete_officer(officer)

                                officers_deleted += 1

                            messages.success(request,
                                             "All {0} officer(s) successfully deleted.".format(officers_deleted))
                    except User.DoesNotExist:
                        # If the user does not exist
                        messages.error(request,
                                       'One of the selected users do not exist in the first place. '
                                       'No officers were deleted.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            else:
                # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                # message
                messages.error(request, 'Invalid request.')

                context = self.display_objects(1)

                return render(request, self.template_name, context)
        else:
            # If no objects are received, it's an invalid request, so stay on the page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)


class UnitView(SysadminView):
    template_name = 'sysadmin/admin-unit.html'

    # A convenience function for deleting a unit
    @staticmethod
    def delete_unit(unit_id):
        # Retrieve the unit
        unit = Unit.objects.get(id=unit_id)

        # Get rid of that unit
        unit.delete()

    def display_objects(self, page, query=False):
        # Show everything if the query is empty
        if query is False:
            units = Unit.objects.all().order_by('college', 'batch', 'name')
        else:
            units = Unit.objects.filter(
                Q(name__icontains=query) |
                Q(college__name__icontains=query) |
                Q(batch__icontains=query)
            ) \
                .order_by('college', 'batch', 'name')

        colleges = College.objects.all().order_by('name')

        paginator = Paginator(units, self.objects_per_page)
        paginated_units = paginator.get_page(page)

        unit_form = UnitForm()

        context = {
            'units': paginated_units,
            'colleges': colleges,
            'unit_form': unit_form
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)
        query = request.GET.get('query', False)

        context = self.display_objects(page if page is not False else 1, query)

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        unit_form = UnitForm(request.POST)

        if form_type is not False:
            if form_type == 'add-unit':
                # The submitted form is for adding a unit
                if unit_form.is_valid():
                    with transaction.atomic():
                        # Save the form to the database if it is valid
                        unit_form.save()

                        messages.success(request, 'Unit successfully added.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Could not add this unit.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            elif form_type == 'delete-unit':
                # The submitted form is for deleting units
                units_list = request.POST.getlist('units')

                if units_list is not False and len(units_list) > 0:
                    try:
                        units_deleted = 0

                        # Try to delete each unit in the list
                        with transaction.atomic():
                            for unit in units_list:
                                self.delete_unit(unit)

                                units_deleted += 1

                            messages.success(request,
                                             "All {0} unit(s) successfully deleted.".format(units_deleted))
                    except Unit.DoesNotExist:
                        # If the unit does not exist
                        messages.error(request,
                                       'One of the selected units do not exist in the first place. '
                                       'No unit were deleted.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            else:
                # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                # message
                messages.error(request, 'Invalid request.')

                context = self.display_objects(1)

                return render(request, self.template_name, context)
        else:
            # If no objects are received, it's an invalid request, so stay on the page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)


@user_passes_test(sysadmin_test_func)
def json_details(request, voter_id):
    # Get the voter
    try:
        voter = Voter.objects.get(user__username=voter_id)
    except Voter.DoesNotExist:
        return JsonResponse({'response': "(This voter does not exist)"})

    # Then return its details
    return JsonResponse({'first_names': voter.user.first_name, 'last_name': voter.user.last_name,
                         'id_number': voter.user.username, 'college': voter.college.name,
                         'voting_status': voter.voting_status, 'eligibility_status': voter.eligibility_status})


@user_passes_test(sysadmin_test_func)
def json_take(request, candidate_id, issue):
    # Get the take
    try:
        take = Take.objects.get(candidate__voter__user__username=candidate_id, issue__name=issue)
    except Take.DoesNotExist:
        return JsonResponse({'response': "(This candidate doesn't have a take on this issue yet)"})

    # Then return its response
    return JsonResponse({'response': take.response})
