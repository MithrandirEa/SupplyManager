from django.shortcuts import render
from authentication.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, Count, Q

from supplier.models import Supplier
from supply.models import Item, ItemsCategory


@login_required
def home(request):
    # Statistiques générales
    total_items = Item.objects.count()
    total_categories = ItemsCategory.objects.count()

    # Quantités totales
    quantities = Item.objects.aggregate(
        total_stock=Sum('total_quantity'),
        total_outside=Sum('outside_quantity'),
        total_available=Sum('available_quantity')
    )

    # Items avec alertes (quantité disponible faible)
    low_stock_items = Item.objects.filter(
        available_quantity__lte=5,
        available_quantity__gt=0
    ).order_by('available_quantity')

    # Items en rupture de stock
    out_of_stock_items = Item.objects.filter(
        available_quantity=0
    )

    # Items avec delta négatif (outside > total)
    items_with_issues = Item.objects.filter(
        outside_quantity__gt=models.F('total_quantity')
    )

    # Statistiques par catégorie
    category_stats = ItemsCategory.objects.annotate(
        item_count=Count('items'),
        total_qty=Sum('items__total_quantity'),
        available_qty=Sum('items__available_quantity')
    ).order_by('-item_count')

    # Items récemment modifiés
    recent_items = Item.objects.all().order_by('-updated_at')[:5]

    context = {
        'total_items': total_items,
        'total_categories': total_categories,
        'total_stock': quantities['total_stock'] or 0,
        'total_outside': quantities['total_outside'] or 0,
        'total_available': quantities['total_available'] or 0,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'items_with_issues': items_with_issues,
        'category_stats': category_stats,
        'recent_items': recent_items,
    }

    return render(request, 'home.html', context)


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
    return render(
        request,
        'suppliers_management.html',
        {'suppliers': suppliers}
    )
