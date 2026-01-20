from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.conf import settings
import re


class UsernameWithSpacesValidator(UnicodeUsernameValidator):
    """Validateur personnalisé autorisant les espaces dans le nom d'utilisateur"""
    regex = re.compile(r'^[\w\s.@+-]+$')
    message = 'Entrez un nom d\'utilisateur valide. Ce champ peut contenir des lettres, chiffres, espaces et les caractères @/./+/-/_'


class User(AbstractUser):
    """Modèle utilisateur unique avec gestion des rôles"""
    
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[UsernameWithSpacesValidator()],
        error_messages={
            'unique': "Un utilisateur avec ce nom existe déjà.",
        },
    )
    
    ADMIN = 'ADMIN'
    DIRECTOR = 'DIRECTOR'
    CREW = 'CREW'

    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (DIRECTOR, 'Responsable'),
        (CREW, 'Équipe'),
    ]

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default=CREW)
    
    # Champs communs
    still_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_users'
    )
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='revoked_users'
    )
    
    # Champs spécifiques CREW
    date_start_contract = models.DateField(null=True, blank=True, verbose_name="Date début contrat")
    date_end_contract = models.DateField(null=True, blank=True, verbose_name="Date fin contrat")

    def save(self, *args, **kwargs):
        # Récupérer created_by depuis kwargs si fourni
        created_by_user = kwargs.pop('created_by_user', None)
        if created_by_user and not self.pk and not self.created_by:
            self.created_by = created_by_user
        
        super().save(*args, **kwargs)
        
        # Ajout automatique au groupe selon le rôle
        self.groups.clear()  # Nettoyer les anciens groupes
        if self.role == self.ADMIN:
            group, _ = Group.objects.get_or_create(name='Admin')
        elif self.role == self.DIRECTOR:
            group, _ = Group.objects.get_or_create(name='Responsable')
        else:
            group, _ = Group.objects.get_or_create(name='Équipe')
        group.user_set.add(self)

    def can_create_user(self, role):
        """Vérifie si l'utilisateur peut créer un user avec ce rôle"""
        if self.role == self.ADMIN:
            return True  # Admin peut créer n'importe qui
        elif self.role == self.DIRECTOR:
            return role in [self.DIRECTOR, self.CREW]  # Director peut créer Director ou Crew
        return False

    def __str__(self):
        return f'{self.username} - {self.get_role_display()}'
