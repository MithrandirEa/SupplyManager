from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin
from django.contrib.auth.models import Group as DjangoGroup
from .models import User

# Register your models here.

# Désenregistrer le Group par défaut pour le réenregistrer
admin.site.unregister(DjangoGroup)
admin.site.register(DjangoGroup, GroupAdmin)

# Configuration de l'admin pour le modèle User personnalisé
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Rôle', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Rôle', {'fields': ('role',)}),
    )

admin.site.register(User, UserAdmin)
