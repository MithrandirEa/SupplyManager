from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

from supplier.forms import Supplier, ChangeSupplierForm, CreateSupplierForm


@login_required
def create_supplier(request):
    if request.method == 'POST':
        form = CreateSupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            return redirect('suppliers_management')
    else:
        form = CreateSupplierForm()
    return render(request, 'create_supplier.html', {'form': form})


@login_required
def change_supplier(request, supplier_id):
    supplier = Supplier.objects.get(id=supplier_id)
    if request.method == 'POST':
        form = ChangeSupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('suppliers_management')
    else:
        form = ChangeSupplierForm(instance=supplier)

    return render(request, 'change_supplier.html', {'form': form, 'supplier_id': supplier_id})


@login_required
def delete_supplier(request, supplier_id):
    supplier = Supplier.objects.get(id=supplier_id)
    supplier.delete()
    return redirect('suppliers_management')