from django.contrib.auth.decorators import login_required

from supplier.models import Order
from supply.models import Inventory, Item

from ..exports import (
    export_inventories_all_detail_csv,
    export_inventories_all_detail_excel,
    export_inventories_list_csv,
    export_inventories_list_excel,
    export_inventory_detail_csv,
    export_inventory_detail_excel,
    export_items_csv,
    export_items_excel,
    export_monthly_stats_csv,
    export_monthly_stats_excel,
    export_order_detail_csv,
    export_order_detail_excel,
    export_orders_all_detail_csv,
    export_orders_all_detail_excel,
    export_orders_list_csv,
    export_orders_list_excel,
)


@login_required
def export_items(request):
    """Export CSV ou Excel de tous les articles."""
    fmt = request.GET.get('fmt', 'csv')
    items = Item.objects.select_related('category').prefetch_related(
        'suppliers'
    ).order_by('category__name', 'name')
    if fmt == 'excel':
        return export_items_excel(items)
    return export_items_csv(items)


@login_required
def export_orders(request):
    """
    Export commandes.
    ?fmt=csv|excel  &  ?scope=list|all-detail
    """
    fmt = request.GET.get('fmt', 'csv')
    scope = request.GET.get('scope', 'list')
    orders = Order.objects.select_related('supplier', 'created_by').prefetch_related(
        'order_items__item__category'
    ).order_by('-order_date')
    if scope == 'all-detail':
        if fmt == 'excel':
            return export_orders_all_detail_excel(orders)
        return export_orders_all_detail_csv(orders)
    # list
    if fmt == 'excel':
        return export_orders_list_excel(orders)
    return export_orders_list_csv(orders)


@login_required
def export_order(request, order_id):
    """Export CSV ou Excel du détail d'une commande."""
    fmt = request.GET.get('fmt', 'csv')
    order = Order.objects.select_related('supplier').prefetch_related(
        'order_items__item__category'
    ).get(pk=order_id)
    if fmt == 'excel':
        return export_order_detail_excel(order)
    return export_order_detail_csv(order)


@login_required
def export_inventories(request):
    """
    Export inventaires.
    ?fmt=csv|excel  &  ?scope=list|all-detail
    """
    fmt = request.GET.get('fmt', 'csv')
    scope = request.GET.get('scope', 'list')
    inventories = Inventory.objects.select_related('created_by').prefetch_related(
        'entries__item__category'
    ).order_by('-created_at')
    if scope == 'all-detail':
        if fmt == 'excel':
            return export_inventories_all_detail_excel(inventories)
        return export_inventories_all_detail_csv(inventories)
    if fmt == 'excel':
        return export_inventories_list_excel(inventories)
    return export_inventories_list_csv(inventories)


@login_required
def export_inventory(request, inventory_id):
    """Export CSV ou Excel du détail d'un inventaire."""
    fmt = request.GET.get('fmt', 'csv')
    inventory = Inventory.objects.select_related('created_by').prefetch_related(
        'entries__item__category'
    ).get(pk=inventory_id)
    if fmt == 'excel':
        return export_inventory_detail_excel(inventory)
    return export_inventory_detail_csv(inventory)


@login_required
def export_monthly_stats(request):
    """Export du suivi mensuel."""
    fmt = request.GET.get('fmt', 'csv')

    if fmt == 'excel':
        return export_monthly_stats_excel()
    return export_monthly_stats_csv()
