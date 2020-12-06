# Create your views here.
import csv
import datetime
from email.mime.image import MIMEImage

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction, connection
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import View
from zipfile import ZipFile, ZIP_DEFLATED

from passcode.views import PasscodeView, ResultsView
from sysadmin.forms import IssueForm, OfficerForm, UnitForm, PositionForm, PollForm
from vote.models import Vote, Voter, College, Candidate, ElectionStatus, Position, Unit, Party, Issue, Take, BasePosition, Poll, Election, ElectionState


# Test function for this view
def sysadmin_test_func(user):
    try:
        return Group.objects.get(name='sysadmin') in user.groups.all()
    except Group.DoesNotExist:
        return False

# EMAIL BODY CONST
fp = open(settings.BASE_DIR + '/email_template.html', 'r')
HTML_STR = fp.read()
fp.close()

def send_email(voter_id, voter_key = None):
    if voter_key == None:
        voter_key = PasscodeView.generate_passcode()

        user = User.objects.get(username=voter_id)
        user.set_password(voter_key)
        user.save()

    voter_email = voter_id + '@dlsu.edu.ph'

    # Create email with message and template
    # Imbedded Image
    fp = open(settings.BASE_DIR + '/ComelecLogo.png', 'rb')
    img = MIMEImage(fp.read())
    fp.close()
    img.add_header('Content-ID', '<logo>')

    subject = '[COMELEC] Election is now starting'
    text = '''\
DLSU Comelec is inviting to you to vote in the elections.
Voter ID: {}
Voter Key: {}
To vote, go to this link: https://some_link
    '''.format(voter_id, voter_key)

    html = HTML_STR
    html = html.replace('11xxxxxx', voter_id, 2)
    html = html.replace('xxxxxxxx', voter_key, 1)

    msg = EmailMultiAlternatives(
        subject = subject,
        body = text,
        from_email = settings.EMAIL_HOST_USER,
        to = [ voter_email ]
    )
    msg.attach_alternative(html, "text/html")
    msg.attach(img)
    msg.send()

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

