from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'date_start_contract', 'date_end_contract', 'still_active')
        widgets = {
            'date_start_contract': forms.DateInput(attrs={'type': 'date'}),
            'date_end_contract': forms.DateInput(attrs={'type': 'date'}),
        }


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'date_start_contract', 'date_end_contract', 'still_active')
        widgets = {
            'date_start_contract': forms.DateInput(attrs={'type': 'date'}),
            'date_end_contract': forms.DateInput(attrs={'type': 'date'}),
        }
    password = None  # Exclure le champ mot de passe du formulaire