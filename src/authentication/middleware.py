from django.utils import timezone

from authentication.models import User


class AccountExpirationMiddleware:
    """
    Middleware qui désactive automatiquement les comptes expirés.
    Vérifie tous les utilisateurs dont la date de fin de contrat
    est dépassée et met leur compte à inactif.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Désactiver tous les comptes expirés avant chaque requête
        self.deactivate_expired_accounts()

        response = self.get_response(request)
        return response

    @staticmethod
    def deactivate_expired_accounts():
        """
        Désactive tous les comptes dont la date de fin de contrat
        est dépassée.
        """
        today = timezone.now().date()

        # Trouver tous les utilisateurs actifs avec une date de fin
        # de contrat dépassée
        expired_users = User.objects.filter(
            is_active=True,
            date_end_contract__isnull=False,
            date_end_contract__lt=today
        )

        # Désactiver ces comptes
        count = expired_users.update(is_active=False)

        # Option: log le nombre de comptes désactivés
        if count > 0:
            print(
                f"[AccountExpirationMiddleware] "
                f"{count} compte(s) expiré(s) désactivé(s)"
            )

        return count
