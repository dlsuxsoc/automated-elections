from django import forms
from django.contrib.auth.models import User

from vote.models import Issue, Unit, Position


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue

        widgets = {
            'name': forms.TextInput(attrs={'class': 'info-input', 'placeholder': 'Issue name'})
        }

        fields = '__all__'


class OfficerForm(forms.ModelForm):
    class Meta:
        model = User

        widgets = {
            'username': forms.TextInput(
                attrs={'class': 'info-input', 'placeholder': 'Username', 'required': 'required'}),
            'first_name': forms.TextInput(
                attrs={'class': 'info-input', 'placeholder': 'First name', 'required': 'required'}),
            'last_name': forms.TextInput(
                attrs={'class': 'info-input', 'placeholder': 'Last name', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'info-input', 'placeholder': 'Email', 'required': 'required'}),
            'password': forms.PasswordInput(
                attrs={'class': 'info-input', 'placeholder': 'Password', 'required': 'required'})
        }

        fields = ['username', 'first_name', 'last_name', 'email', 'password']


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit

        widgets = {
            'college': forms.Select(
                attrs={'class': 'info-input'}),
            'batch': forms.TextInput(
                attrs={'class': 'info-input', 'placeholder': 'Batch'}),
            'name': forms.TextInput(
                attrs={'class': 'info-input', 'placeholder': 'Unit name', 'required': 'required'}),
        }

        fields = '__all__'


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position

        widgets = {
            'base_position': forms.Select(
                attrs={'class': 'info-input', 'required': 'required'}),
            'unit': forms.Select(
                attrs={'class': 'info-input', 'required': 'required'}),
        }

        fields = '__all__'
