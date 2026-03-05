import logging
import time

from django.utils import timezone

from authentication.models import User

logger = logging.getLogger(__name__)


class AccountExpirationMiddleware:
    """
    Middleware qui désactive automatiquement les comptes expirés.
    Vérifie les utilisateurs dont la date de fin de contrat
    est dépassée et met leur compte à inactif.

    La vérification est throttlée pour ne s'exécuter qu'une fois
    par minute au maximum.
    """
    _last_check = 0
    CHECK_INTERVAL = 60  # secondes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        now = time.time()
        if now - AccountExpirationMiddleware._last_check > self.CHECK_INTERVAL:
            self.deactivate_expired_accounts()
            AccountExpirationMiddleware._last_check = now

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

        if count > 0:
            logger.info(
                "%d compte(s) expiré(s) désactivé(s)", count
            )

        return count
