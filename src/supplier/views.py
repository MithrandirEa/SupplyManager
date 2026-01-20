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
    selected_item_ids = list(supplier.associated_items.values_list('id', flat=True))
    
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