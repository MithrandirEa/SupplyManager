import json
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from authentication.decorators import role_required
from supplier.forms import ChangeOrderForm, ChangeSupplierForm, CreateSupplierForm, Supplier
from supplier.models import Order
from supply.models import Item, ItemsCategory


@role_required(['ADMIN', 'DIRECTOR'])
def create_supplier(request):
    if request.method == 'POST':
        form = CreateSupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()

            # Récupérer les items sélectionnés depuis les inputs hidden
            selected_items = request.POST.getlist('associated_items')
            if selected_items:
                supplier.items.set(selected_items)

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
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        form = ChangeSupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()

            # Récupérer les items sélectionnés depuis les inputs hidden
            selected_items = request.POST.getlist('associated_items')
            supplier.items.set(selected_items)

            return redirect('suppliers_management')
    else:
        form = ChangeSupplierForm(instance=supplier)

    all_items = Item.objects.all().order_by('name')
    selected_item_ids = list(
        supplier.items.values_list('id', flat=True)
    )

    return render(request, 'change_supplier.html', {
        'form': form,
        'supplier_id': supplier_id,
        'all_items': all_items,
        'selected_item_ids': selected_item_ids
    })


@require_POST
@role_required(['ADMIN', 'DIRECTOR'])
def delete_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    supplier.delete()
    return redirect('suppliers_management')


@login_required
def change_order(request, order_id):
    """Vue pour modifier une commande"""
    order = get_object_or_404(Order, id=order_id)

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


@require_POST
@role_required(['ADMIN', 'DIRECTOR'])
def delete_order(request, order_id):
    """Vue pour supprimer une commande"""
    order = get_object_or_404(Order, id=order_id)
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
    from supplier.services import OrderReceptionService

    order = get_object_or_404(
        Order.objects.prefetch_related('order_items__item'),
        id=order_id
    )

    if order.status in ['completed', 'partial']:
        messages.warning(request, 'Cette commande est déjà réceptionnée.')
        return redirect('supplies_management')

    order_items = list(order.order_items.select_related('item').all())

    if request.method == 'POST':
        receptions, errors = OrderReceptionService.validate_receptions(
            order_items, request.POST
        )

        if errors:
            return render(request, 'receive_order.html', {
                'order': order,
                'order_items': order_items,
                'errors': errors,
                'post_data': request.POST,
            })

        backorder = OrderReceptionService.process_reception(
            order, receptions, request.user
        )

        if backorder:
            messages.warning(
                request,
                f"Une nouvelle commande (#{backorder.id}) a été créée "
                f"pour les articles manquants."
            )

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
