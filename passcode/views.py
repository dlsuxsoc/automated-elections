# Create your views here.
import csv
import datetime
import json
import smtplib
from random import randint

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.contrib.sessions.models import Session
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError, connection
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

# Test function for this view
from vote.models import Voter, College, Candidate, ElectionStatus, Vote, Position, Issue, BasePosition, Unit


def officer_test_func(user):
    try:
        return Group.objects.get(name='comelec') in user.groups.all()
    except Group.DoesNotExist:
        return False


class RestrictedView(UserPassesTestMixin, View):
    # Check whether the user accessing this page is a system administrator or not
    def test_func(self):
        return officer_test_func(self.request.user)


class OfficerView(RestrictedView):
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


class VotersView(OfficerView):
    template_name = 'passcode/officer-voter.html'

    # A convenience function for creating a voter
    @staticmethod
    def create_voter(first_name, last_name, username, college_name, voting_status_name, eligibility_status_name):
        # Save the names in title case
        first_name = first_name.title()
        last_name = last_name.title()

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
        
        if ResultsView.is_election_ongoing() and not voting_status and eligibility_status:
            # Also check if his batch and college is in the election status
            if ElectionStatus.objects.filter(college=college, batch=int(username[:3])).count() > 0:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                server.ehlo()
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                
                msg = '''Subject: [COMELEC] Election is starting

Hello {} {},
Election has started.
Use this as your credential for submitting your vote:
User: {}
Pass: {}
                '''.format(
                    first_name,
                    last_name,
                    username,
                    password
                )

                # Send the email to the user
                server.sendmail(settings.EMAIL_HOST_USER, email, msg)

                server.quit()

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

        # Only allow editing while there are no elections ongoing and there are no votes in the database
        if not ResultsView.is_election_ongoing() and ResultsView.is_votes_empty():
            if form_type is not False:
                if form_type == 'edit-voter':
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
                                               ' added previously. No further voters were added. (Error at row ' + repr(
                                                   num_voters_added + 2) + ')')

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

                        current_row = 0

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

                                current_row += 1

                            # Display a success message after all voters have been successfully added
                            messages.success(request, 'All {0} voter(s) successfully added.'.format(num_voters_added))
                        except IntegrityError:
                            messages.error(request, 'A voter with that ID number already exists. (Error at row ' + repr(
                                current_row) + ')')
                        except College.DoesNotExist:
                            messages.error(request,
                                           'The uploaded list contained invalid voter data. No voters were added. '
                                           '(Error at row ' + repr(current_row) + ')')

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

                                messages.success(request,
                                                 "All {0} voter(s) successfully deleted.".format(voters_deleted))
                        except User.DoesNotExist:
                            # If the user does not exist
                            messages.error(request,
                                           'One of the selected users has not existed in the first place. '
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
        else:
            messages.error(request, 'You cannot do that now because there are still votes being tracked. There may be '
                                    'elections still ongoing, or you haven\'t archived the votes yet.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)


class CandidatesView(OfficerView):
    template_name = 'passcode/officer-candidate.html'

    def display_objects(self, page, query=False):
        # Show everything if the query is empty
        if query is False:
            candidates = Candidate.objects.all().order_by('voter__user__username')
        else:
            candidates = Candidate.objects.filter(
                Q(voter__user__username__icontains=query) |
                Q(voter__user__first_name__icontains=query) |
                Q(voter__user__last_name__icontains=query) |
                Q(position__base_position__name__icontains=query) |
                Q(position__unit__name=query) |
                Q(party__name__icontains=query)
            ) \
                .order_by('voter__user__username')

        paginator = Paginator(candidates, self.objects_per_page)
        paginated_candidates = paginator.get_page(page)

        context = {
            'candidates': paginated_candidates,
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)
        query = request.GET.get('query', False)

        context = self.display_objects(page if page is not False else 1, query)

        return render(request, self.template_name, context)

    def post(self, request):
        self.get(request)


class ResultsView(OfficerView):
    template_name = 'passcode/officer-results.html'

    def display_objects(self, page, query=False):
        # Retrieve all colleges
        colleges = College.objects.all().order_by('name')

        # Set a flag indicating whether elections have started or not
        election_ongoing = self.is_election_ongoing()

        # Show the checkbox page when the elections aren't on
        if not election_ongoing:
            # Get all batches from the batch of the current year until the batch of the year six years from the current
            # year
            current_year = datetime.datetime.now().year

            batches = ['1' + str(year)[2:] for year in range(current_year, current_year - 6, -1)]
            batches[-1] = batches[-1] + ' and below'

            # Retrieve all positions
            positions = Position.objects.all().order_by('base_position__name', 'unit__college__name', 'unit__name')

            if query is not False:
                # Count the votes of all candidates by position
                TOTAL_VOTES_QUERY = (
                    "WITH all_candidates AS (\n"
                    "	SELECT\n"
                    "		c.id AS 'CandidateID',\n"
                    "		c.position_id AS 'PositionID',\n"
                    "		IFNULL(vs.position_id, NULL) AS 'HasBeenVoted'\n"
                    "	FROM\n"
                    "		vote_candidate c\n"
                    "	LEFT JOIN\n"
                    "		vote_voteset vs ON c.id = vs.candidate_id\n"
                    "	UNION ALL\n"
                    "	SELECT\n"
                    "		vs.candidate_id AS 'CandidateID',\n"
                    "		vs.position_id AS 'PositionID',\n"
                    "		IFNULL(vs.position_id, NULL) AS 'HasBeenVoted'\n"
                    "	FROM\n"
                    "		vote_voteset vs\n"
                    "	WHERE\n"
                    "		vs.candidate_id IS NULL\n"
                    "),\n"
                    "raw_count_position AS (\n"
                    "	SELECT\n"
                    "		bp.name AS 'Position',\n"
                    "		u.name AS 'Unit',\n"
                    "		ac.'CandidateID' AS 'CandidateID',\n"
                    "		COUNT(ac.'HasBeenVoted') AS 'Votes'\n"
                    "	FROM\n"
                    "		all_candidates ac\n"
                    "	LEFT JOIN\n"
                    "		vote_position p ON ac.'PositionID' = p.id\n"
                    "	LEFT JOIN\n"
                    "		vote_baseposition bp ON p.base_position_id = bp.id\n"
                    "	LEFT JOIN\n"
                    "		vote_unit u ON p.unit_id = u.id\n"
                    "	WHERE\n"
                    "		p.identifier = %s\n"
                    "	GROUP BY\n"
                    "		ac.'PositionID', ac.'CandidateID'\n"
                    "),\n"
                    "candidate_name AS (\n"
                    "	SELECT\n"
                    "		rcp.'Position',\n"
                    "		rcp.'Unit',\n"
                    "		IFNULL(u.first_name || ' ' || u.last_name, '(abstained)') AS 'Candidate',\n"
                    "		p.name AS 'Party',\n"
                    "		rcp.'Votes'\n"
                    "	FROM\n"
                    "		raw_count_position rcp\n"
                    "	LEFT JOIN\n"
                    "		vote_candidate c ON rcp.'CandidateID' = c.id\n"
                    "	LEFT JOIN\n"
                    "		vote_voter v ON c.voter_id = v.id\n"
                    "	LEFT JOIN\n"
                    "		auth_user u ON v.user_id = u.id\n"
                    "	LEFT JOIN\n"
                    "		vote_party p ON c.party_id = p.id\n"
                    "),\n"
                    "party_name AS (\n"
                    "	SELECT\n"
                    "		cn.'Position' AS 'Position',\n"
                    "		cn.'Unit' AS 'Unit',\n"
                    "		cn.'Candidate' AS 'Candidate',\n"
                    "		CASE cn.'Candidate'\n"
                    "			WHEN '(abstained)' THEN '(abstained)'\n"
                    "			ELSE IFNULL(cn.'Party', 'Independent')\n"
                    "		END AS 'Party',\n"
                    "		cn.'Votes' AS 'Votes'\n"
                    "	FROM\n"
                    "		candidate_name cn\n"
                    ")\n"
                    "SELECT\n"
                    "	pn.'Position' AS 'Position',\n"
                    "	pn.'Unit' AS 'Unit',\n"
                    "	pn.'Candidate' AS 'Candidate',\n"
                    "	pn.'Party' AS 'Party',\n"
                    "	pn.'Votes' AS 'Votes'\n"
                    "FROM\n"
                    "	party_name pn\n"
                    "ORDER BY\n"
                    "	pn.'Position',\n"
                    "	pn.'Unit',\n"
                    "	pn.'Votes' DESC,\n"
                    "	pn.'Candidate';\n"
                )

                # Correctly format the query
                query_formatted = query.replace('-', '')

                vote_results = {}

                with connection.cursor() as cursor:
                    cursor.execute(TOTAL_VOTES_QUERY, [query_formatted])

                    vote_results[query] = cursor.fetchall()

                # Create a shorter JSON version of the results
                vote_results_json = {}

                for result in vote_results[query]:
                    print(result)

                    vote_results_json[result[2]] = result[4]

                vote_results_json = json.dumps(vote_results_json)

            context = {
                'election_ongoing': election_ongoing,
                'colleges': colleges,
                'batches': batches,
                'positions': positions,
                'vote_results': vote_results if query is not False else False,
                'vote_results_json': vote_results_json if query is not False else False,
                'identifier': query,
            }
        else:
            # Show the eligible batches when the elections are on
            college_batch_dict = {}

            college_batches = ElectionStatus.objects.all().order_by('college__name', '-batch')

            for college_batch in college_batches:
                if college_batch.college.name not in college_batch_dict.keys():
                    college_batch_dict[college_batch.college.name] = []

                college_batch_dict[college_batch.college.name].append(college_batch.batch)

            # As well as the the relevant data from the election
            votes = Vote.objects.all()

            # Overall votes
            overall_votes = votes.count()

            # Total registered voters
            overall_registered_voters = Voter.objects.count()
            
            # Voter turnout
            overall_turnout = overall_votes / overall_registered_voters * 100 if overall_registered_voters != 0 else 0

            # Votes today
            now = datetime.datetime.now()

            votes_today = votes.filter(timestamp__day=now.day)

            overall_votes_today = votes_today.count()

            reference_12 = now.replace(hour=12, minute=0, second=0, microsecond=0)
            reference_15 = now.replace(hour=15, minute=0, second=0, microsecond=0)
            reference_18 = now.replace(hour=18, minute=0, second=0, microsecond=0)

            votes_today_12 = votes_today.filter(timestamp__lte=reference_12).count()
            votes_today_15 = votes_today.filter(timestamp__lte=reference_15).count()
            votes_today_18 = votes_today.filter(timestamp__lte=reference_18).count()

            # Votes overall per day per batch
            BATCH_QUERY = (
                "WITH votes_12 AS (\n"
                "	SELECT\n"
                "		DATE(v12.timestamp) AS 'Date12',\n"
                "		SUBSTR(v12.voter_id_number, 0, 4) AS 'Batch12',\n"
                "		COUNT(v12.id) AS 'Count12'\n"
                "	FROM\n"
                "		vote_vote v12\n"
                "	WHERE\n"
                "		v12.timestamp <= DATETIME(v12.timestamp, 'start of day', '+12 hours')\n"
                "	GROUP BY\n"
                "		DATE(v12.timestamp),\n"
                "		SUBSTR(v12.voter_id_number, 0, 4)\n"
                "),\n"
                "votes_15 AS (\n"
                "	SELECT\n"
                "		DATE(v15.timestamp) AS 'Date15',\n"
                "		SUBSTR(v15.voter_id_number, 0, 4) AS 'Batch15',\n"
                "		COUNT(v15.id) AS 'Count15'\n"
                "	FROM\n"
                "		vote_vote v15\n"
                "	WHERE\n"
                "		v15.timestamp <= DATETIME(v15.timestamp, 'start of day', '+15 hours')\n"
                "	GROUP BY\n"
                "		DATE(v15.timestamp),\n"
                "		SUBSTR(v15.voter_id_number, 0, 4)\n"
                "),\n"
                "votes_18 AS (\n"
                "	SELECT\n"
                "		DATE(v18.timestamp) AS 'Date18',\n"
                "		SUBSTR(v18.voter_id_number, 0, 4) AS 'Batch18',\n"
                "		COUNT(v18.id) AS 'Count18'\n"
                "	FROM\n"
                "		vote_vote v18\n"
                "	WHERE\n"
                "		v18.timestamp <= DATETIME(v18.timestamp, 'start of day', '+18 hours')\n"
                "	GROUP BY\n"
                "		DATE(v18.timestamp),\n"
                "		SUBSTR(v18.voter_id_number, 0, 4)\n"
                ")\n"
                "SELECT\n"
                "	DATE(v.timestamp) AS 'Date',\n"
                "	SUBSTR(v.voter_id_number, 0, 4) AS 'Batch',\n"
                "	COUNT(v.id) 'Total Count',\n"
                "	IFNULL(votes_12.'Count12', 0) AS 'As of 12 nn',\n"
                "	IFNULL(votes_15.'Count15', 0) AS 'As of 3 pm',\n"
                "	IFNULL(votes_18.'Count18', 0) AS 'As of 6 pm'\n"
                "FROM\n"
                "	vote_vote v\n"
                "LEFT JOIN\n"
                "	votes_12 ON\n"
                "		DATE(v.timestamp) = votes_12.'Date12'\n"
                "		AND SUBSTR(v.voter_id_number, 0, 4) = votes_12.'Batch12'\n"
                "LEFT JOIN\n"
                "	votes_15 ON\n"
                "		DATE(v.timestamp) = votes_15.'Date15'\n"
                "		AND SUBSTR(v.voter_id_number, 0, 4) = votes_15.'Batch15'\n"
                "LEFT JOIN\n"
                "	votes_18 ON\n"
                "		DATE(v.timestamp) = votes_18.'Date18'\n"
                "		AND SUBSTR(v.voter_id_number, 0, 4) = votes_18.'Batch18'\n"
                "GROUP BY\n"
                "	DATE(v.timestamp),\n"
                "	SUBSTR(v.voter_id_number, 0, 4)\n"
                "ORDER BY\n"
                "   DATE(v.timestamp) DESC,\n"
                "   SUBSTR(v.voter_id_number, 0, 4) ASC\n"
            )

            batch_results = []

            with connection.cursor() as cursor:
                cursor.execute(BATCH_QUERY)

                batch_results.append(cursor.fetchall())

            # Get the eligible colleges
            eligible_colleges = ElectionStatus.objects.values('college').distinct()
            eligible_colleges = [College.objects.get(id=eligible_college['college']) for eligible_college in
                                 eligible_colleges]

            overall_votes_college = {}

            for eligible_college in eligible_colleges:
                overall_votes_college[eligible_college.name] = Vote.objects.filter(
                    voter_college=eligible_college.name).count()

            # Votes per day per college per batch
            COLLEGE_BATCH_QUERY = (
                "WITH votes_12 AS (\n"
                "	SELECT\n"
                "		DATE(v12.timestamp) AS 'Date12',\n"
                "		SUBSTR(v12.voter_id_number, 0, 4) AS 'Batch12',\n"
                "		COUNT(v12.id) AS 'Count12'\n"
                "	FROM\n"
                "		vote_vote v12\n"
                "	WHERE\n"
                "		v12.timestamp <= DATETIME(v12.timestamp, 'start of day', '+12 hours')\n"
                "		AND v12.voter_college = %s\n"
                "	GROUP BY\n"
                "		DATE(v12.timestamp),\n"
                "		SUBSTR(v12.voter_id_number, 0, 4)\n"
                "),\n"
                "votes_15 AS (\n"
                "	SELECT\n"
                "		DATE(v15.timestamp) AS 'Date15',\n"
                "		SUBSTR(v15.voter_id_number, 0, 4) AS 'Batch15',\n"
                "		COUNT(v15.id) AS 'Count15'\n"
                "	FROM\n"
                "		vote_vote v15\n"
                "	WHERE\n"
                "		v15.timestamp <= DATETIME(v15.timestamp, 'start of day', '+15 hours')\n"
                "		AND v15.voter_college = %s\n"
                "	GROUP BY\n"
                "		DATE(v15.timestamp),\n"
                "		SUBSTR(v15.voter_id_number, 0, 4)\n"
                "),\n"
                "votes_18 AS (\n"
                "	SELECT\n"
                "		DATE(v18.timestamp) AS 'Date18',\n"
                "		SUBSTR(v18.voter_id_number, 0, 4) AS 'Batch18',\n"
                "		COUNT(v18.id) AS 'Count18'\n"
                "	FROM\n"
                "		vote_vote v18\n"
                "	WHERE\n"
                "		v18.timestamp <= DATETIME(v18.timestamp, 'start of day', '+18 hours')\n"
                "		AND v18.voter_college = %s\n"
                "	GROUP BY\n"
                "		DATE(v18.timestamp),\n"
                "		SUBSTR(v18.voter_id_number, 0, 4)\n"
                ")\n"
                "SELECT\n"
                "	DATE(v.timestamp) AS 'Date',\n"
                "	SUBSTR(v.voter_id_number, 0, 4) AS 'Batch',\n"
                "	COUNT(v.id) 'Total Count',\n"
                "	IFNULL(votes_12.'Count12', 0) AS 'As of 12 nn',\n"
                "	IFNULL(votes_15.'Count15', 0) AS 'As of 3 pm',\n"
                "	IFNULL(votes_18.'Count18', 0) AS 'As of 6 pm'\n"
                "FROM\n"
                "	vote_vote v\n"
                "LEFT JOIN\n"
                "	votes_12 ON\n"
                "		DATE(v.timestamp) = votes_12.'Date12'\n"
                "		AND SUBSTR(v.voter_id_number, 0, 4) = votes_12.'Batch12'\n"
                "LEFT JOIN\n"
                "	votes_15 ON\n"
                "		DATE(v.timestamp) = votes_15.'Date15'\n"
                "		AND SUBSTR(v.voter_id_number, 0, 4) = votes_15.'Batch15'\n"
                "LEFT JOIN\n"
                "	votes_18 ON\n"
                "		DATE(v.timestamp) = votes_18.'Date18'\n"
                "		AND SUBSTR(v.voter_id_number, 0, 4) = votes_18.'Batch18'\n"
                "WHERE\n"
                "	v.voter_college = %s\n"
                "GROUP BY\n"
                "	DATE(v.timestamp),\n"
                "	SUBSTR(v.voter_id_number, 0, 4)\n"
                "ORDER BY\n"
                "   DATE(v.timestamp) DESC,\n"
                "   SUBSTR(v.voter_id_number, 0, 4) ASC\n"
            )

            college_batch_results = {}

            for eligible_college in eligible_colleges:
                with connection.cursor() as cursor:
                    cursor.execute(COLLEGE_BATCH_QUERY,
                                   [eligible_college.name,
                                    eligible_college.name,
                                    eligible_college.name,
                                    eligible_college.name]
                                   )

                    college_batch_results[eligible_college.name] = cursor.fetchall()

            context = {
                'election_ongoing': election_ongoing,
                'colleges': colleges,
                'college_batch_dict': college_batch_dict,
                'overall_votes': overall_votes,
                'overall_registered_voters': overall_registered_voters,
                'overall_turnout': overall_turnout,
                'overall_votes_today': overall_votes_today,
                'votes_today_12': (votes_today_12 if now.time() >= reference_12.time() else None),
                'votes_today_15': (votes_today_15 if now.time() >= reference_15.time() else None),
                'votes_today_18': (votes_today_18 if now.time() >= reference_18.time() else None),
                'batch_results': batch_results,
                'eligible_colleges': eligible_colleges,
                'overall_votes_college': overall_votes_college,
                'college_batch_results': college_batch_results
            }

        return context

    @staticmethod
    def is_election_ongoing():
        return ElectionStatus.objects.all().exists()

    @staticmethod
    def is_votes_empty():
        return not Vote.objects.all().exists()

    # Generate a random passcode for a user
    @staticmethod
    def generate_passcode():
        # Length of the passcode
        length = 8

        # The character domain of the passcode
        charset = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNOPQRSTUVWXYZ0123456789'

        # The passcode to be generated
        passcode = ''

        # Generate a random passcode of specified length
        for index in range(length):
            passcode += charset[randint(0, len(charset) - 1)]

        return passcode

    def get(self, request):
        page = request.GET.get('page', False)
        query = request.GET.get('query', False)

        context = self.display_objects(page if page is not False else 1, query)

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        if form_type is not False:
            # The submitted form is for starting the elections
            if form_type == 'start-elections':
                # If the elections have already started, it can't be started again!
                if self.is_election_ongoing():
                    messages.error(request, 'The elections have already been started.')
                elif not self.is_votes_empty():
                    # If there still are votes left from the previous elections, the elections can't be started yet
                    messages.error(request,
                                   'The votes from the previous election haven\'t been archived yet. Archive them '
                                   'first before starting this election.')
                else:
                    # Only continue if the re-authentication password indeed matches the password of the current
                    # COMELEC officer
                    reauth_password = request.POST.get('reauth', False)

                    if reauth_password is False \
                            or authenticate(username=request.user.username, password=reauth_password) is None:
                        messages.error(request,
                                       'The elections weren\'t started because the password was incorrect. Try again.')
                    else:
                        college_batches = {}

                        # Collect all batches per college
                        for college in College.objects.all().order_by('name'):
                            college_batches[college.name] = request.POST.getlist(college.name + '-batch')

                        # Keep track of whether no checkboxes where checked
                        empty = True

                        # List of all voters
                        voters = [ ]

                        # Add each into the database
                        for college, batches in college_batches.items():
                            # Get the college object from the name
                            try:
                                college_object = College.objects.get(name=college)

                                # Then use that object to create the an election status value for these specific batches
                                for batch in batches:
                                    empty = False

                                    ElectionStatus.objects.create(college=college_object, batch=batch)
                                    batch_voters = list(
                                        Voter.objects.filter(
                                            college=college_object,
                                            user__username__startswith=str(batch),
                                            voting_status=False,
                                            eligibility_status=True
                                        ).values('user__email', 'user__first_name', 'user__last_name', 'user__username')
                                    )

                                    # print(batch_voters)
                                    voters += batch_voters
                            except College.DoesNotExist:
                                # If the college does not exist
                                messages.error(request, 'Internal server error.')

                        # Check whether batches were actually selected in the first place
                        if not empty:
                            # Email every student once election starts
                            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                            server.ehlo()
                            server.starttls()
                            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                            
                            for voter in voters:
                                # Limit to 1 email for testing
                                if(voter['user__email'] == '11731788@dlsu.edu.ph'):
                                # Create a new passcode for the student
                                    passcode = self.generate_passcode()
                                    msg = '''Subject: [COMELEC] Election is starting

    Hello {} {},
    Election has started.
    Use this as your credential for submitting your vote:
    User: {}
    Pass: {}
                                    '''.format(
                                        voter['user__first_name'],
                                        voter['user__last_name'],
                                        voter['user__username'],
                                        passcode
                                    )

                                    # Send the email to the user
                                    server.sendmail(settings.EMAIL_HOST_USER, voter['user__email'], msg)

                                    # Save the new pass code to the database
                                    user = User.objects.get(username=voter['user__username'])
                                    user.set_password(passcode)
                                    user.save()

                            server.quit()
                            messages.success(request, 'The elections have now started.')
                        else:
                            messages.error(request,
                                           'The elections weren\'t started because there were no batches selected at'
                                           ' all.')

                context = self.display_objects(1)

                return render(request, self.template_name, context)
            elif form_type == 'end-elections':
                # If the elections have already ended, it can't be ended again!
                if self.is_election_ongoing():
                    # Only continue if the re-authentication password indeed matches the password of the current
                    # COMELEC officer
                    reauth_password = request.POST.get('reauth', False)

                    if reauth_password is False \
                            or authenticate(username=request.user.username, password=reauth_password) is None:
                        messages.error(request,
                                       'The elections weren\'t ended because the password was incorrect. Try again.')
                    else:
                        # Clear the entire election status table
                        ElectionStatus.objects.all().delete()

                        messages.success(request, 'The elections have now ended.')
                else:
                    messages.error(request, 'The elections have already been ended.')

                context = self.display_objects(1)

                return render(request, self.template_name, context)
            elif form_type == 'archive':
                # If there are elections ongoing, no archiving may be done yet
                if self.is_election_ongoing():
                    messages.error(request, 'You may not archive while the elections are ongoing.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                elif self.is_votes_empty():
                    # If there no votes to archive, what's the point?
                    messages.error(request,
                                   'There aren\'t any election results to archive yet.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # The submitted form is for archiving the election results
                    # Only continue if the re-authentication password indeed matches the password of the current
                    # COMELEC officer
                    reauth_password = request.POST.get('reauth-archive', False)

                    if reauth_password is False \
                            or authenticate(username=request.user.username, password=reauth_password) is None:
                        messages.error(request,
                                       'The election results weren\'t archived because the password was incorrect. '
                                       'Try again.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)
                    else:
                        with transaction.atomic():
                            # Count the votes of all candidates
                            TOTAL_VOTES_QUERY = (
                                "WITH all_candidates AS (\n"
                                "	SELECT\n"
                                "		c.id AS 'CandidateID',\n"
                                "		c.position_id AS 'PositionID',\n"
                                "		IFNULL(vs.position_id, NULL) AS 'HasBeenVoted'\n"
                                "	FROM\n"
                                "		vote_candidate c\n"
                                "	LEFT JOIN\n"
                                "		vote_voteset vs ON c.id = vs.candidate_id\n"
                                "	UNION ALL\n"
                                "	SELECT\n"
                                "		vs.candidate_id AS 'CandidateID',\n"
                                "		vs.position_id AS 'PositionID',\n"
                                "		IFNULL(vs.position_id, NULL) AS 'HasBeenVoted'\n"
                                "	FROM\n"
                                "		vote_voteset vs\n"
                                "	WHERE\n"
                                "		vs.candidate_id IS NULL\n"
                                "),\n"
                                "raw_count_position AS (\n"
                                "	SELECT\n"
                                "		bp.name AS 'Position',\n"
                                "		u.name AS 'Unit',\n"
                                "		ac.'CandidateID' AS 'CandidateID',\n"
                                "		COUNT(ac.'HasBeenVoted') AS 'Votes'\n"
                                "	FROM\n"
                                "		all_candidates ac\n"
                                "	LEFT JOIN\n"
                                "		vote_position p ON ac.'PositionID' = p.id\n"
                                "	LEFT JOIN\n"
                                "		vote_baseposition bp ON p.base_position_id = bp.id\n"
                                "	LEFT JOIN\n"
                                "		vote_unit u ON p.unit_id = u.id\n"
                                "	GROUP BY\n"
                                "		ac.'PositionID', ac.'CandidateID'\n"
                                "),\n"
                                "candidate_name AS (\n"
                                "	SELECT\n"
                                "		rcp.'Position',\n"
                                "		rcp.'Unit',\n"
                                "		IFNULL(u.first_name || ' ' || u.last_name, '(abstained)') AS 'Candidate',\n"
                                "		p.name AS 'Party',\n"
                                "		rcp.'Votes'\n"
                                "	FROM\n"
                                "		raw_count_position rcp\n"
                                "	LEFT JOIN\n"
                                "		vote_candidate c ON rcp.'CandidateID' = c.id\n"
                                "	LEFT JOIN\n"
                                "		vote_voter v ON c.voter_id = v.id\n"
                                "	LEFT JOIN\n"
                                "		auth_user u ON v.user_id = u.id\n"
                                "	LEFT JOIN\n"
                                "		vote_party p ON c.party_id = p.id\n"
                                "),\n"
                                "party_name AS (\n"
                                "	SELECT\n"
                                "		cn.'Position' AS 'Position',\n"
                                "		cn.'Unit' AS 'Unit',\n"
                                "		cn.'Candidate' AS 'Candidate',\n"
                                "		CASE cn.'Candidate'\n"
                                "			WHEN '(abstained)' THEN '(abstained)'\n"
                                "			ELSE IFNULL(cn.'Party', 'Independent')\n"
                                "		END AS 'Party',\n"
                                "		cn.'Votes' AS 'Votes'\n"
                                "	FROM\n"
                                "		candidate_name cn\n"
                                ")\n"
                                "SELECT\n"
                                "	pn.'Position' AS 'Position',\n"
                                "	pn.'Unit' AS 'Unit',\n"
                                "	pn.'Candidate' AS 'Candidate',\n"
                                "	pn.'Party' AS 'Party',\n"
                                "	pn.'Votes' AS 'Votes'\n"
                                "FROM\n"
                                "	party_name pn\n"
                                "ORDER BY\n"
                                "	pn.'Position',\n"
                                "	pn.'Unit',\n"
                                "	pn.'Votes' DESC,\n"
                                "	pn.'Candidate';\n"
                            )

                            vote_results = {}

                            with connection.cursor() as cursor:
                                cursor.execute(TOTAL_VOTES_QUERY, [])

                                columns = [col[0] for col in cursor.description]
                                vote_results['results'] = cursor.fetchall()

                            # Create a response object, and classify it as a CSV response
                            response = HttpResponse(content_type='text/csv')
                            response['Content-Disposition'] = 'attachment; filename="results.csv"'

                            # Then write the results to a CSV file
                            writer = csv.writer(response)

                            writer.writerow(columns)

                            for row in vote_results['results']:
                                writer.writerow(list(row))

                            # Clear all users who are voters
                            # This also clears the following tables: voters, candidates, takes, vote set
                            User.objects.filter(groups__name='voter').delete()

                            # Clear all issues
                            Issue.objects.all().delete()

                            # Clear all votes
                            Vote.objects.all().delete()

                            # Clear all batch positions
                            Position.objects.filter(base_position__type=BasePosition.BATCH).delete()

                            # Clear all batch units
                            Unit.objects.filter(college__isnull=False, batch__isnull=False)

                            # Show a Save As box so the user may download it
                            return response
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


class PasscodeView(UserPassesTestMixin, View):
    template_name = 'passcode/password_generator.html'

    # Check whether the user id of the queried user is currently in
    @staticmethod
    def is_currently_in(user_id):
        # Query all non-expired sessions
        # use timezone.now() instead of datetime.now() in latest versions of Django
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        uid_list = []

        # Build a list of user ids from that query
        for session in sessions:
            data = session.get_decoded()
            uid_list.append(data.get('_auth_user_id', None))

        print(User.objects.filter(id__in=uid_list))

        # Query all logged in users based on id list
        return User.objects.filter(id=user_id, id__in=uid_list).count() > 0

    # Generate a random passcode for a user
    @staticmethod
    def generate_passcode():
        # Length of the passcode
        length = 8

        # The character domain of the passcode
        charset = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNOPQRSTUVWXYZ0123456789'

        # The passcode to be generated
        passcode = ''

        # Generate a random passcode of specified length
        for index in range(length):
            passcode += charset[randint(0, len(charset) - 1)]

        return passcode

    # Check whether the user accessing this page is a COMELEC officer or not
    def test_func(self):
        try:
            return Group.objects.get(name='comelec') in self.request.user.groups.all()
        except Group.DoesNotExist:
            return False

    def get(self, request):
        # Get this page
        context = {'message': ''}

        return render(request, self.template_name, context)

    def post(self, request):
        # Set error messages up
        DOES_NOT_EXIST = 'DNE'
        ALREADY_IN = 'AI'
        ALREADY_VOTED = 'AV'
        INELIGIBLE = 'IE'
        INVALID_REQUEST = 'IR'

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
                # Get the user and voter associated with that ID number
                id_number = id_number.strip()

                user = User.objects.get(username=id_number)
                voter = Voter.objects.get(user__username=id_number)

                # Check if that user is eligible at all
                if voter.eligibility_status and ElectionStatus.objects.filter(
                        college__name=voter.college.name).count() > 0:
                    # Check if that user has already voted
                    if not voter.voting_status:
                        # FIXME: is_currently_in() does not work yet
                        # Check if that user is currently logged in
                        if not self.is_currently_in(user.id):
                            # Generate a passcode
                            passcode = self.generate_passcode()

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
                            context = {'message': ALREADY_IN}
                    else:
                        # If the voter has already voted, the passcode can't be changed for that voter anymore
                        context = {'message': ALREADY_VOTED}
                else:
                    # If the voter is not eligible (or the voter's college is not eligible), don't churn out a passcode
                    context = {'message': INELIGIBLE}
            except (User.DoesNotExist, Voter.DoesNotExist):
                # That user does not exist, so return a does not exist error.
                context = {'message': DOES_NOT_EXIST}
        else:
            # Send back an invalid request error.
            context = {'message': INVALID_REQUEST}

        # Go back to this page
        return render(request, self.template_name, context)


@user_passes_test(officer_test_func)
def json_details(request, voter_id):
    # Get the voter
    try:
        voter = Voter.objects.get(user__username=voter_id)
    except Voter.DoesNotExist:
        return JsonResponse({'response': "(This voter does not exist)"})

    print({'first_names': voter.user.first_name, 'last_name': voter.user.last_name,
           'id_number': voter.user.username, 'college': voter.college.name,
           'voting_status': voter.voting_status, 'eligibility_status': voter.eligibility_status})

    # Then return its details
    return JsonResponse({'first_names': voter.user.first_name, 'last_name': voter.user.last_name,
                         'id_number': voter.user.username, 'college': voter.college.name,
                         'voting_status': voter.voting_status, 'eligibility_status': voter.eligibility_status})
