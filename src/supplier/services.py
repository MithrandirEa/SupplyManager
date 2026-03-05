"""
Service de réception de commandes.
"""
from django.utils import timezone

from supplier.models import Order, OrderItem


class OrderReceptionService:
    """Traite la réception d'une commande et retourne les résultats."""

    @staticmethod
    def validate_receptions(order_items, post_data):
        """
        Valide les quantités reçues/facturées depuis les données POST.

        Returns:
            tuple (receptions, errors)
            - receptions: liste de (order_item, received, invoiced)
            - errors: liste de messages d'erreur
        """
        errors = []
        receptions = []

        for oi in order_items:
            key_recv = f'received_qty_{oi.id}'
            key_inv = f'invoiced_qty_{oi.id}'

            raw_recv = post_data.get(key_recv, '').strip()
            raw_inv = post_data.get(key_inv, '').strip()

            try:
                received = int(raw_recv)
                invoiced = int(raw_inv) if raw_inv else 0

                if received < 0:
                    raise ValueError("Quantité reçue négative")
                if invoiced < 0:
                    raise ValueError("Quantité facturée négative")

                if received > oi.quantity:
                    errors.append(
                        f"{oi.item.name} : la quantité reçue ({received}) "
                        f"dépasse la quantité commandée ({oi.quantity})."
                    )
            except (ValueError, TypeError):
                errors.append(
                    f"{oi.item.name} : valeurs invalides."
                )
                continue
            receptions.append((oi, received, invoiced))

        return receptions, errors

    @staticmethod
    def process_reception(order, receptions, user):
        """
        Applique les réceptions : met à jour les stocks, enregistre les
        quantités, crée un reliquat si nécessaire, et clôture la commande.

        Returns:
            backorder (Order ou None) : la commande reliquat créée, ou None
        """
        backorder_items = []
        for oi, received, invoiced in receptions:
            remaining = oi.quantity - received
            if remaining > 0:
                backorder_items.append({
                    'item': oi.item,
                    'quantity': remaining
                })

            item = oi.item
            item.available_quantity += received
            item.outside_quantity = max(0, item.outside_quantity - received)
            item.save(update_fields=['available_quantity', 'outside_quantity'])

            oi.received_quantity = received
            oi.invoiced_quantity = invoiced
            oi.save(update_fields=['received_quantity', 'invoiced_quantity'])

        # Créer une commande reliquat si nécessaire
        backorder = None
        if backorder_items:
            original_date = order.order_date.strftime('%d/%m/%Y')
            reliquat_msg = f"Reliquat commande #{order.id}"

            backorder = Order.objects.create(
                supplier=order.supplier,
                created_by=user,
                order_date=timezone.now(),
                expected_return_date=order.expected_return_date,
                status='pending',
                notes=f"{reliquat_msg} du {original_date}",
            )

            for item_data in backorder_items:
                OrderItem.objects.create(
                    order=backorder,
                    item=item_data['item'],
                    quantity=item_data['quantity']
                )

        # Clôturer la commande
        if backorder_items:
            order.status = 'partial'
        else:
            order.status = 'completed'

        order.actual_return_date = timezone.now().date()
        order.save(update_fields=['status', 'actual_return_date'])

        return backorder
