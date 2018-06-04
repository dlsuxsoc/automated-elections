# Create your views here.
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.views import View


class SysadminView(UserPassesTestMixin, View):
    template_name = ''

    # Redirect the user to a 404 page when the user does is not allowed to view this page
    def get_login_url(self):
        # TODO: Create a 404 page
        return redirect('page_404:page_404')

    # Check whether the user accessing this page is a system administrator or not
    def test_func(self):
        try:
            return Group.objects.get(name='sysadmin') in self.request.user.groups.all()
        except Group.DoesNotExist:
            return False

    def get(self, request):
        pass

    def post(self, request):
        pass


class VotersView(SysadminView):
    template_name = 'sysadmin/admin-voter.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        return render(request, self.template_name)


class CandidatesView(SysadminView):
    template_name = 'sysadmin/admin-candidate.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
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
