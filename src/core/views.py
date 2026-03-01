from django.shortcuts import render, redirect
from django.contrib import messages
from authentication.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from supplier.models import Supplier
from supply.models import Item
from .services import DashboardService
from .forms import BulkInventoryForm, ChangeInventoryForm, ContractExtensionForm
from supplier.forms import QuickOrderForm


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
    from supplier.models import Order
    from supply.models import Inventory
    from collections import defaultdict

    items = Item.objects.all().order_by('category__name', 'name')
    orders = Order.objects.select_related(
        'supplier', 'created_by'
    ).prefetch_related('order_items__item').all().order_by('-order_date')
    inventories = Inventory.objects.select_related(
        'created_by'
    ).prefetch_related('entries__item__category').all()

    # Groupement par catégorie pour le modal inventaire
    items_by_category = defaultdict(list)
    available_items = Item.objects.filter(
        is_available=True
    ).select_related('category').order_by('category__name', 'name')
    for item in available_items:
        cat = item.category.name if item.category else "Sans catégorie"
        items_by_category[cat].append(item)

    # Compter les commandes non terminées
    pending_orders_count = orders.exclude(status='completed').count()

    context = {
        'items': items,
        'orders': orders,
        'inventories': inventories,
        'pending_orders_count': pending_orders_count,
        'items_by_category': dict(items_by_category),
    }
    return render(request, 'supplies_management.html', context)


@login_required
@permission_required('supplier.view_supplier', raise_exception=True)
def suppliers_management(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(
        request,
        'suppliers_management.html',
        {'suppliers': suppliers}
    )


def _user_can_access_dashboard(user):
    """
    Vérifie si l'utilisateur peut accéder au dashboard.

    Seuls Admin et Director ont accès.
    """
    return user.role in [User.ADMIN, User.DIRECTOR]


@login_required
def dashboard(request):
    """
    Vue principale du dashboard.

    Affiche les stocks, alertes et statut des commandes.
    Accessible uniquement aux Admin et Director.
    """
    # Vérification des permissions
    if not _user_can_access_dashboard(request.user):
        messages.error(
            request,
            "Vous n'avez pas la permission d'accéder au dashboard."
        )
        return redirect('home')

    # Récupération de toutes les données du dashboard
    dashboard_data = DashboardService.get_all_dashboard_data()

    # Récupération du nombre d'alertes pour l'affichage
    alerts_count = DashboardService.get_alerts_count()

    # Récupération des fournisseurs pour le formulaire de commande
    all_suppliers = Supplier.objects.all().order_by('name')
    
    # Récupération des items groupés par catégorie pour le formulaire
    from supply.models import ItemsCategory
    from collections import defaultdict
    
    items_by_category = defaultdict(list)
    all_items = Item.objects.filter(
        is_available=True
    ).select_related('category').order_by('category__name', 'name')
    
    for item in all_items:
        category_name = item.category.name if item.category else "Sans catégorie"
        items_by_category[category_name].append(item)

    # Récupération des commandes non terminées pour la réception
    from supplier.models import Order
    pending_orders = Order.objects.filter(
        status__in=['pending', 'delayed']
    ).select_related('supplier').prefetch_related('order_items__item').order_by('expected_return_date')

    # Préparation du contexte
    context = {
        # Stocks
        'missing_items': dashboard_data['missing_items'],
        'excess_items': dashboard_data['excess_items'],
        'items_at_supplier': dashboard_data['items_at_supplier'],

        # Alertes
        'stock_alerts': dashboard_data['stock_alerts'],
        'order_alerts': dashboard_data['order_alerts'],
        'contract_alerts': dashboard_data['contract_alerts'],

        # Commandes
        'outdated_orders': dashboard_data['outdated_orders'],
        'waited_orders': dashboard_data['waited_orders'],
        'pending_orders': pending_orders,

        # Compteurs pour badges
        'alerts_count': alerts_count,

        # Informations additionnelles
        'total_alerts': alerts_count['total'],
        
        # Pour les actions rapides
        'all_suppliers': all_suppliers,
        'all_items': list(all_items),
        'items_by_category': dict(items_by_category),
    }

    return render(request, 'dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def create_order_ajax(request):
    """
    Vue AJAX pour créer une commande rapide depuis le dashboard
    """
    # Vérification des permissions
    if not _user_can_access_dashboard(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée.'
        }, status=403)

    form = QuickOrderForm(request.POST, user=request.user)
    
    if form.is_valid():
        order = form.save()
        return JsonResponse({
            'success': True,
            'message': f'Commande #{order.id} créée avec succès.',
            'order_id': order.id
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
@require_http_methods(["POST"])
def update_inventory_ajax(request):
    """
    Vue AJAX pour enregistrer un inventaire global (tous les articles).
    """
    # Vérification des permissions
    if not _user_can_access_dashboard(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée.'
        }, status=403)

    form = BulkInventoryForm(request.POST)

    if form.is_valid():
        inventory = form.save(user=request.user)
        return JsonResponse({
            'success': True,
            'message': (
                f'Inventaire du {inventory.created_at.strftime("%d/%m/%Y %H:%M")} '
                f'enregistré ({inventory.entries.count()} articles).'
            ),
            'inventory_id': inventory.id,
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
@require_http_methods(["POST"])
def extend_contract_ajax(request):
    """
    Vue AJAX pour prolonger un contrat
    """
    # Vérification des permissions
    if not _user_can_access_dashboard(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée.'
        }, status=403)

    form = ContractExtensionForm(request.POST)
    
    if form.is_valid():
        user = form.save()
        end_date = user.date_end_contract.strftime("%d/%m/%Y")
        return JsonResponse({
            'success': True,
            'message': (
                f'Contrat de {user.username} '
                f'prolongé jusqu\'au {end_date}.'
            ),
            'username': user.username,
            'new_date': user.date_end_contract.isoformat()
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def change_inventory(request, inventory_id):
    """Vue pour modifier un inventaire existant."""
    from supply.models import Inventory, Item
    from collections import defaultdict

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


# ─────────────────────────────────────────────
#  Vues d'export
# ─────────────────────────────────────────────

@login_required
def export_items(request):
    """Export CSV ou Excel de tous les articles."""
    from .exports import export_items_csv, export_items_excel
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
    from supplier.models import Order
    from .exports import (
        export_orders_list_csv, export_orders_list_excel,
        export_orders_all_detail_csv, export_orders_all_detail_excel,
    )
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
    from supplier.models import Order
    from .exports import export_order_detail_csv, export_order_detail_excel
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
    from supply.models import Inventory
    from .exports import (
        export_inventories_list_csv, export_inventories_list_excel,
        export_inventories_all_detail_csv, export_inventories_all_detail_excel,
    )
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
    from supply.models import Inventory
    from .exports import export_inventory_detail_csv, export_inventory_detail_excel
    fmt = request.GET.get('fmt', 'csv')
    inventory = Inventory.objects.select_related('created_by').prefetch_related(
        'entries__item__category'
    ).get(pk=inventory_id)
    if fmt == 'excel':
        return export_inventory_detail_excel(inventory)
    return export_inventory_detail_csv(inventory)
