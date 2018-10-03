# Create your models here.
import uuid

from django.contrib.auth.models import User
from django.db import models


class College(models.Model):
    name = models.CharField(max_length=16, unique=True)

    def __str__(self):
        return self.name


class ElectionStatus(models.Model):
    batch = models.CharField(max_length=4)
    college = models.ForeignKey(College, on_delete=models.CASCADE)

    def __str__(self):
        return self.college.name + "," + self.batch


class Unit(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True)
    batch = models.CharField(max_length=4, null=True, blank=True)
    name = models.CharField(max_length=16, unique=True)

    def __str__(self):
        college_batch = (self.college.name if self.college is not None else "") + (
            (", " + self.batch) if self.batch is not None else "")

        return self.name + ((" (" + college_batch + ")") if college_batch != "" else "")


class BasePosition(models.Model):
    EXECUTIVE = 'Executive'
    BATCH = 'Batch'
    COLLEGE = 'College'

    POSITION_TYPES = (
        (EXECUTIVE, 'Executive'),
        (BATCH, 'Batch'),
        (COLLEGE, 'College'),
    )

    name = models.CharField(max_length=64)
    type = models.CharField(max_length=16, choices=POSITION_TYPES)

    def __str__(self):
        return self.name + ' (' + self.type + ')'


class Position(models.Model):
    base_position = models.ForeignKey(BasePosition, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    identifier = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        unique_together = ('base_position', 'unit')

    def __str__(self):
        return ((self.unit.name + " ")
                if self.base_position.type != BasePosition.EXECUTIVE else "") + self.base_position.name


class Voter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    voting_status = models.BooleanField(default=True)
    eligibility_status = models.BooleanField(default=True)

    def __str__(self):
        return "(" + self.user.username + ") " + self.user.first_name + " " + self.user.last_name


class Party(models.Model):
    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    voter = models.OneToOneField(Voter, on_delete=models.CASCADE, unique=True)
    identifier = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, default=None, null=True, blank=True)

    class Meta:
        unique_together = ('position', 'party')

    def __str__(self):
        return self.voter.user.first_name + " " + self.voter.user.last_name \
               + " (" + (
                   self.party.name if self.party is not None else "Independent") + ") - " + self.position.__str__()


class Issue(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Take(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    response = models.TextField()

    def __str__(self):
        return self.response + \
               " (" + self.candidate.voter.user.first_name + " " + self.candidate.voter.user.last_name + ")"


class Vote(models.Model):
    voter_id_number = models.CharField(max_length=8, unique=True)
    voter_college = models.CharField(max_length=3)
    serial_number = models.CharField(max_length=6, default=voter_id_number, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "(" + self.serial_number + ") " + self.voter_id_number + " voted on " + repr(self.timestamp)


class VoteSet(models.Model):
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.vote.voter_id_number + " voted for " \
               + self.candidate.voter.user.first_name + " " + self.candidate.voter.user.last_name
