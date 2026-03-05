from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from authentication.decorators import role_required
from supply.models import Item

from ..forms import ChangeInventoryForm


@login_required
@role_required(['ADMIN', 'DIRECTOR'])
def change_inventory(request, inventory_id):
    """Vue pour modifier un inventaire existant."""
    from supply.models import Inventory

    inventory = Inventory.objects.prefetch_related(
        'entries__item__category'
    ).get(pk=inventory_id)

    entry_map = {
        e.item_id: (e.counted_quantity, e.outside_quantity_snapshot)
        for e in inventory.entries.all()
    }

    all_items = Item.objects.filter(
        is_available=True
    ).select_related('category').order_by('category__name', 'name')

    items_by_category = defaultdict(list)
    for item in all_items:
        cat = item.category.name if item.category else "Sans catégorie"
        if item.id in entry_map:
            counted, outside = entry_map[item.id]
        else:
            counted = item.available_quantity
            outside = item.outside_quantity
        items_by_category[cat].append((item, counted, outside))

    if request.method == 'POST':
        form = ChangeInventoryForm(request.POST)
        if form.is_valid():
            form.save(inventory)
            messages.success(
                request,
                f'Inventaire du {inventory.created_at.strftime("%d/%m/%Y %H:%M")} '
                f'mis à jour.'
            )
            return redirect('supplies_management')
    else:
        form = ChangeInventoryForm(initial={'notes': inventory.notes})

    return render(request, 'change_inventory.html', {
        'inventory': inventory,
        'items_by_category': dict(items_by_category),
        'form': form,
    })


@login_required
def print_inventory_sheet(request):
    """
    Vue pour afficher une fiche d'inventaire imprimable.
    ?sort=alpha (par défaut) ou sort=category
    """
    sort = request.GET.get('sort', 'alpha')
    items = Item.objects.filter(is_available=True).select_related('category')

    context = {'sort': sort}

    if sort == 'category':
        items = items.order_by('category__name', 'name')
        items_by_cat = defaultdict(list)
        for item in items:
            cat = item.category.name if item.category else "Sans catégorie"
            items_by_cat[cat].append(item)
        # Trier les clés
        context['items_by_category'] = dict(sorted(items_by_cat.items()))
    else:
        # alpha
        items = items.order_by('name')
        context['items'] = items

    return render(request, 'inventory_sheet.html', context)
