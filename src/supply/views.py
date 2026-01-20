from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CreateItemForm, ChangeItemForm

from supply.models import Item
from supplier.models import Supplier


@login_required
def create_item(request):
    if request.method == 'POST':
        form = CreateItemForm(request.POST)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.available_quantity = (
                new_item.total_quantity - new_item.outside_quantity
            )
            new_item.created_by = request.user
            new_item.save()

            # Récupérer les fournisseurs sélectionnés depuis les inputs hidden
            selected_suppliers = request.POST.getlist('suppliers')
            if selected_suppliers:
                new_item.suppliers.set(selected_suppliers)

            return redirect('supplies_management')
    else:
        form = CreateItemForm()

    all_suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'create_item.html', {
        'form': form,
        'all_suppliers': all_suppliers,
        'selected_supplier_ids': []
    })


@login_required
def change_item(request, item_id):
    item = Item.objects.get(id=item_id)
    if request.method == 'POST':
        form = ChangeItemForm(request.POST, instance=item)
        if form.is_valid():
            change_item = form.save(commit=False)
            change_item.available_quantity = (
                change_item.total_quantity - change_item.outside_quantity
            )
            change_item.save()

            # Récupérer les fournisseurs sélectionnés depuis les inputs hidden
            selected_suppliers = request.POST.getlist('suppliers')
            change_item.suppliers.set(selected_suppliers)

            return redirect('supplies_management')
    else:
        form = ChangeItemForm(instance=item)

    all_suppliers = Supplier.objects.all().order_by('name')
    selected_supplier_ids = list(item.suppliers.values_list('id', flat=True))

    return render(request, 'change_item.html', {
        'form': form,
        'item': item,
        'all_suppliers': all_suppliers,
        'selected_supplier_ids': selected_supplier_ids
    })


@login_required
def delete_item(request, item_id):
    item = Item.objects.get(id=item_id)
    item.delete()
    return redirect('supplies_management')