class ElectionsView(SysadminView):
    template_name = 'sysadmin/admin-elections.html'
    
    @staticmethod
    def is_votes_empty():
        return not Vote.objects.all().exists()

    @staticmethod
    def get_election_state():
        try:
            return Election.objects.latest('timestamp').state
        except:
            return None

    @staticmethod
    def get_context():
        # Retrieve all colleges
        colleges = College.objects.all().order_by('name')

        # Set a flag indicating whether elections have started or not
        election_state = ElectionsView.get_election_state()

        audits = []

        AUDITS_QUERY = (
            "SELECT\n"
            "    a.username AS \"ID Number\",\n"
            "    x.ts AS \"Timestamp\"\n"
            "FROM\n"
            "    xaction AS x\n"
            "INNER JOIN\n"
            "    auth_user AS a\n"
            "ON\n"
            "    x.user_id=a.id\n"
            "WHERE\n"
            "    x.entity_id=1 AND x.xaction_type=\"I\"\n"
            "ORDER BY\n"
            "    x.id DESC\n"
            "LIMIT\n"
            "    100"
        )

        with connection.cursor() as cursor:
            cursor.execute(AUDITS_QUERY)

            audits.append(cursor.fetchall())

        context = {}

        if not election_state or election_state == ElectionState.ARCHIVED.value:
            # Get all batches from the batch of the current year until the batch of the year six years from the current
            # year
            current_year = datetime.datetime.now().year

            batches = ['1' + str(year)[2:] for year in range(current_year, current_year - 6, -1)]
            batches[-1] = batches[-1] + ' and below'

            context = {
                'election_state': election_state,
                'colleges': colleges,
                'batches': batches,
                'audits': audits,
            }
        else:
            # Show the eligible batches when the elections are on
            college_batch_dict = {}

            college_batches = ElectionStatus.objects.all().order_by('college__name', '-batch')

            for college_batch in college_batches:
                if college_batch.college.name not in college_batch_dict.keys():
                    college_batch_dict[college_batch.college.name] = []

                college_batch_dict[college_batch.college.name].append(college_batch.batch)
            
            context = {
                'college_batch_dict': college_batch_dict,
                'election_state': election_state,
                'colleges': colleges,
                'audits': audits,
            }
        
        return context

    def get(self, request):
        context = self.get_context()

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        election_state = ElectionsView.get_election_state()

        if form_type is not False:
            # The submitted form is for starting the elections
            if form_type == 'start-elections':
                # If the elections have already started, it can't be started again!
                if (election_state and election_state != ElectionState.ARCHIVED.value) or not self.is_votes_empty():
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

                                    Election.objects.create(state=ElectionState.ONGOING.value)

                                    ElectionStatus.objects.create(college=college_object, batch=batch)
                                    # Include all ID numbers below the specified batch number e.g. <= 115XXXXX
                                    if 'and below' in batch: 
                                        starting_batch = batch.split()[0]
                                        starting_batch += "99999"
                                        batch_voters = list(
                                            Voter.objects.filter(
                                                college=college_object,
                                                user__username__lte=starting_batch,
                                                voting_status=False,
                                                eligibility_status=True
                                            ).values('user__username')
                                        )
                                    # Include just the batch e.g. 118XXXXX
                                    else: 
                                        batch_voters = list(
                                            Voter.objects.filter(
                                                college=college_object,
                                                user__username__startswith=str(batch),
                                                voting_status=False,
                                                eligibility_status=True
                                            ).values('user__username')
                                        )
                                    # print(batch_voters)
                                    voters += batch_voters
                            except College.DoesNotExist:
                                # If the college does not exist
                                messages.error(request, 'Internal server error.')

                        # Check whether batches were actually selected in the first place
                        if not empty:
                            for index, voter in enumerate(voters):
                                send_email(voter['user__username'])
                                print('Email sent to ' + voter['user__username'] + '.' + str(index) + ' out of ' + str(len(voters)) + ' sent.')

                            messages.success(request, 'The elections have now started.')
                        else:
                            messages.error(request,
                                           'The elections weren\'t started because there were no batches selected at'
                                           ' all.')

                context = self.get_context()

                return render(request, self.template_name, context)

            elif form_type == 'end-elections':
                # If the elections have already ended, it can't be ended again!
                if election_state == ElectionState.ONGOING.value or election_state == ElectionState.PAUSED.value:
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

                        e = Election.objects.latest('timestamp')
                        e.state = ElectionState.BLOCKED.value
                        e.save()

                        messages.success(request, 'The elections have now ended.')
                else:
                    messages.error(request, 'The elections have already been ended.')

                context = self.get_context()

                return render(request, self.template_name, context)

            elif form_type == 'archive-results':
                # If there are elections ongoing, no archiving may be done yet
                if election_state != ElectionState.FINISHED.value:
                    messages.error(request, 'You may not archive while the elections are not yet finished.')

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

                            TOTAL_POLL_VOTES_QUERY = (
                                "SELECT\n"
                                "   p.'name' AS 'Question',\n"
                                "   SUM((CASE WHEN ps.'answer' = 'yes' THEN 1 ELSE 0 END)) AS 'Yes',\n"
                                "   SUM((CASE WHEN ps.'answer' = 'no' THEN 1 ELSE 0 END)) AS 'No'\n"
                                "FROM\n"
                                "   vote_pollset ps\n"
                                "LEFT JOIN\n"
                                "   vote_poll p\n"
                                "ON\n"
                                "   ps.'poll_id' = p.'id'\n"
                                "GROUP BY\n"
                                "   p.'id';\n"
                            )

                            vote_results = {}
                            poll_results = {}

                            with connection.cursor() as cursor:
                                cursor.execute(TOTAL_VOTES_QUERY, [])

                                columns = [col[0] for col in cursor.description]
                                vote_results['results'] = cursor.fetchall()

                            with connection.cursor() as cursor:
                                cursor.execute(TOTAL_POLL_VOTES_QUERY, [])

                                poll_columns = [col[0] for col in cursor.description]
                                poll_results['results'] = cursor.fetchall()

                            # Then write the results to a CSV file
                            # writer = csv.writer(response)

                            # writer.writerow(["Election Results"])

                            with open('Election Results.csv', 'w', newline='', encoding='utf-8') as csvFile:
                                electionWriter = csv.writer(csvFile,)

                                electionWriter.writerow(columns)

                                for row in vote_results['results']:
                                    electionWriter.writerow(list(row))

                            # writer.writerow("")

                            # writer.writerow(["Poll Results"])

                            with open('Poll Results.csv', 'w', newline='', encoding='utf-8') as csvFile:
                                pollWriter = csv.writer(csvFile,)

                                pollWriter.writerow(poll_columns)

                                for row in poll_results['results']:
                                    pollWriter.writerow(list(row))

                            electionPollZip = ZipFile('Election and Poll Results.zip', 'w')
                            electionPollZip.write('Election Results.csv', compress_type=ZIP_DEFLATED)
                            electionPollZip.write('Poll Results.csv', compress_type=ZIP_DEFLATED)
                            electionPollZip.close()

                            # Create a response object, and classify it as a ZIP response
                            response = HttpResponse(open('Election and Poll Results.zip', 'rb').read(), content_type='application/x-zip-compressed')
                            response['Content-Disposition'] = 'attachment; filename="Election and Poll Results.zip"'

                            e = Election.objects.latest('timestamp')
                            e.state = ElectionState.ARCHIVED.value
                            e.save()

                            # Clear all users who are voters
                            # This also clears the following tables: voters, candidates, takes, vote set, poll set
                            User.objects.filter(groups__name='voter').delete()

                            # Clear all issues
                            Issue.objects.all().delete()

                            # Clear all votes
                            Vote.objects.all().delete()

                            # Clear all polls
                            Poll.objects.all().delete()

                            # Clear all batch positions
                            Position.objects.filter(base_position__type=BasePosition.BATCH).delete()

                            # Clear all batch units
                            Unit.objects.filter(college__isnull=False, batch__isnull=False)

                            # Show a Save As box so the user may download it
                            return response
            
            elif form_type == "pause-elections":
                # If the elections have already ended, it can't be ended again!
                if election_state == ElectionState.ONGOING.value:
                    # Only continue if the re-authentication password indeed matches the password of the current
                    # COMELEC officer
                    reauth_password = request.POST.get('reauth', False)

                    if reauth_password is False \
                            or authenticate(username=request.user.username, password=reauth_password) is None:
                        messages.error(request,
                                       'The elections weren\'t paused because the password was incorrect. Try again.')
                    else:
                        e = Election.objects.latest('timestamp')
                        e.state = ElectionState.PAUSED.value
                        e.save()

                        messages.success(request, 'The elections have now been paused.')
                else:
                    messages.error(request, 'The elections are not currently ongoing.')

                context = self.get_context()

                return render(request, self.template_name, context)

            elif form_type == "resume-elections":
                # If the elections have already ended, it can't be ended again!
                if election_state == ElectionState.PAUSED.value:
                    # Only continue if the re-authentication password indeed matches the password of the current
                    # COMELEC officer
                    reauth_password = request.POST.get('reauth', False)

                    if reauth_password is False \
                            or authenticate(username=request.user.username, password=reauth_password) is None:
                        messages.error(request,
                                       'The elections weren\'t resumed because the password was incorrect. Try again.')
                    else:
                        e = Election.objects.latest('timestamp')
                        e.state = ElectionState.ONGOING.value
                        e.save()

                        messages.success(request, 'The elections have now been resumed.')
                else:
                    messages.error(request, 'The elections are not currently paused.')

                context = self.get_context()

                return render(request, self.template_name, context)

            elif form_type == "unblock-results":
                # If the elections have already ended, it can't be ended again!
                if election_state == ElectionState.BLOCKED.value:
                    # Only continue if the re-authentication password indeed matches the password of the current
                    # COMELEC officer
                    reauth_password = request.POST.get('reauth-unblock', False)

                    if reauth_password is False \
                            or authenticate(username=request.user.username, password=reauth_password) is None:
                        messages.error(request,
                                       'The elections results weren\'t unblocked because the password was incorrect. Try again.')
                    else:
                        e = Election.objects.latest('timestamp')
                        e.state = ElectionState.FINISHED.value
                        e.save()

                        messages.success(request, 'The elections results have been unblocked.')
                else:
                    messages.error(request, 'The elections are not yet over.')

                context = self.get_context()

                return render(request, self.template_name, context)
            
            else:
                # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                # message
                messages.error(request, 'Invalid request.')

                context = self.display_objects(1)

                return render(request, self.template_name, context)

        return render(request, self.template_name)


