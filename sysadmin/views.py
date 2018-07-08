# Create your views here.

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import render
from django.views import View

from passcode.views import generate_passcode
from sysadmin.forms import CandidateForm, IssueForm
from vote.models import Voter, College, Candidate, Position, Unit


class SysadminView(UserPassesTestMixin, View):
    template_name = ''

    # Defines the number of objects shown in a page
    objects_per_page = 6

    # Check whether the user accessing this page is a system administrator or not
    def test_func(self):
        try:
            return Group.objects.get(name='sysadmin') in self.request.user.groups.all()
        except Group.DoesNotExist:
            return False

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
        password = generate_passcode()

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

        # Create and return the voter using the created user
        return Voter.objects.create(user=user, college=college,
                                    voting_status=voting_status, eligibility_status=eligibility_status)

    # A convenience function for changing a voter
    @staticmethod
    def change_voter_eligibility(voter_id, eligibility_status_name):
        # Retrieve the voter in question
        voter = Voter.objects.get(id=voter_id)

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
        # Search for everything if the query is empty

        if query is False:
            voters = Voter.objects.all().order_by('user__username')
        else:
            voters = Voter.objects.filter(
                Q(user__username__contains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query)
            ) \
                .order_by('user__username')

        colleges = College.objects.all().order_by('name')

        paginator = Paginator(voters, self.objects_per_page)
        paginated_voters = paginator.get_page(page)

        context = {
            'voters': paginated_voters,
            'colleges': colleges
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
                print(request.POST)

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

    def display_objects(self, page):
        candidates = Candidate.objects.all().order_by('voter__user__username')
        positions = Position.objects.all().order_by('name')

        paginator = Paginator(candidates, self.objects_per_page)
        paginated_candidates = paginator.get_page(page)

        candidate_form = CandidateForm()
        issue_form = IssueForm()

        context = {
            'candidates': paginated_candidates,
            'positions': positions,
            'candidate_form': candidate_form,
            'issue_form': issue_form
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)

        context = self.display_objects(page if page is not False else 1)

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        candidate_form = CandidateForm(request.POST)
        issue_form = IssueForm(request.POST)

        if form_type is not False:
            # The submitted form is for adding a candidate
            if form_type == 'add-candidate':
                if candidate_form.is_valid():
                    # Save the form to the database if it is valid
                    candidate_form.save()

                    messages.success(request, 'Candidate successfully added.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Could not add this candidate.')

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

    def display_objects(self, page):
        officers = User.objects.all().order_by('username').filter(groups__name='comelec')
        colleges = College.objects.all().order_by('name')

        paginator = Paginator(officers, self.objects_per_page)
        paginated_officers = paginator.get_page(page)

        context = {
            'officers': paginated_officers,
            'colleges': colleges
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)

        context = self.display_objects(page if page is not False else 1)

        return render(request, self.template_name, context)

    def post(self, request):
        return render(request, self.template_name)


class UnitView(SysadminView):
    template_name = 'sysadmin/admin-unit.html'

    def display_objects(self, page):
        units = Unit.objects.all().order_by('college', 'batch', 'name')
        colleges = College.objects.all().order_by('name')

        paginator = Paginator(units, self.objects_per_page)
        paginated_units = paginator.get_page(page)

        context = {
            'units': paginated_units,
            'colleges': colleges
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)

        context = self.display_objects(page if page is not False else 1)

        return render(request, self.template_name, context)

    def post(self, request):
        return render(request, self.template_name)
