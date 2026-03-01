from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

from supplier.forms import Supplier, ChangeSupplierForm, CreateSupplierForm
from supply.models import Item


@login_required
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


@login_required
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


@login_required
def delete_supplier(request, supplier_id):
    supplier = Supplier.objects.get(id=supplier_id)
    supplier.delete()
    return redirect('suppliers_management')


@login_required
def change_order(request, order_id):
    """Vue pour modifier une commande"""
    from supplier.models import Order
    from supplier.forms import ChangeOrderForm
    from django.contrib import messages
    from supply.models import Item, ItemsCategory
    from collections import defaultdict
    import json
    
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


@login_required
def delete_order(request, order_id):
    """Vue pour supprimer une commande"""
    from supplier.models import Order
    from django.contrib import messages
    
    order = Order.objects.get(id=order_id)
    order.delete()
    messages.success(request, 'Commande supprimée avec succès.')
    return redirect('supplies_management')
