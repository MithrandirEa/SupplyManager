from django.shortcuts import render
from authentication.models import User
from django.contrib.auth.decorators import login_required, permission_required

from supplier.models import Supplier
from supply.models import Item


@login_required
def home(request):
    return render(request, 'home.html')


@login_required
@permission_required('authentication.view_user', raise_exception=True)
def staff_management(request):
    users = User.objects.all().order_by('role', 'username')
    return render(request, 'staff_management.html', {'users': users})


@login_required
def supplies_management(request):
    items = Item.objects.all().order_by('category', 'name')
    return render(request, 'supplies_management.html', {'items': items})


@login_required
@permission_required('supplier.view_supplier', raise_exception=True)
def suppliers_management(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'suppliers_management.html', {'suppliers': suppliers})