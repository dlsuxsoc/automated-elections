from django import forms

from vote.models import Issue


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue

        widgets = {
            'name': forms.TextInput(attrs={'class': 'info-input', 'placeholder': 'Issue name'})
        }

        fields = '__all__'
