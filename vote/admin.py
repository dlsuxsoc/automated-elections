# Register your models here.
from django.contrib import admin

from vote.models import College, Unit, Position, Voter, Candidate, Issue, Take, Vote, Party

admin.site.register(College)
admin.site.register(Unit)
admin.site.register(Position)
admin.site.register(Voter)
admin.site.register(Party)
admin.site.register(Candidate)
admin.site.register(Issue)
admin.site.register(Take)
admin.site.register(Vote)
