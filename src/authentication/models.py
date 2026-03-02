from django.contrib.auth.models import AbstractUser, Group, UserManager as BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.conf import settings
import re


class UsernameWithSpacesValidator(UnicodeUsernameValidator):
    """Validateur personnalisé autorisant les espaces dans username"""
    regex = re.compile(r'^[\w\s.@+-]+$')
    message = (
        'Entrez un nom d\'utilisateur valide. Ce champ peut contenir '
        'des lettres, chiffres, espaces et les caractères @/./+/-/_'
    )


class UserManager(BaseUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Force le rôle ADMIN pour les superusers
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)


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

    objects = UserManager()

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
    date_start_contract = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date début contrat"
    )
    date_end_contract = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date fin contrat"
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        indexes = [
            models.Index(fields=['role'], name='user_role_idx'),
            models.Index(fields=['still_active'], name='user_active_idx'),
            models.Index(fields=['date_end_contract'], name='user_end_contract_idx'),
            models.Index(
                fields=['role', 'still_active'],
                name='user_role_active_idx'
            ),
            models.Index(
                fields=['role', 'date_end_contract'],
                name='user_role_contract_idx'
            ),
        ]

    def save(self, *args, **kwargs):
        # Récupérer created_by depuis kwargs si fourni
        created_by_user = kwargs.pop('created_by_user', None)
        if created_by_user and not self.pk and not self.created_by:
            self.created_by = created_by_user
        
        # Synchroniser is_active avec still_active
        self.is_active = self.still_active
        
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
            # Director peut créer Director ou Crew
            return role in [self.DIRECTOR, self.CREW]
        return False

    def __str__(self):
        return f'{self.username} - {self.get_role_display()}'
