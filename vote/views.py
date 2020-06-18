# Create your views here.
import json
import traceback

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View

# Sends an email receipt containing the voted candidates to the voter
from vote.models import Issue, Candidate, Voter, Take, Vote, VoteSet, BasePosition, Position, Poll, PollSet, PollAnswerType


# Test function for this view
def vote_test_func(user):
    if user.is_authenticated:
        try:
            return Group.objects.get(name='voter') in user.groups.all()
        except Group.DoesNotExist:
            return False
    else:
        return False


class VoteView(UserPassesTestMixin, View):
    template_name = 'vote/voting.html'

    # Check for duplicate votes and positions in a voteset
    @staticmethod
    def contains_duplicates(position_votes):
        positions = []
        votes = []

        for position_vote in position_votes:
            positions.append(position_vote[0])
            votes.append(position_vote[1])

        votes = list(filter(lambda vote: vote is not False, votes))

        return len(positions) == len(list(set(positions))) and len(votes) == len(list(set(votes)))

    # Generate a serial number
    @staticmethod
    def generate_serial_number(id):
        # The serial number is simply the vote id padded so it fits a ten-digit space
        LEN_SERIAL_NUMBER = 10

        return str(id).rjust(LEN_SERIAL_NUMBER, '0')

    # Sends an email receipt to the voter
    @staticmethod
    def send_email_receipt(user, voted, serial_number):
        from_email = settings.EMAIL_HOST_USER
        to_email = [user.email]
        subject = '[COMELEC] Voter\'s receipt for ' + user.first_name + ' ' + user.last_name

        candidates_voted = ''

        # Generate message for the candidates voted
        for position_candidate in voted.values():
            candidates_voted += position_candidate[0].__str__() + ": " + (
                (position_candidate[1].voter.user.first_name + " " + position_candidate[1].voter.user.last_name) if
                position_candidate[1] is not False else '(abstained)') + '\n'

        # Append the serial number
        candidates_voted += '\nYour serial number is ' + serial_number + '.\n'

        message \
            = '''Good day, {0},\n\nThank you for voting! You have voted for the following candidates:\n\n{1}''' \
            .format(
            user.first_name,
            candidates_voted)

        # Send an email, but fail silently (accept exception, bust just show message)
        try:
            send_mail(subject=subject, from_email=from_email, recipient_list=to_email, message=message,
                      fail_silently=False)
        except Exception:
            # Show the exception in the server, but mask it from the user
            print("Email send failure.")

            traceback.print_exc()

    # Check whether the user accessing this page is a voter or not
    def test_func(self):
        return vote_test_func(self.request.user)

    def get(self, request):
        # Get the current voter from the current user
        voter = Voter.objects.get(user__username=request.user.username)

        # Get the college of the current voter
        college = voter.college.name

        # Get the batch of the current voter
        batch = voter.user.username[:3]

        # Get all candidates
        candidates = {}

        # And remember all "voteable" positions
        positions = []
        positions_json = []

        # Partition the candidates into their position's types
        base_positions = BasePosition.objects.values('type').distinct().order_by('-type')

        for base_position in base_positions:
            # Take note of the position type
            position_type = base_position['type']

            # Create a partition for that position type
            candidates[position_type] = {}

            # Then try to fill that partition with candidates running for that position type
            candidates_type = Candidate.objects.filter(position__base_position__type=position_type).order_by(
                'party__name').order_by('position__priority')

            if candidates_type.count() != 0:
                for candidate in candidates_type:
                    # If the position is of type college, the position's college must match the voter's college
                    # If the position is of type batch, that position's batch must match the voter's batch and college
                    if position_type == BasePosition.COLLEGE and candidate.position.unit.college.name != college \
                            or position_type == BasePosition.BATCH \
                            and (candidate.position.unit.batch != batch
                                 or candidate.position.unit.college.name != college):
                        continue

                    # Only add the candidate if all the conditions above have been satisfied
                    position = candidate.position

                    if position not in candidates[position_type]:
                        candidates[position_type][position] = []

                    candidates[position_type][position].append(candidate)

                    # Remember the positions, if they haven't already been remembered
                    if position not in positions:
                        positions.append(position)
                        positions_json.append(str(position.identifier))

                # If there turned out to be no candidates running for this position type relevant to the voter, just
                # forget about that position type and move on
                if not candidates[position_type]:
                    candidates.pop(position_type)
            else:
                # If there are no candidates running for this position type, just forget about that position type and
                # move on
                candidates.pop(position_type)

        # print(candidates["Executive"])

        # Dump the positions into JSON
        positions_json = json.dumps(list(positions_json))

        # Get all issues
        issues = Issue.objects.all().order_by('name')

        # Get polls
        polls = Poll.objects.all().order_by('name')
        polls_json = []
        for poll in polls:
            polls_json.append(str(poll.identifier))
        polls_json = json.dumps(list(polls_json))

        context = {
            'candidates': candidates,
            'positions': positions,
            'positions_json': positions_json,
            'issues': issues,
            'polls': polls,
            'polls_json': polls_json
        }

        # Get this page
        return render(request, self.template_name, context)

    def post(self, request):
        voter = request.user.voter

        # Check if the voter has already voted
        # If not yet...
        if not voter.voting_status:
            # Take note of the voter's votes
            votes = []
            poll_votes = []

            # Collect all "voteable" positions
            positions = request.POST.getlist('position')

            # Collect all polls
            polls = request.POST.getlist('poll')

            if positions is not False and len(positions) > 0:
                for position in positions:
                    # For each position, get the voter's pick through its identifier
                    # It should return False when the voter abstained for that position (picked no one)
                    votes.append((position, request.POST.get(position, False),))

            if polls is not False and len(polls) > 0:
                for poll in polls:
                    poll_votes.append((poll, request.POST.get(poll)[request.POST.get(poll).rfind('-')+1:],))
            
            print(poll_votes)

            # Proceed only when there are no duplicate votes and positions
            if self.contains_duplicates(votes) and self.contains_duplicates(poll_votes):
                # If there are no duplicates, convert the list of tuples into a dict
                votes_dict = {}

                for vote in votes:
                    votes_dict[vote[0]] = vote[1]

                votes = votes_dict

                poll_votes_dict = {}

                for poll in poll_votes:
                    poll_votes_dict[poll[0]] = poll[1]

                polls = poll_votes_dict

                try:
                    # Change the identifiers to the actual candidates they represent
                    for position, candidate in votes.items():
                        votes[position] = (Position.objects.get(identifier=position),
                                           Candidate.objects.get(
                                               identifier=candidate) if candidate is not False else False,)

                    for identifier, answer in polls.items():
                        polls[identifier] = (Poll.objects.get(identifier=identifier),
                                           answer,)

                    with transaction.atomic():
                        # Create a vote object to represent a single vote of a user
                        vote = Vote(voter_id_number=voter.user.username, voter_college=voter.college.name)
                        vote.save()

                        # Generate its serial number
                        serial_number = self.generate_serial_number(vote.id)

                        vote.serial_number = serial_number
                        vote.save()

                        # Create a vote set array representing the individual votes to be saved in the database
                        actual_votes = [
                            VoteSet(vote=vote,
                                    candidate=(position_candidate[1] if position_candidate[1] is not False else None),
                                    position=position_candidate[0]) for position_candidate in votes.values()
                        ]

                        actual_poll_votes = [
                            PollSet(vote=vote,
                                    poll=(poll[0]),
                                    answer=(poll[1])) for poll in polls.values()
                        ]

                        # Save all votes into the database
                        for actual_vote in actual_votes:
                            actual_vote.save()

                        for actual_poll_vote in actual_poll_votes:
                            actual_poll_vote.save()

                        # Send email receipt
                        #self.send_email_receipt(request.user, votes, serial_number)

                        # Mark the voter as already voted
                        voter.voting_status = True
                        voter.save()

                    # Log the user out
                    logout(request)

                    return redirect('logout:logout_voter')
                except PollAnswerType.ValueError:
                    # One of the votes for the polls is not a valid answer
                    messages.error(request, 'Some of your answers to the polls do not exist')

                    return self.get(request)
                except Candidate.DoesNotExist:
                    # One of the votes do not represent a candidate
                    messages.error(request, 'One of your voted candidates do not exist.')

                    return self.get(request)
                except IntegrityError:
                    # A vote has already been created to the voter's name, meaning he has already voted
                    messages.error(request, 'You may have already voted before.')

                    # Log the user out
                    logout(request)

                    voter.voting_status = True
                    voter.save()

                    return redirect('logout:logout_fail')
                # except SMTPException:
                #     # Could not send an email receipt
                #     messages.error(request, 'Could not send an email receipt to your email address.')
                #
                #     return self.get(request)
            else:
                # If there are duplicate votes
                messages.error(request, 'There are duplicate votes in your submission.')

                return self.get(request)
        else:
            # But if the voter already did...
            messages.error(request, 'You have already voted. You may only vote once.')

            # Log the user out
            logout(request)

            return redirect('logout:logout_fail')


@user_passes_test(vote_test_func)
def json_take(request, candidate_identifier, issue):
    # Get the take
    try:
        # Then use that identifier to retrieve the candidate's take
        take = Take.objects.get(candidate__identifier=candidate_identifier, issue__name=issue)
    except Take.DoesNotExist:
        return JsonResponse({'response': "(no takes on this issue given)"})
    except (Candidate.MultipleObjectsReturned, Candidate.DoesNotExist):
        return JsonResponse({'response': '(that candidate does not exist)'})

    # Then return its response
    return JsonResponse({'response': take.response})