class VotersView(SysadminView):
    template_name = 'sysadmin/admin-voter.html'

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

        if form_type is False:
            # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)
        
        # The submitted form is for adding a voter/s
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
                # If the form type is unknown, it's an invalid request, so stay on the page and then show an
                # error message
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
                                        'The uploaded list contained invalid voter data. No voters were added (Error'
                                        ' at row ' + repr(current_row) + ')')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                    # message
                    messages.error(request, 'Invalid request.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
            
        # Only allow editing and deleting while there are no elections ongoing and there are no votes in the database
        if (not ResultsView.get_election_state() or ResultsView.get_election_state() == ElectionState.ARCHIVED.value) and ResultsView.is_votes_empty():
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
                    except Voter.DoesNotExist:
                        # If the user does not exist
                        messages.error(request,
                                        'One of the selected users has not existed in the first place. '
                                        'No voters were deleted.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an
                    # error message
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


class CandidatesView(SysadminView):
    template_name = 'sysadmin/admin-candidate.html'

    # A convenience function for adding a candidate
    @staticmethod
    def add_candidate(voter_id, position_unit, position_name, party):
        # Retrieve the voter
        voter = Voter.objects.get(user__username=voter_id)

        # Retrieve the position
        position = Position.objects.get(unit__name=position_unit, base_position__name=position_name)

        # Retrieve the party
        if party == 'Independent':
            party = None
        else:
            party = Party.objects.get(name=party)

        # A candidate may only run for a college or batch position in his own college and batch
        if position.base_position.type == BasePosition.EXECUTIVE \
                or position.base_position.type == BasePosition.COLLEGE \
                and position.unit.college.name == voter.college.name \
                or position.base_position.type == BasePosition.BATCH \
                and (position.unit.batch == voter.user.username[:3]
                     and position.unit.college.name == voter.college.name):
            # Create the candidate
            Candidate.objects.create(voter=voter, position=position, party=party)
        else:
            raise Candidate.DoesNotExist

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
                Q(position__base_position__name__icontains=query) |
                Q(position__unit__name=query) |
                Q(party__name__icontains=query)
            ) \
                .order_by('voter__user__username')

        voters = Voter.objects.all().order_by('user__username')
        positions = Position.objects.all().order_by('unit__name', 'base_position__name')
        parties = Party.objects.all().order_by('name')
        issues = Issue.objects.all().order_by('name')

        paginator = Paginator(candidates, self.objects_per_page)
        paginated_candidates = paginator.get_page(page)

        context = {
            'candidates': paginated_candidates,
            'voters': voters,
            'positions': positions,
            'parties': parties,
            'issues': issues,
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

        # Only allow editing while there are no elections ongoing and there are no votes in the database
        if (not ResultsView.get_election_state() or ResultsView.get_election_state() == ElectionState.ARCHIVED.value) and ResultsView.is_votes_empty():
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
                                           'A candidate with the same name or position and party has already been added'
                                           '.')
                        except Voter.DoesNotExist:
                            messages.error(request,
                                           'That student does not exist or has not yet been registered in here.')
                        except Position.DoesNotExist:
                            messages.error(request, 'That position does not exist.')
                        except Party.DoesNotExist:
                            messages.error(request, 'That party does not exist.')
                        except Candidate.DoesNotExist:
                            messages.error(request,
                                           'A candidate may only run for a college or batch position in his own college'
                                           ' and batch.')

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
                                                 "All {0} candidate(s) successfully deleted.".format(
                                                     candidates_deleted))
                        except Candidate.DoesNotExist:
                            # If the user does not exist
                            messages.error(request,
                                           'One of the selected candidates has not existed in the first place. '
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
                        if action == 'Save Changes':
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
        else:
            messages.error(request,
                           'You cannot do that now because there are still votes being tracked. There may be '
                           'elections still ongoing, or you haven\'t archived the votes yet.')

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

        if form_type is False:
            # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
            # message
            messages.error(request, 'Invalid request.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)
        
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
                
        # Only allow editing while there are no elections ongoing and there are no votes in the database
        if (not ResultsView.get_election_state() or ResultsView.get_election_state() == ElectionState.ARCHIVED.value) and ResultsView.is_votes_empty():
            if form_type == 'delete-officer':
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
                                        'One of the selected users has not existed in the first place. '
                                        'No officers were deleted.')

                    context = self.display_objects(1)

                    return render(request, self.template_name, context)
                else:
                    # If the form type is unknown, it's an invalid request, so stay on the page and then show an
                    # error message
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
            messages.error(request,
                           'You cannot do that now because there are still votes being tracked. There may be '
                           'elections still ongoing, or you haven\'t archived the votes yet.')

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

        paginator = Paginator(units, self.objects_per_page)
        paginated_units = paginator.get_page(page)

        unit_form = UnitForm()

        context = {
            'units': paginated_units,
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

        # Only allow editing while there are no elections ongoing and there are no votes in the database
        if (not ResultsView.get_election_state() or ResultsView.get_election_state() == ElectionState.ARCHIVED.value) and ResultsView.is_votes_empty():
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
                                           'One of the selected units has not existed in the first place. '
                                           'No units were deleted.')

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
            messages.error(request,
                           'You cannot do that now because there are still votes being tracked. There may be '
                           'elections still ongoing, or you haven\'t archived the votes yet.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)


class PositionView(SysadminView):
    template_name = 'sysadmin/admin-position.html'

    # A convenience function for deleting a position
    @staticmethod
    def delete_position(position_id):
        # Retrieve the position
        position = Position.objects.get(id=position_id)

        # Get rid of that position
        position.delete()

    def display_objects(self, page, query=False):
        # Show everything if the query is empty
        if query is False:
            positions = Position.objects.all().order_by('base_position__name', 'unit__name')
        else:
            positions = Position.objects.filter(
                Q(base_position__name__icontains=query) |
                Q(unit__name__icontains=query)
            ) \
                .order_by('base_position__name', 'unit__name')

        paginator = Paginator(positions, self.objects_per_page)
        paginated_positions = paginator.get_page(page)

        position_form = PositionForm()

        context = {
            'positions': paginated_positions,
            'position_form': position_form
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)
        query = request.GET.get('query', False)

        context = self.display_objects(page if page is not False else 1, query)

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        position_form = PositionForm(request.POST)

        # Only allow editing while there are no elections ongoing and there are no votes in the database
        if (not ResultsView.get_election_state() or ResultsView.get_election_state() == ElectionState.ARCHIVED.value) and ResultsView.is_votes_empty():
            if form_type is not False:
                if form_type == 'add-position':
                    # The submitted form is for adding a position
                    if position_form.is_valid():
                        with transaction.atomic():
                            # Save the form to the database if it is valid
                            position_form.save()

                            messages.success(request, 'Position successfully added.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)
                    else:
                        # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                        # message
                        messages.error(request, 'Could not add this position.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)
                elif form_type == 'delete-position':
                    # The submitted form is for deleting positions
                    positions_list = request.POST.getlist('positions')

                    if positions_list is not False and len(positions_list) > 0:
                        try:
                            positions_deleted = 0

                            # Try to delete each position in the list
                            with transaction.atomic():
                                for position in positions_list:
                                    self.delete_position(position)

                                    positions_deleted += 1

                                messages.success(request,
                                                 "All {0} position(s) successfully deleted.".format(positions_deleted))
                        except Position.DoesNotExist:
                            # If the position does not exist
                            messages.error(request,
                                           'One of the selected positions has not existed in the first place. '
                                           'No positions were deleted.')

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
            messages.error(request,
                           'You cannot do that now because there are still votes being tracked. There may be '
                           'elections still ongoing, or you haven\'t archived the votes yet.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)


class IssueView(SysadminView):
    template_name = 'sysadmin/admin-issue.html'

    # A convenience function for deleting an issue
    @staticmethod
    def delete_issue(issue_id):
        # Retrieve the issue
        issue = Issue.objects.get(id=issue_id)

        # Get rid of that issue
        issue.delete()

    def display_objects(self, page, query=False):
        # Show everything if the query is empty
        if query is False:
            issues = Issue.objects.all().order_by('name')
        else:
            issues = Issue.objects.filter(name__icontains=query).order_by('name')

        paginator = Paginator(issues, self.objects_per_page)
        paginated_issues = paginator.get_page(page)

        issue_form = IssueForm()

        context = {
            'issues': paginated_issues,
            'issue_form': issue_form
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

        # Only allow editing while there are no elections ongoing and there are no votes in the database
        if (not ResultsView.get_election_state() or ResultsView.get_election_state() == ElectionState.ARCHIVED.value) and ResultsView.is_votes_empty():
            if form_type is not False:
                if form_type == 'add-issue':
                    # The submitted form is for adding an issue
                    if issue_form.is_valid():
                        with transaction.atomic():
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
                elif form_type == 'delete-issues':
                    # The submitted form is for deleting issues
                    issues_list = request.POST.getlist('issues')

                    if issues_list is not False and len(issues_list) > 0:
                        try:
                            issues_deleted = 0

                            # Try to delete each issue in the list
                            with transaction.atomic():
                                for issue in issues_list:
                                    self.delete_issue(issue)

                                    issues_deleted += 1

                                messages.success(request,
                                                 "All {0} issue(s) successfully deleted.".format(issues_deleted))
                        except Issue.DoesNotExist:
                            # If the position does not exist
                            messages.error(request,
                                           'One of the selected issues has not existed in the first place. '
                                           'No issues were deleted.')

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
            messages.error(request,
                           'You cannot do that now because there are still votes being tracked. There may be '
                           'elections still ongoing, or you haven\'t archived the votes yet.')

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

class PollView(SysadminView):
    template_name = 'sysadmin/admin-poll.html'

    # A convenience function for deleting an poll
    @staticmethod
    def delete_poll(poll_id):
        # Retrieve the poll
        poll = Poll.objects.get(id=poll_id)

        # Get rid of that issupolle
        poll.delete()

    def display_objects(self, page, query=False):
        # Show everything if the query is empty
        if query is False:
            polls = Poll.objects.all().order_by('name')
        else:
            polls = Poll.objects.filter(name__icontains=query).order_by('name')

        paginator = Paginator(polls, self.objects_per_page)
        paginated_polls = paginator.get_page(page)

        poll_form = PollForm()

        context = {
            'polls': paginated_polls,
            'poll_form': poll_form
        }

        return context

    def get(self, request):
        page = request.GET.get('page', False)
        query = request.GET.get('query', False)

        context = self.display_objects(page if page is not False else 1, query)

        return render(request, self.template_name, context)

    def post(self, request):
        form_type = request.POST.get('form-type', False)

        poll_form = PollForm(request.POST)

        # Only allow editing while there are no elections ongoing and there are no votes in the database
        if (not ResultsView.get_election_state() or ResultsView.get_election_state() == ElectionState.ARCHIVED.value) and ResultsView.is_votes_empty():
            if form_type is not False:
                if form_type == 'add-poll':
                    # The submitted form is for adding an poll
                    if poll_form.is_valid():
                        with transaction.atomic():
                            # Save the form to the database if it is valid
                            poll_form.save()

                            messages.success(request, 'Poll successfully added.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)
                    else:
                        # If the form type is unknown, it's an invalid request, so stay on the page and then show an error
                        # message
                        messages.error(request, 'Could not add this poll.')

                        context = self.display_objects(1)

                        return render(request, self.template_name, context)
                elif form_type == 'delete-polls':
                    # The submitted form is for deleting polls
                    polls_list = request.POST.getlist('polls')

                    if polls_list is not False and len(polls_list) > 0:
                        try:
                            polls_deleted = 0

                            # Try to delete each poll in the list
                            with transaction.atomic():
                                for poll in polls_list:
                                    self.delete_poll(poll)

                                    polls_deleted += 1

                                messages.success(request,
                                                 "All {0} poll(s) successfully deleted.".format(polls_deleted))
                        except Poll.DoesNotExist:
                            # If the position does not exist
                            messages.error(request,
                                           'One of the selected polls has not existed in the first place. '
                                           'No polls were deleted.')

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
            messages.error(request,
                           'You cannot do that now because there are still votes being tracked. There may be '
                           'elections still ongoing, or you haven\'t archived the votes yet.')

            context = self.display_objects(1)

            return render(request, self.template_name, context)