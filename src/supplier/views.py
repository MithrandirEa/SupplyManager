from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from authentication.decorators import role_required
from supplier.forms import ChangeSupplierForm, CreateSupplierForm, Supplier
from supply.models import Item


@role_required(['ADMIN', 'DIRECTOR'])
def create_supplier(request):
    if request.method == 'POST':
        form = CreateSupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()

            # Récupérer les items sélectionnés depuis les inputs hidden
            selected_items = request.POST.getlist('associated_items')
            if selected_items:
                supplier.associated_items.set(selected_items)

            return redirect('suppliers_management')
    else:
        form = CreateSupplierForm()

    all_items = Item.objects.all().order_by('name')
    return render(request, 'create_supplier.html', {
        'form': form,
        'all_items': all_items,
        'selected_item_ids': []
    })


@role_required(['ADMIN', 'DIRECTOR'])
def change_supplier(request, supplier_id):
    supplier = Supplier.objects.get(id=supplier_id)
    if request.method == 'POST':
        form = ChangeSupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()

            # Récupérer les items sélectionnés depuis les inputs hidden
            selected_items = request.POST.getlist('associated_items')
            supplier.associated_items.set(selected_items)

            return redirect('suppliers_management')
    else:
        form = ChangeSupplierForm(instance=supplier)

    all_items = Item.objects.all().order_by('name')
    selected_item_ids = list(
        supplier.associated_items.values_list('id', flat=True)
    )

    return render(request, 'change_supplier.html', {
        'form': form,
        'supplier_id': supplier_id,
        'all_items': all_items,
        'selected_item_ids': selected_item_ids
    })


@role_required(['ADMIN', 'DIRECTOR'])
def delete_supplier(request, supplier_id):
    supplier = Supplier.objects.get(id=supplier_id)
    supplier.delete()
    return redirect('suppliers_management')


@login_required
def change_order(request, order_id):
    """Vue pour modifier une commande"""
    import json
    from collections import defaultdict

    from django.contrib import messages

    from supplier.forms import ChangeOrderForm
    from supplier.models import Order
    from supply.models import Item, ItemsCategory

    order = Order.objects.get(id=order_id)

    if request.method == 'POST':
        form = ChangeOrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Commande mise à jour avec succès.')
            return redirect('supplies_management')
    else:
        form = ChangeOrderForm(instance=order)

    # Récupérer tous les items groupés par catégorie
    items_by_category = defaultdict(list)
    all_items = Item.objects.filter(
        is_available=True
    ).select_related('category').order_by('category__name', 'name')

    for item in all_items:
        category_name = item.category.name if item.category else "Sans catégorie"
        items_by_category[category_name].append(item)

    # Récupérer les items actuels de la commande
    current_items = []
    for order_item in order.order_items.all():
        current_items.append({
            'item_id': str(order_item.item.id),
            'item_name': order_item.item.name,
            'quantity': order_item.quantity
        })

    return render(request, 'change_order.html', {
        'form': form,
        'order': order,
        'items_by_category': dict(items_by_category),
        'current_items_json': json.dumps(current_items),
    })


@role_required(['ADMIN', 'DIRECTOR'])
def delete_order(request, order_id):
    """Vue pour supprimer une commande"""
    from django.contrib import messages

    from supplier.models import Order

    order = Order.objects.get(id=order_id)
    order.delete()
    messages.success(request, 'Commande supprimée avec succès.')
    return redirect('supplies_management')


@login_required
def receive_order(request, order_id):
    """
    Vue pour réceptionner une commande :
    l'utilisateur saisit la quantité reçue pour chaque article.
    Les articles non reçus sont signalés comme restés chez le fournisseur.
    """
    from django.contrib import messages
    from django.utils import timezone

    from supplier.models import Order

    order = Order.objects.prefetch_related(
        'order_items__item'
    ).get(id=order_id)

    if order.status in ['completed', 'partial']:
        messages.warning(request, 'Cette commande est déjà réceptionnée.')
        return redirect('supplies_management')

    order_items = list(order.order_items.select_related('item').all())

    if request.method == 'POST':
        errors = []
        receptions = []

        for oi in order_items:
            key_recv = f'received_qty_{oi.id}'
            key_inv = f'invoiced_qty_{oi.id}'

            raw_recv = request.POST.get(key_recv, '').strip()
            raw_inv = request.POST.get(key_inv, '').strip()

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

        if errors:
            return render(request, 'receive_order.html', {
                'order': order,
                'order_items': order_items,
                'errors': errors,
                'post_data': request.POST,
            })

        # Appliquer les réceptions
        backorder_items = []
        for oi, received, invoiced in receptions:
            remaining = oi.quantity - received
            if remaining > 0:
                backorder_items.append({
                    'item': oi.item,
                    'quantity': remaining
                })

            item = oi.item

            # Mettre à jour les stocks
            # NOTE: On ne décrémente que ce qui a été reçu.
            # Le reste (reliquat) reste comptabilisé comme "chez le fournisseur" (outside_quantity)
            # jusqu'à ce qu'il soit reçu via la nouvelle commande de reliquat.
            item.available_quantity += received
            item.outside_quantity = max(0, item.outside_quantity - received)
            item.save(update_fields=['available_quantity', 'outside_quantity'])

            # Enregistrer les quantités sur l'OrderItem
            oi.received_quantity = received
            oi.invoiced_quantity = invoiced
            oi.save(update_fields=['received_quantity', 'invoiced_quantity'])

        # Créer une commande reliquat si nécessaire
        if backorder_items:
            from datetime import timedelta

            original_date = order.order_date.strftime('%d/%m/%Y')

            # Message de reliquat standardisé
            reliquat_msg = f"Reliquat commande #{order.id}"

            backorder = Order.objects.create(
                supplier=order.supplier,
                created_by=request.user,
                order_date=timezone.now(),
                # Garder la date originale ou +7 jours ? +7 semble logique pour un retard
                expected_return_date=order.expected_return_date,
                status='pending',
                notes=f"{reliquat_msg} du {original_date}",
                # On utilise le champ notes pour stocker l'info,
                # mais l'utilisateur veut voir "En attente (reliquat...)" en statut.
                # On va modifier l'affichage dans le template plutôt que de corrompre le champ status
            )

            from supplier.models import OrderItem
            for item_data in backorder_items:
                OrderItem.objects.create(
                    order=backorder,
                    item=item_data['item'],
                    quantity=item_data['quantity']
                )

            messages.warning(
                request,
                f"Une nouvelle commande (#{backorder.id}) a été créée pour les {len(backorder_items)} articles manquants."
            )

        # Clôturer la commande
        if backorder_items:
            order.status = 'partial'
        else:
            order.status = 'completed'

        order.actual_return_date = timezone.now().date()
        order.save(update_fields=['status', 'actual_return_date'])

        messages.success(
            request,
            f'Commande #{order.id} réceptionnée avec succès.'
        )
        return redirect('supplies_management')

    return render(request, 'receive_order.html', {
        'order': order,
        'order_items': order_items,
        'errors': [],
        'post_data': {},
    })
