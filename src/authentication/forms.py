from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter les classes Bootstrap aux champs
        for field_name, field in self.fields.items():
            if field_name == 'still_active':
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

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

    def save(self, commit=True):
        from datetime import date

        user = super().save(commit=False)

        # Logique de réactivation automatique si le contrat est prolongé
        if user.role == User.CREW and user.date_end_contract:
            # Si la date de fin de contrat est dans le futur,
            # réactiver automatiquement le compte
            if user.date_end_contract >= date.today():
                user.still_active = True

        if commit:
            user.save()

        return user

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
