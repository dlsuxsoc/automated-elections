# Create your models here.

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


class Position(models.Model):
    name = models.CharField(max_length=64)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + " (" + self.unit.name + ")"


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
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE, default=None, null=True, blank=True)

    class Meta:
        unique_together = ('position', 'party')

    def __str__(self):
        return self.voter.user.first_name + " " + self.voter.user.last_name \
               + " (" + self.position.name + ", " + (self.party.name if self.party is not None else "Independent") + ")"


class Issue(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Take(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    response = models.TextField(default='No take.')

    def __str__(self):
        return self.response + \
               " (" + self.candidate.voter.user.first_name + " " + self.candidate.voter.user.last_name + ")"


class Vote(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voter_id_number = models.CharField(max_length=8, unique=True)
    timestamp = models.DateTimeField()

    def __str__(self):
        return "Vote for " + self.candidate.voter.user.first_name + " " + self.candidate.voter.user.last_name
