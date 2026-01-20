from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def create_supplier(request):
    return render(request, 'create_supplier.html')


@login_required
def change_supplier(request, supplier_id):
    return render(request, 'change_supplier.html', {'supplier_id': supplier_id})


@login_required
def delete_supplier(request, supplier_id):
    return render(request, 'delete_supplier.html', {'supplier_id': supplier_id})
