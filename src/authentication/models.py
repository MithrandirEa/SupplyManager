from django.contrib.auth.models import AbstractUser, Group
from django.db import models

# Create your models here.


class User(AbstractUser):
    # 3 types d'utilisateurs : admin ,responsable  et équipe.

    ADMIN = 'ADMIN'
    DIRECTOR = 'DIRECTOR'
    CREW = 'CREW'

    ROLE_CHOICES = (
        (ADMIN, 'Admin'),
        (DIRECTOR, 'Responsable'),
        (CREW, 'Équipe'),
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default=CREW,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# Ajout automatique aux groupes selon le rôle (Admin ou Responsable ou Crew)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.role == self.ADMIN:
            group = Group.objects.get(name='Admin')
            group.user_set.add(self)
        elif self.role == self.DIRECTOR:
            group = Group.objects.get(name='Responsable')
            group.user_set.add(self)
        else:
            group = Group.objects.get(name='Équipe')
            group.user_set.add(self)
