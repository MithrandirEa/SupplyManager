from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import User


class Command(BaseCommand):
    help = (
        'Désactive automatiquement tous les comptes dont la date '
        'de fin de contrat est dépassée'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les comptes à désactiver sans les modifier',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()

        # Trouver tous les utilisateurs actifs avec une date de fin
        # de contrat dépassée
        expired_users = User.objects.filter(
            is_active=True,
            date_end_contract__isnull=False,
            date_end_contract__lt=today
        )

        count = expired_users.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Aucun compte expiré trouvé.')
            )
            return

        # Afficher les comptes trouvés
        self.stdout.write(
            self.style.WARNING(
                f'\n{count} compte(s) expiré(s) trouvé(s):'
            )
        )
        for user in expired_users:
            self.stdout.write(
                f'  - {user.username} ({user.get_role_display()}) - '
                f'Contrat terminé le {user.date_end_contract}'
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.NOTICE(
                    '\nMode --dry-run: aucune modification effectuée.'
                )
            )
            return

        # Désactiver les comptes
        expired_users.update(is_active=False, still_active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ {count} compte(s) désactivé(s) avec succès.'
            )
        )
