from django import forms

from vote.models import Candidate, Issue


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate

        widgets = {
            'voter': forms.Select(attrs={'class': 'info-input'}),
            'position': forms.Select(attrs={'class': 'info-input'}),
            'party': forms.Select(attrs={'class': 'info-input'}),
        }

        fields = '__all__'


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue

        widgets = {
            'name': forms.TextInput(attrs={'class': 'info-input', 'placeholder': 'Issue name'})
        }

        fields = '__all__'
