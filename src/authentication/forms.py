from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        # Si l'utilisateur connecté n'est pas Admin,
        # retirer l'option Admin des choix
        if current_user and current_user.role != 'ADMIN':
            self.fields['role'].choices = [
                (User.DIRECTOR, 'Responsable'),
                (User.CREW, 'Équipe'),
            ]

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        date_start_contract = cleaned_data.get('date_start_contract')
        date_end_contract = cleaned_data.get('date_end_contract')

        # Si le rôle est Équipe, les dates sont obligatoires
        if role == User.CREW:
            if not date_start_contract:
                self.add_error(
                    'date_start_contract',
                    'La date de début de contrat est obligatoire pour '
                    'les membres de l\'\u00e9quipe.'
                )
            if not date_end_contract:
                self.add_error(
                    'date_end_contract',
                    'La date de fin de contrat est obligatoire pour '
                    'les membres de l\'\u00e9quipe.'
                )

        return cleaned_data

    class Meta:
        model = User
        fields = (
            'username', 'email', 'role',
            'date_start_contract', 'date_end_contract', 'still_active'
        )
        labels = {
            'username': 'Nom & Prénom',
            'email': 'Email',
            'role': 'Rôle',
            'date_start_contract': 'Date de début de contrat',
            'date_end_contract': 'Date de fin de contrat',
            'still_active': 'Compte actif',
        }
        widgets = {
            'date_start_contract': forms.DateInput(attrs={'type': 'date'}),
            'date_end_contract': forms.DateInput(attrs={'type': 'date'}),
        }


class CustomUserChangeForm(UserChangeForm):
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        date_start_contract = cleaned_data.get('date_start_contract')
        date_end_contract = cleaned_data.get('date_end_contract')

        # Si le rôle est Équipe, les dates sont obligatoires
        if role == User.CREW:
            if not date_start_contract:
                self.add_error(
                    'date_start_contract',
                    'La date de début de contrat est obligatoire pour '
                    'les membres de l\'\u00e9quipe.'
                )
            if not date_end_contract:
                self.add_error(
                    'date_end_contract',
                    'La date de fin de contrat est obligatoire pour '
                    'les membres de l\'\u00e9quipe.'
                )

        return cleaned_data

    class Meta:
        model = User
        fields = (
            'username', 'email', 'role',
            'date_start_contract', 'date_end_contract', 'still_active'
        )
        labels = {
            'username': 'Nom & Prénom',
            'email': 'Email',
            'role': 'Rôle',
            'date_start_contract': 'Date de début de contrat',
            'date_end_contract': 'Date de fin de contrat',
            'still_active': 'Compte actif',
        }
        widgets = {
            'date_start_contract': forms.DateInput(attrs={'type': 'date'}),
            'date_end_contract': forms.DateInput(attrs={'type': 'date'}),
        }
    password = None  # Exclure le champ mot de passe du formulaire
