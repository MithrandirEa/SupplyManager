"""
Services pour le dashboard - logique métier centralisée
"""
from datetime import date, timedelta

from django.db.models import Prefetch, Q

from authentication.models import User
from supplier.models import Order, OrderItem
from supply.models import Item


class DashboardService:
    """Service pour gérer toutes les données du dashboard"""

    @staticmethod
    def get_missing_items():
        """
        Retourne les items avec une quantité manquante.

        Quantité manquante = total - (disponible + chez fournisseur)
        """
        items = Item.objects.select_related('category').prefetch_related(
            'suppliers'
        ).filter(is_available=True)

        missing_items = []
        for item in items:
            if item.missing_quantity > 0:
                missing_items.append(item)

        return missing_items

    @staticmethod
    def get_excess_items():
        """
        Retourne les items avec une quantité excédentaire.
        """
        items = Item.objects.select_related('category').filter(
            excess_quantity__gt=0,
            is_available=True
        )
        return list(items)

    @staticmethod
    def get_items_at_supplier():
        """
        Retourne les items actuellement chez un fournisseur.

        Items avec outside_quantity > 0
        """
        items = Item.objects.select_related('category').prefetch_related(
            'suppliers'
        ).filter(
            outside_quantity__gt=0,
            is_available=True
        ).order_by('category__name', 'name')
        return list(items)

    @staticmethod
    def get_stock_anomalies():
        """
        Retourne toutes les anomalies de stock.

        Combine les items manquants et excédentaires avec leur type.
        """
        anomalies = []

        # Anomalies de défaut (manquant)
        missing_items = DashboardService.get_missing_items()
        for item in missing_items:
            anomalies.append({
                'type': 'deficit',
                'severity': 'danger',
                'item': item,
                'quantity': item.missing_quantity,
                'message': f"Article manquant : {item.name}"
            })

        # Anomalies d'excès
        excess_items = DashboardService.get_excess_items()
        for item in excess_items:
            anomalies.append({
                'type': 'excess',
                'severity': 'warning',
                'item': item,
                'quantity': item.excess_quantity,
                'message': f"Article excédentaire : {item.name}"
            })

        return anomalies

    @staticmethod
    def get_order_anomalies():
        """
        Retourne les commandes en retard (anomalies de commande).
        """
        orders = Order.objects.select_related(
            'supplier', 'created_by'
        ).prefetch_related(
            Prefetch(
                'order_items',
                queryset=OrderItem.objects.select_related('item')
            )
        ).filter(
            status__in=['pending', 'delayed'],
            expected_return_date__lt=date.today()
        )

        anomalies = []
        for order in orders:
            severity = 'danger' if order.days_delayed > 7 else 'warning'
            message = f"Commande #{order.id} en retard de {order.days_delayed} jour(s)"

            # Si c'est un reliquat, on précise
            if order.notes and "Reliquat" in order.notes:
                message += " (Reliquat)"

            anomalies.append({
                'type': 'order_delay',
                'severity': severity,
                'order': order,
                'days_delayed': order.days_delayed,
                'message': message
            })

        # Ajouter les reliquats en attente même s'ils ne sont pas en retard ?
        # La demande "apparaitre comme une anomalie" pourrait signifier qu'on veut voir ces reliquats spécifiquement.
        # Checkons les commandes "pending" qui sont des reliquats mais PAS en retard
        backorders = Order.objects.filter(
            status='pending',
            notes__icontains='Reliquat',
            expected_return_date__gte=date.today()  # Pas encore en retard
        )

        for bo in backorders:
            anomalies.append({
                'type': 'backorder_pending',
                'severity': 'info',  # Moins critique car pas en retard
                'order': bo,
                'days_delayed': 0,
                'message': f"Reliquat en attente : Commande #{bo.id}"
            })

        return anomalies

    @staticmethod
    def get_contract_anomalies():
        """
        Retourne les utilisateurs Crew dont le contrat expire
        dans les 2 semaines.
        """
        two_weeks_from_now = date.today() + timedelta(weeks=2)

        crew_members = User.objects.filter(
            role=User.CREW,
            still_active=True,
            date_end_contract__isnull=False,
            date_end_contract__lte=two_weeks_from_now,
            date_end_contract__gte=date.today()
        ).order_by('date_end_contract')

        anomalies = []
        for crew in crew_members:
            days_remaining = (
                crew.date_end_contract - date.today()
            ).days
            severity = 'danger' if days_remaining <= 7 else 'warning'

            anomalies.append({
                'type': 'contract_expiry',
                'severity': severity,
                'user': crew,
                'days_remaining': days_remaining,
                'message': (
                    f"Contrat de {crew.username} expire dans "
                    f"{days_remaining} jour(s)"
                )
            })

        return anomalies

    @staticmethod
    def get_outdated_orders():
        """
        Retourne les commandes dont la date de retour attendue
        est dépassée.
        """
        orders = Order.objects.select_related(
            'supplier', 'created_by'
        ).prefetch_related(
            Prefetch(
                'order_items',
                queryset=OrderItem.objects.select_related('item')
            )
        ).filter(
            Q(status='delayed') | Q(
                status='pending',
                expected_return_date__lt=date.today()
            )
        ).order_by('expected_return_date')

        return list(orders)

    @staticmethod
    def get_waited_orders():
        """
        Retourne les commandes en attente dans les délais.

        Commandes dont la date de retour n'est pas encore dépassée.
        """
        orders = Order.objects.select_related(
            'supplier', 'created_by'
        ).prefetch_related(
            Prefetch(
                'order_items',
                queryset=OrderItem.objects.select_related('item')
            )
        ).filter(
            status='pending',
            expected_return_date__gte=date.today()
        ).order_by('expected_return_date')

        return list(orders)

    @classmethod
    def get_all_dashboard_data(cls):
        """
        Retourne toutes les données nécessaires pour le dashboard
        en une seule fois.

        Optimisé pour minimiser les requêtes à la base de données.
        """
        return {
            'missing_items': cls.get_missing_items(),
            'excess_items': cls.get_excess_items(),
            'items_at_supplier': cls.get_items_at_supplier(),
            'stock_alerts': cls.get_stock_anomalies(),
            'order_alerts': cls.get_order_anomalies(),
            'contract_alerts': cls.get_contract_anomalies(),
            'outdated_orders': cls.get_outdated_orders(),
            'waited_orders': cls.get_waited_orders(),
        }

    @classmethod
    def get_alerts_count(cls):
        """
        Retourne le nombre total d'alertes pour afficher
        un badge de notification.
        """
        stock_alerts = len(cls.get_stock_anomalies())
        order_alerts = len(cls.get_order_anomalies())
        contract_alerts = len(cls.get_contract_anomalies())

        return {
            'stock': stock_alerts,
            'orders': order_alerts,
            'contracts': contract_alerts,
            'total': stock_alerts + order_alerts + contract_alerts
        }
